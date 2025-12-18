import os
from os import fspath


def pick_setup(setups_dir="setups"):

    try:
        setups = sorted(
            d for d in os.listdir(fspath(setups_dir))
            if os.path.isdir(os.path.join(fspath(setups_dir), d))
        )
    except FileNotFoundError:
        raise RuntimeError(f"Setup directory '{setups_dir}' does not exist")

    if not setups:
        raise RuntimeError("No setups found")

    while True:
        print("\nSetups:")
        for i, setup in enumerate(setups):
            print(f"{i} -> {setup}")

        choice = input("\nEnter setup number (or 'q' to quit): ").strip()

        if choice.lower() == "q":
            raise SystemExit("Aborted by user")

        if not choice.isdigit():
            print("❌ Please enter a number.")
            continue

        index = int(choice)

        if 0 <= index < len(setups):
            return setups[index]

        print("❌ Number out of range.")
