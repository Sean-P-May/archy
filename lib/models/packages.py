
from pathlib import Path
from lib.process_helpers import *


from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class PackageGroup:
    pacman: Optional[Path] = None
    aur: Optional[Path] = None

    @classmethod
    def from_entries(
        cls,
        entries: list[dict],
        *,
        base_dir: Path | str | None = None,
        base_dirs: Iterable[Path | str] | None = None,
    ) -> list["PackageGroup"]:
        search_paths = []

        if base_dirs:
            search_paths.extend(Path(p) for p in base_dirs)
        elif base_dir is not None:
            search_paths.append(Path(base_dir))
        else:
            search_paths.append(Path.cwd())

        search_paths = [path.resolve() for path in search_paths]
        groups: list[PackageGroup] = []

        for entry in entries:
            pacman = entry.get("pacman")
            aur = entry.get("aur")

            if not pacman and not aur:
                raise ValueError("Package group must contain pacman and/or aur")

            def resolve(path_value: str | None) -> Optional[Path]:
                if not path_value:
                    return None

                candidate = Path(path_value)
                if candidate.is_absolute():
                    return candidate.resolve()

                for base_path in search_paths:
                    potential = (base_path / candidate).resolve()
                    if potential.exists():
                        return potential

                return (search_paths[0] / candidate).resolve()

            group = cls(
                pacman=resolve(pacman),
                aur=resolve(aur),
            )

            if group.pacman and not group.pacman.exists():
                raise FileNotFoundError(group.pacman)

            if group.aur and not group.aur.exists():
                raise FileNotFoundError(group.aur)

            groups.append(group)

        return groups

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
