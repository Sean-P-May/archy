"""Capture installed packages and separate native, AUR, and Flatpak lists."""

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

    native_packages = set(capture_packages(["pacman", "-Qqen"]))
    aur_packages = set(capture_packages(["pacman", "-Qqem"]))

    # Ensure we never write overlapping entries to pacman.txt when pacman misreports
    native_packages -= aur_packages

    flatpak_packages: set[str] = set()
    try:
        # Collect both system and user-installed flatpaks
        flatpak_packages.update(capture_packages(["flatpak", "list", "--app", "--columns=application", "--system"]))
        flatpak_packages.update(capture_packages(["flatpak", "list", "--app", "--columns=application", "--user"]))
    except FileNotFoundError:
        print("flatpak not installed; skipping flatpak package capture")
    except RuntimeError as e:
        print(f"Skipping flatpak capture: {e}")

    write_packages(sorted(native_packages), packages_dir / "pacman.txt")
    write_packages(sorted(aur_packages), packages_dir / "aur.txt")
    write_packages(sorted(flatpak_packages), packages_dir / "flatpak.txt")

    print(f"Saved {len(native_packages)} pacman packages to {packages_dir / 'pacman.txt'}")
    print(f"Saved {len(aur_packages)} AUR packages to {packages_dir / 'aur.txt'}")
    print(f"Saved {len(flatpak_packages)} Flatpak apps to {packages_dir / 'flatpak.txt'}")


if __name__ == "__main__":
    main()
