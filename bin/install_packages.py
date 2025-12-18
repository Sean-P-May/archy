#!/usr/bin/env python3
"""Install package groups onto an already installed system using a setup file."""

from pathlib import Path
import os
import pwd
import sys

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.install_helpers import select_package_user, vefity_internet
from lib.loader import load_setup_yaml
from lib.models import PackageGroup, PackageInstaller, SystemSettings
from lib.picker import pick_setup


def ensure_root():
    if os.geteuid() != 0:
        sys.exit("This script must be run as root.")


def ensure_user_exists(username: str):
    try:
        pwd.getpwnam(username)
    except KeyError:
        sys.exit(f"User '{username}' does not exist on this system.")


def main():
    ensure_root()

    if not vefity_internet():
        sys.exit("No Internet!")

    setups_root = repo_root / "setups"
    package_root = repo_root / "packages"

    setup = pick_setup(setups_root)
    base_dir = setups_root / setup
    print(f"Selected setup: {setup}")

    raw = load_setup_yaml(setup, setups_root=setups_root)
    machine_config = raw.get("machine") or raw.get("system")
    if not machine_config:
        raise KeyError("Setup file missing 'system' configuration")

    system = SystemSettings.from_config(machine_config)
    package_groups = PackageGroup.from_entries(raw.get("packages", []), base_dir=package_root)

    if not package_groups:
        print("No package groups configured; nothing to install.")
        return

    package_user = select_package_user(system)
    ensure_user_exists(package_user)

    installer = PackageInstaller(package_user, root_path="/")

    pacman_failures: list[str] = []
    aur_failures: list[str] = []
    flatpak_failures: list[str] = []

    for group in package_groups:
        if group.pacman:
            pacman_failures.extend(installer.install_pacman_file(group.pacman))
        if group.aur:
            aur_failures.extend(installer.install_aur_file(group.aur))
        if group.flatpak:
            flatpak_failures.extend(installer.install_flatpak_file(group.flatpak))

    if pacman_failures or aur_failures or flatpak_failures:
        print("Package installation completed with some failures:")
        if pacman_failures:
            print(f"  Pacman: {', '.join(pacman_failures)}")
        if aur_failures:
            print(f"  AUR: {', '.join(aur_failures)}")
        if flatpak_failures:
            print(f"  Flatpak: {', '.join(flatpak_failures)}")
    else:
        print("All package installations completed successfully.")


if __name__ == "__main__":
    main()
