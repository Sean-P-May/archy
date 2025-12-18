#!/usr/bin/env python3
"""Sync dotfiles/configs from a setup onto an already installed system."""

from pathlib import Path
import os
import sys

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from lib.install_helpers import apply_dotfiles
from lib.loader import load_setup_yaml
from lib.models import SystemSettings
from lib.picker import pick_setup


def ensure_root():
    if os.geteuid() != 0:
        sys.exit("This script must be run as root.")


def main():
    ensure_root()

    setups_root = repo_root / "setups"

    setup = pick_setup(setups_root)
    base_dir = setups_root / setup
    print(f"Selected setup: {setup}")

    raw = load_setup_yaml(setup, setups_root=setups_root)
    machine_config = raw.get("machine") or raw.get("system")
    if not machine_config:
        raise KeyError("Setup file missing 'system' configuration")

    system = SystemSettings.from_config(machine_config)
    dotfiles_entries = raw.get("dotfiles", [])

    if not dotfiles_entries:
        print("No dotfiles configured; nothing to sync.")
        return

    resource_roots = [base_dir, setups_root, repo_root]
    apply_dotfiles(dotfiles_entries, resource_roots, users=system.users, root_path="/")

    print("Dotfiles synced successfully.")


if __name__ == "__main__":
    main()
