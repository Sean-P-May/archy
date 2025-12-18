# Archy

Archy is an interactive Arch Linux installer script that provisions disks, installs packages, and applies dotfiles based on a declarative YAML setup. Run it from an Arch live environment to reuse the same configuration across multiple machines.

## Repository layout

- `archyinstall.py` – entrypoint that guides you through selecting a setup, partitions disks, runs `pacstrap`, and installs packages inside `/mnt`.
- `bin/copypackages.py` – utility that saves the current system's explicit pacman (native), AUR, and Flatpak packages into `packages/pacman.txt`, `packages/aur.txt`, and `packages/flatpak.txt`.
- `bin/install_packages.py` – installs pacman, AUR, and Flatpak package groups onto an already installed system using a selected setup.
- `bin/sync_configs.py` – syncs dotfiles/config folders from a setup onto an already installed system without running the full installer.
- `lib/` – helpers for loading setups, validating models, partition planning, and package installation.
- `packages/` – shared pacman, AUR, and Flatpak package lists referenced by setups.
- `setups/` – per-machine configuration directories. Each setup must include a `setup.yaml` file. Package lists live under the repo-root `packages/` directory and shared dotfiles/config folders live at the repository root (for example, `configs/`).

## Prerequisites

- Booted into an Arch live ISO with internet access.
- UEFI firmware (the script reads `/sys/firmware/efi/fw_platform_size` and configures `systemd-boot`).
- Run as root so partitioning, mounting, and `pacstrap` succeed.

## Defining a setup

Create a directory under `setups/` (for example, `setups/my-laptop`) containing:

- `setup.yaml` – describes system settings, disks, package lists, and dotfiles.
- Optional dotfiles or configuration folders to copy into the target system. Package list files should live under the repo-root `packages/` directory so multiple setups can share them.

Example `setup.yaml`:

```yaml
system:
  hostname: surfacebook4
  timezone: America/New_York
  locale: en_US.UTF-8
  users:
    - username: sean
      sudo: true

storage:
  - disk: /dev/nvme0n1
    wipe: true
    partitions:
      - mount: /boot
        fs: vfat
        size: 512M
      - mount: swap
        size: 4G
      - mount: /
        fs: btrfs
        size: fill

packages:
  - pacman: pacman.txt
    aur: aur.txt
    flatpak: flatpak.txt

dotfiles:
  - copy_to: /home/sean/.config/
    copy_from: configs
```

Key fields:

- `system` – hostname, timezone, locale, and users. The first sudo-capable user is used for AUR builds.
- `storage` – disks and partitions. Each partition specifies a mount (`/`, `/boot`, or `swap`), filesystem (`ext4`, `btrfs`, `xfs`, `vfat`), and size (e.g., `512M`, `4G`, or `fill` for the remainder).
- `packages` – one or more groups, each pointing to optional `pacman`, `aur`, and `flatpak` package list files. Relative paths are resolved against the repo-root `packages/` directory (for example, `pacman.txt`, `aur.txt`, `flatpak.txt`, or `desktop/pacman.txt`).
- `dotfiles` – entries that copy files or directories into the target filesystem (paths are resolved relative to the setup directory, then `setups/`, then the repository root unless absolute). Dotfiles stored at the repo root (such as `configs/` or `etc/`) are preferred so multiple setups can reuse them; missing paths are skipped.

## Running the installer

1. Boot into the Arch live ISO and clone this repository.
2. From the repo root, run:

   ```bash
   python archyinstall.py
   ```

3. Choose a setup from the menu, review the partition plan, and confirm the prompts.
4. The script will partition disks, mount them under `/mnt`, run `pacstrap`, generate fstab, configure locale/timezone/hostname, create users, and install packages (including AUR packages via the sudo-enabled user).

## Safety notes

- Partitioning is destructive when `wipe: true` is set. Double-check disk identifiers before confirming.
- The script assumes UEFI boot and enables `systemd-boot` plus `NetworkManager` inside the new system.
- Keep your package lists and dotfiles under version control to repeat installations safely.
