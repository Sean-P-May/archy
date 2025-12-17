from pathlib import Path
from lib.process_helpers import *
from lib.models import Disk, PackageGroup, PackageInstaller, SystemSettings
from lib.picker import pick_setup
from lib.loader import load_setup_yaml
from lib.partitioner import partition_disks
import subprocess

def main():

    


    # 1. Pick setup





    #Keyboard layout
    subprocess.run(["loadkeys", "us"])

    #check_efi
    with open("/sys/firmware/efi/fw_platform_size") as f:
        value = f.read().strip() 
    
    if value != "64":
        print("architecture not supported by this install script.")
        exit()
    # 2. Load raw YAML
    
    # run_process_exit_on_fail("pacman-key -v archlinux-version-x86_64.iso.sig")



    setup = pick_setup()
    base_dir = Path("setups") / setup
    print(f"Selected setup: {setup}")
    if not vefity_internet():
        print("No Internet!")
        exit()

    raw = load_setup_yaml(setup)

    # 3. Normalize → validated models
    machine_config = raw.get("machine") or raw.get("system")
    if not machine_config:
        raise KeyError("Setup file missing 'system' configuration")

    disks = Disk.from_storage(raw["storage"])
    system = SystemSettings.from_config(machine_config)
    package_groups = PackageGroup.from_entries(raw.get("packages", []), base_dir=base_dir)

    print(f"Users: {system.users}")
    print(f"Hostname: {system.hostname}")
    print(f"Users: {system.users}")
    for disk in disks:
        print(" Disk: " + disk.device)
        for partition in disk.partitions:
            print(f"  {partition}")
    
    print(f"Package groups: {package_groups}")




    if not input("Ready to install? (yes or y): ").lower() in ["yes", "y"]:
        print("Exiting!!!")
        exit()


    partition_disks(disks)

    for disk in disks:
        for partition in disk.partitions:
            if partition.is_root():
                run_process_exit_on_fail(f"mount {partition.dev_path} /mnt")

            if partition.is_boot():
                run_process_exit_on_fail(f"mount {partition.dev_path} /mnt/boot")

            if partition.is_swap():
                run_process_exit_on_fail(f"swapon {partition.dev_path}")
    

    run_process_exit_on_fail("pacstrap -K /mnt base linux linux-firmware")

    chroot_process(f"ln -sf /usr/share/zoneinfo/Area/Location/{system.timezone} /etc/localtime")
    chroot_process("hwclock --systohc")
    chroot_process("locale-gen")
    chroot_process(f'echo "LANG={system.timezone}" >> /etc/locale.conf')
    chroot_process(f'echo "{system.hostname}" >>  /etc/hostname')

    setup_users(system)

    package_user = select_package_user(system)
    installer = PackageInstaller(package_user)

    for group in package_groups:
        if group.pacman:
            installer.install_pacman_file(group.pacman)
        if group.aur:
            installer.install_aur_file(group.aur)




 

    






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

if __name__ == "__main__":
    main()
