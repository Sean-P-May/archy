import subprocess
from typing import List

from .models.disk import Disk


def build_partition_actions(disk: Disk, dry_run=False):
    """
    Build (and optionally print) the sgdisk + filesystem creation commands
    needed to partition the disk. No commands execute unless dry_run=False.
    """

    device = disk.device
    scheme = disk.scheme
    wipe = disk.wipe
    partitions = disk.partitions

    # ---- Inline GPT type logic ----
    def gpt_type_for(part):
        if part.mount == "/boot":
            return "ef00"  # EFI System Partition
        if part.mount == "swap":
            return "8200"  # Swap
        return "8300"      # Normal Linux filesystem

    # ---- Inline size formatter ----
    def format_size(size_bytes):
        if size_bytes is None:
            return "0"  # fill-to-end
        if size_bytes % (1024**3) == 0:
            return f"+{size_bytes // (1024**3)}G"
        if size_bytes % (1024**2) == 0:
            return f"+{size_bytes // (1024**2)}M"
        if size_bytes % 1024 == 0:
            return f"+{size_bytes // 1024}K"
        return f"+{size_bytes}"

    # ---- Step 1: probe disk size ----
    result = subprocess.run(
        ["blockdev", "--getsize64", device],
        capture_output=True,
        text=True
    )
    disk_bytes = int(result.stdout.strip())

    # ---- Step 2: determine sizes ----
    plan = disk.partition_plan(disk_bytes)

    actions = []

    # ---- wipe disk if requested ----
    if wipe:
        actions.append({
            "desc": "wipe disk",
            "cmd": ["sgdisk", "--zap-all", device]
        })

    # ---- Step 3: build sgdisk partition creation commands ----
    number = 1
    for part, size_bytes in plan:
        part_type = gpt_type_for(part)
        size_str = format_size(size_bytes)

        label = (
            "boot" if part.mount == "/boot" else
            "swap" if part.mount == "swap" else
            "root" if part.mount == "/" else
            part.mount.strip("/").replace("/", "_")
        )

        # 1. create the partition
        actions.append({
            "desc": f"create partition {number}",
            "cmd": ["sgdisk", f"-n{number}:0:{size_str}", device]
        })

        # 2. set type
        actions.append({
            "desc": f"set type for partition {number}",
            "cmd": ["sgdisk", f"-t{number}:{part_type}", device]
        })

        # 3. set label
        actions.append({
            "desc": f"label partition {number}",
            "cmd": ["sgdisk", f"-c{number}:{label}", device]
        })

        number += 1

    # ---- Step 4: build filesystem creation commands ----

    number = 1
    for part in partitions:
        # derive partition device name
        # nvme devices use p suffix
        part_dev = f"{device}p{number}" if "nvme" in device else f"{device}{number}"

        if part.mount == "swap":
            actions.append({
                "desc": f"make swap on partition {number}",
                "cmd": ["mkswap", part_dev]
            })
            number += 1
            continue

        if part.mount == "/boot" and part.fs == "vfat":
            actions.append({
                "desc": f"make FAT32 filesystem for EFI on partition {number}",
                "cmd": ["mkfs.vfat", "-F", "32", part_dev]
            })
            number += 1
            continue

        # General Linux filesystems
        if part.fs == "ext4":
            actions.append({
                "desc": f"make ext4 filesystem on partition {number}",
                "cmd": ["mkfs.ext4", "-F", part_dev]
            })
        elif part.fs == "btrfs":
            actions.append({
                "desc": f"make btrfs filesystem on partition {number}",
                "cmd": ["mkfs.btrfs", "-f", part_dev]
            })
        elif part.fs == "xfs":
            actions.append({
                "desc": f"make xfs filesystem on partition {number}",
                "cmd": ["mkfs.xfs", "-f", part_dev]
            })
        else:
            raise ValueError(f"Unhandled filesystem type: {part.fs}")

        number += 1
        

    return actions



def partition_disks(disks: List[Disk], dry_run=True):

    total_actions = []

    for disk in disks:
        actions = build_partition_actions(disk)

        print("\nDisk: " + disk.device)
        for action in actions:
            print(f"  #{action['desc']}")
            print("    " + " ".join(action["cmd"]))
        print("\n")

        total_actions += actions


    if not (input("confirm disk setup: (y or yes) ").lower() in ["yes","y"]):
        print("exiting!!")
        exit()


    if not dry_run:
        for action in total_actions:
            print(f"Running: {' '.join(action['cmd'])}")
            try:
                result = subprocess.run(
                    action["cmd"],
                    capture_output=True,
                    check=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                print(f"Partitioning step failed: {action['desc']}")
                print(f"Command: {' '.join(action['cmd'])}")
                if exc.stdout:
                    print(f"stdout:\n{exc.stdout.strip()}")
                if exc.stderr:
                    print(f"stderr:\n{exc.stderr.strip()}")
                raise
            else:
                if result.stdout:
                    print(result.stdout.strip())
                if result.stderr:
                    print(result.stderr.strip())
            
            





        




        



