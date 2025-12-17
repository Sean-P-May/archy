
from pathlib import Path
from lib.process_helpers import *


from dataclasses import dataclass
from typing import Optional


@dataclass
class PackageGroup:
    pacman: Optional[Path] = None
    aur: Optional[Path] = None

class PackageInstaller:
    def __init__(self, username: str):
        """
        username is required for AUR installs
        """
        self.username = username

    # -------------------------
    # Helpers
    # -------------------------

    def _read_package_file(self, path: Path) -> list[str]:
        with open(path) as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]

    def _chroot_run_as_user(self, cmd: str):
        chroot_process([
            "sudo", "-u", self.username,
            "bash", "-lc", cmd
        ])

    # -------------------------
    # Install methods
    # -------------------------

    def install_pacman_packages(self, packages: list[str]):
        if not packages:
            return

        chroot_process([
            "pacman", "-S", "--noconfirm", "--needed",
            *packages
        ])

    def install_pacman_file(self, path: Path):
        packages = self._read_package_file(path)
        self.install_pacman_packages(packages)

    def install_aur_packages(self, packages: list[str]):
        if not packages:
            return

        aur_dir = f"/home/{self.username}/.cache/aur"

        self._chroot_run_as_user(f"mkdir -p {aur_dir}")

        for pkg in packages:
            self._chroot_run_as_user(
                f"""
                set -e
                cd {aur_dir}
                rm -rf {pkg}
                git clone https://aur.archlinux.org/{pkg}.git
                cd {pkg}
                makepkg -si --noconfirm
                """
            )

    def install_aur_file(self, path: Path):
        packages = self._read_package_file(path)
        self.install_aur_packages(packages)

