# lib/validator.py

REQUIRED_TOP_LEVEL_KEYS = {"machine", "storage", "packages"}
REQUIRED_MACHINE_KEYS = {"hostname", "timezone", "locale", "users"}
REQUIRED_DISK_KEYS = {"disk", "wipe", "partitions"}
REQUIRED_PARTITION_KEYS = {"mount", "size"}

VALID_MOUNTS = {"/", "/boot", "swap"}


def validate_setup(data):
    # ─── Top-level ─────────────────────────────────────────────
    if not isinstance(data, dict):
        raise ValueError("Setup must be a mapping at top level")

    missing = REQUIRED_TOP_LEVEL_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing top-level keys: {missing}")

    # ─── Machine ───────────────────────────────────────────────
    machine = data["machine"]
    if not isinstance(machine, dict):
        raise ValueError("'machine' must be a mapping")

    missing = REQUIRED_MACHINE_KEYS - machine.keys()
    if missing:
        raise ValueError(f"Missing machine keys: {missing}")

    if not isinstance(machine["users"], list) or not machine["users"]:
        raise ValueError("'machine.users' must be a non-empty list")

    # ─── Storage ───────────────────────────────────────────────
    storage = data["storage"]
    if not isinstance(storage, list) or not storage:
        raise ValueError("'storage' must be a non-empty list")

    for disk in storage:
        if not isinstance(disk, dict):
            raise ValueError("Each disk entry must be a mapping")

        missing = REQUIRED_DISK_KEYS - disk.keys()
        if missing:
            raise ValueError(f"Disk entry missing keys: {missing}")

        partitions = disk["partitions"]
        if not isinstance(partitions, list) or not partitions:
            raise ValueError("Each disk must have partitions")

        has_root = False

        for part in partitions:
            if not isinstance(part, dict):
                raise ValueError("Partition entries must be mappings")

            missing = REQUIRED_PARTITION_KEYS - part.keys()
            if missing:
                raise ValueError(f"Partition missing keys: {missing}")

            mount = part["mount"]

            if mount not in VALID_MOUNTS:
                raise ValueError(f"Invalid mount point: {mount}")

            if mount == "/":
                has_root = True
                if "fs" not in part:
                    raise ValueError("Root partition must define filesystem")

            if mount == "swap" and "fs" in part:
                raise ValueError("Swap partition should not define fs")

        if not has_root:
            raise ValueError("Disk is missing root (/) partition")

    # ─── Packages ──────────────────────────────────────────────
    packages = data["packages"]
    if not isinstance(packages, str):
        raise ValueError("'packages' must be a filename (string)")
