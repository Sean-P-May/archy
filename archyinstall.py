from pathlib import Path
import shutil
import subprocess
from lib.process_helpers import *
from lib.models import Disk, PackageGroup, PackageInstaller, SystemSettings
from lib.picker import pick_setup
from lib.loader import load_setup_yaml
from lib.partitioner import partition_disks


def main():

    # 1. Pick setup

    # Keyboard layout
    subprocess.run(["loadkeys", "us"])

    # check_efi
    with open("/sys/firmware/efi/fw_platform_size") as f:
        value = f.read().strip()

    if value != "64":
        print("architecture not supported by this install script.")
        exit()

    # 2. Load raw YAML

    repo_root = Path(__file__).resolve().parent
    setups_root = repo_root / "setups"

    setup = pick_setup(setups_root)
    base_dir = setups_root / setup
    print(f"Selected setup: {setup}")
    if not vefity_internet():
        print("No Internet!")
        exit()

    raw = load_setup_yaml(setup, setups_root=setups_root)

    # 3. Normalize → validated models
    machine_config = raw.get("machine") or raw.get("system")
    if not machine_config:
        raise KeyError("Setup file missing 'system' configuration")

    disks = Disk.from_storage(raw["storage"])
    system = SystemSettings.from_config(machine_config)
    resource_roots = [base_dir, setups_root, repo_root]
    package_root = repo_root / "packages"

    package_groups = PackageGroup.from_entries(
        raw.get("packages", []),
        base_dir=package_root,
    )

    print(f"Users: {system.users}")
    print(f"Hostname: {system.hostname}")
    print(f"Users: {system.users}")
    print(f"Secure Boot enabled: {system.secure_boot}")
    for disk in disks:
        print(" Disk: " + disk.device)
        for partition in disk.partitions:
            print(f"  {partition}")

    print(f"Package groups: {package_groups}")

    if not input("Ready to install? (yes or y): ").lower() in ["yes", "y"]:
        print("Exiting!!!")
        exit()

    partition_disks(disks, dry_run=False)

    roots = []
    boots = []
    swaps = []

    for disk in disks:
        for partition in disk.partitions:
            if partition.is_root():
                roots.append(partition)
            if partition.is_boot():
                boots.append(partition)
            if partition.is_swap():
                swaps.append(partition)

    if not roots:
        raise RuntimeError("No root partition found to mount")

    root = roots[0]
    run_process_exit_on_fail(["mount", root.dev_path, "/mnt"])

    if boots:
        run_process_exit_on_fail(["mkdir", "-p", "/mnt/boot"])
        for boot in boots:
            run_process_exit_on_fail(["mount", boot.dev_path, "/mnt/boot"])

    for swap in swaps:
        run_process_exit_on_fail(["swapon", swap.dev_path])

    run_process_exit_on_fail(
        "pacstrap -K /mnt base linux linux-firmware linux-headers base-devel sbctl networkmanager"
    )

    run_process_exit_on_fail(["bash", "-lc", "genfstab -U /mnt >> /mnt/etc/fstab"])

    chroot_process(["sed", "-i", f's/^#\\s*{system.locale}/{system.locale}/', "/etc/locale.gen"])
    chroot_process(f"ln -sf /usr/share/zoneinfo/{system.timezone} /etc/localtime")
    chroot_process("hwclock --systohc")
    chroot_process("locale-gen")
    chroot_process(["/bin/sh", "-c", f'echo "LANG={system.locale}" > /etc/locale.conf'])
    chroot_process(["/bin/sh", "-c", f'echo "{system.hostname}" > /etc/hostname'])

    set_root_password()
    install_bootloader(disks, enable_secure_boot=system.secure_boot)

    apply_dotfiles(raw.get("dotfiles", []), resource_roots)

    setup_users(system)

    package_user = select_package_user(system)
    installer = PackageInstaller(package_user)

    for group in package_groups:
        if group.pacman:
            installer.install_pacman_file(group.pacman)
        if group.aur:
            installer.install_aur_file(group.aur)

    print("Install complete. Please reboot.")


def vefity_internet():
    command = ["ping", "-c", "1", "archlinux.org"]   # Linux/macOS
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def select_package_user(system: SystemSettings) -> str:
    if not system.users:
        raise ValueError("No users configured for package installation")

    for user in system.users:
        if user.sudo:
            return user.username

    return system.users[0].username


