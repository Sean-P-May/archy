from lib.picker import pick_setup
from lib.loader import load_and_validate_setup


def main():
    # 1. Pick which setup to use
    setup = pick_setup()
    print(f"Selected setup: {setup}")

    # 2. Load YAML → validate → normalize → models
    config = load_and_validate_setup(setup)

    # 3. At this point, everything is safe & executable
    #    No raw YAML, no unchecked values
    disks = config["disks"]
    machine = config["machine"]
    packages = config["packages"]

    print("✅ Setup loaded and validated")
    print(f"Machine hostname: {machine['hostname']}")
    print(f"Disks to configure: {[d.device for d in disks]}")
    print(f"Packages file: {packages}")

    # NEXT STEPS (not implemented yet):
    # - probe disk sizes
    # - generate partition plan
    # - dry-run sgdisk commands
    # - confirm
    # - execute


if __name__ == "__main__":
    main()

