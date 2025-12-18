#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGES_DIR = PROJECT_ROOT / "packages"


def read_packages(command: list[str]) -> list[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr)
        raise

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def write_package_list(path: Path, packages: list[str]) -> None:
    content = "\n".join(sorted(packages))
    if content:
        content += "\n"
    path.write_text(content)
    print(f"Wrote {len(packages)} packages to {path.relative_to(PROJECT_ROOT)}")


def main():
    PACKAGES_DIR.mkdir(exist_ok=True)

    explicit_packages = read_packages(["pacman", "-Qqe"])
    aur_packages = set(read_packages(["pacman", "-Qqm"]))
    pacman_packages = [pkg for pkg in explicit_packages if pkg not in aur_packages]

    write_package_list(PACKAGES_DIR / "pacman.txt", pacman_packages)
    write_package_list(PACKAGES_DIR / "aur.txt", sorted(aur_packages))


if __name__ == "__main__":
    main()
