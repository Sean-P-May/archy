from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from lib.models import SystemSettings
from lib.process_helpers import chroot_process, run_process_exit_on_fail


def vefity_internet() -> bool:
    """Check whether the host has Internet connectivity."""

    command = ["ping", "-c", "1", "archlinux.org"]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def select_package_user(system: SystemSettings) -> str:
    """Pick a user to run package installs under, preferring sudo users."""

    if not system.users:
        raise ValueError("No users configured for package installation")

    for user in system.users:
        if user.sudo:
            return user.username

    return system.users[0].username


def apply_dotfiles(
    entries: list[dict],
    base_dirs: list[Path],
    users=None,
    *,
    root_path: Path | str = "/mnt",
):
    user_lookup = {user.username for user in (users or [])}
    root_path = Path(root_path)

    def run_in_target(process: list[str] | str):
        if root_path == Path("/"):
            run_process_exit_on_fail(process)
        else:
            chroot_process(process)

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

        destination = root_path / destination.relative_to("/")
        destination.parent.mkdir(parents=True, exist_ok=True)

        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True)
        elif source.is_symlink():
            shutil.copy(source, destination, follow_symlinks=False)
        else:
            shutil.copy2(source, destination)

        chroot_destination = Path("/") / destination.relative_to(root_path)
        if chroot_destination.parts[:2] == ("/", "home") and len(chroot_destination.parts) >= 3:
            owner = chroot_destination.parts[2]
            if owner in user_lookup:
                run_in_target([
                    "chown",
                    "-R",
                    "--no-dereference",
                    f"{owner}:{owner}",
                    str(chroot_destination),
                ])

