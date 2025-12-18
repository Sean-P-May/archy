"""Capture installed packages and separate native vs AUR lists."""

from pathlib import Path
import subprocess


def capture_packages(args: list[str]) -> list[str]:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to run {' '.join(args)}: {result.stderr}")

    packages = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return sorted(packages)


def write_packages(packages: list[str], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(packages) + ("\n" if packages else ""))


def main():
    repo_root = Path(__file__).resolve().parent.parent
    packages_dir = repo_root / "packages"

    native_packages = capture_packages(["pacman", "-Qqen"])
    aur_packages = capture_packages(["pacman", "-Qqem"])

    write_packages(native_packages, packages_dir / "pacman.txt")
    write_packages(aur_packages, packages_dir / "aur.txt")

    print(f"Saved {len(native_packages)} pacman packages to {packages_dir / 'pacman.txt'}")
    print(f"Saved {len(aur_packages)} AUR packages to {packages_dir / 'aur.txt'}")


if __name__ == "__main__":
    main()