def setup_users(system: SystemSettings):
    sudo_needed = False

    for user in system.users:
        create_user(user.username)
        set_user_password(user.username)
        sudo_needed = sudo_needed or user.sudo

    if sudo_needed:
        enable_wheel_sudo()


def install_bootloader(disks: list[Disk], *, enable_secure_boot: bool = False):
    root_partition = None
    for disk in disks:
        for partition in disk.partitions:
            if partition.is_root():
                root_partition = partition
                break
        if root_partition:
            break

    if not root_partition:
        raise ValueError("No root partition found for bootloader configuration")

    result = subprocess.run(
        ["blkid", "-s", "UUID", "-o", "value", root_partition.dev_path],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Unable to read UUID for {root_partition.dev_path}: {result.stderr}")

    root_uuid = result.stdout.strip()
    if not root_uuid:
        raise RuntimeError(f"Missing UUID for {root_partition.dev_path}")

    chroot_process(["bootctl", "install"])
    chroot_process(["mkdir", "-p", "/boot/loader/entries"])

    loader_conf = """default arch.conf\ntimeout 3\neditor no\n"""
    entry_conf = f"""title Arch Linux\nlinux /vmlinuz-linux\ninitrd /initramfs-linux.img\noptions root=UUID={root_uuid} rw\n"""

    chroot_process([
        "/bin/sh", "-c",
        f"cat > /boot/loader/loader.conf <<'EOF'\n{loader_conf}\nEOF"
    ])

    chroot_process([
        "/bin/sh", "-c",
        f"cat > /boot/loader/entries/arch.conf <<'EOF'\n{entry_conf}\nEOF"
    ])

    chroot_process(["systemctl", "enable", "NetworkManager.service"])

    if enable_secure_boot:
        setup_secure_boot()


def setup_secure_boot():
    clear_immutable_efivars()

    keys_dir = Path("/mnt/usr/share/secureboot/keys")
    if not keys_dir.exists():
        chroot_process(["sbctl", "create-keys"])

    chroot_process(["sbctl", "enroll-keys", "--microsoft"])

    binaries = [
        "/boot/EFI/systemd/systemd-bootx64.efi",
        "/boot/EFI/BOOT/BOOTX64.EFI",
        "/boot/vmlinuz-linux",
    ]

    for binary in binaries:
        chroot_process(["sbctl", "sign", "-s", binary])

    configure_secure_boot_hook()


def clear_immutable_efivars():
    efivarfs = Path("/sys/firmware/efi/efivars")
    if not efivarfs.exists():
        print("efivarfs not mounted; skipping immutable attribute check.")
        return

    targets = []
    for prefix in ("PK-", "KEK-", "db-"):
        targets.extend(efivarfs.glob(f"{prefix}*"))

    for target in targets:
        run_process_exit_on_fail(["chattr", "-i", str(target)])


def configure_secure_boot_hook():
    hook_path = Path("/mnt/etc/pacman.d/hooks/90-secure-boot-sign.hook")
    hook_path.parent.mkdir(parents=True, exist_ok=True)

    hook_contents = """[Trigger]
Operation = Install
Operation = Upgrade
Operation = Remove
Type = Path
Target = usr/lib/systemd/boot/efi/systemd-bootx64.efi
Target = boot/EFI/BOOT/BOOTX64.EFI
Target = boot/vmlinuz-linux

[Action]
Description = Signing EFI binaries for Secure Boot
When = PostTransaction
Exec = /usr/bin/sbctl sign-all
"""

    hook_path.write_text(hook_contents)


def apply_dotfiles(entries: list[dict], base_dirs: list[Path]):
    for entry in entries:
        source = Path(entry["copy_from"])
        if not source.is_absolute():
            resolved_source = None
            for base_dir in base_dirs:
                candidate = (base_dir / source).resolve()
                if candidate.exists():
                    resolved_source = candidate
                    break
            source = resolved_source or (base_dirs[0] / source).resolve()

        if not source.exists():
            print(f"Skipping missing dotfiles source: {source}")
            continue

        destination = Path(entry["copy_to"])
        if not destination.is_absolute():
            destination = Path("/") / destination

        destination = Path("/mnt") / destination.relative_to("/")
        destination.parent.mkdir(parents=True, exist_ok=True)

        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True)
        elif source.is_symlink():
            shutil.copy(source, destination, follow_symlinks=False)
        else:
            shutil.copy2(source, destination)


if __name__ == "__main__":
    main()
