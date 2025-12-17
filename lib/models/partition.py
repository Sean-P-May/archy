
from dataclasses import dataclass, field
from typing import Optional

VALID_FS = {"ext4", "vfat", "btrfs", "xfs"}
VALID_FLAGS = {"esp", "boot"}
SIZE_SUFFIXES = {"K", "M", "G"}


@dataclass
class Partition:
    mount: str
    dev_path: str
    size: str
    fs: Optional[str] = None
    flags: list[str] = field(default_factory=list)

    @classmethod
    def from_config(cls, config: dict, parent_device: str, index: int) -> "Partition":
        """Create a Partition from a raw config entry.

        The device naming for NVMe disks uses the ``p`` suffix, while other
        devices simply append the partition number.
        """
        if "nvme" in parent_device:
            dev_path = f"{parent_device}p{index}"
        else:
            dev_path = f"{parent_device}{index}"

        return cls(
            mount=config["mount"],
            dev_path=dev_path,
            size=config["size"],
            fs=config.get("fs"),
            flags=config.get("flags", []),
        )

    def __post_init__(self):
        # --- MOUNT VALIDATION ---
        # swap (special case)
        if self.mount == "swap":
            pass
        # any path starting with "/" is allowed
        elif self.mount.startswith("/"):
            pass
        else:
            raise ValueError(f"Invalid mount point: {self.mount}")

        # --- SIZE VALIDATION ---
        if self.size != "fill":
            if len(self.size) < 2:
                raise ValueError(f"Invalid size format: {self.size}")

            value, suffix = self.size[:-1], self.size[-1].upper()
            if not value.isdigit() or suffix not in SIZE_SUFFIXES:
                raise ValueError(f"Invalid size format: {self.size}")

        # --- FILESYSTEM RULES ---
        if self.mount == "swap":
            if self.fs is not None:
                raise ValueError("Swap partition must not define fs")
        else:
            if not self.fs:
                raise ValueError(f"Filesystem required for mount {self.mount}")

            if self.fs not in VALID_FS:
                raise ValueError(f"Invalid filesystem: {self.fs}")

        # --- FLAGS VALIDATION ---
        for flag in self.flags:
            if flag not in VALID_FLAGS:
                raise ValueError(f"Invalid partition flag: {flag}")

    def is_boot(self) -> bool:
        return self.mount == "/boot"

    
    def is_root(self) -> bool:
        return self.mount == "/"

    def is_swap(self) -> bool:
        return self.mount == "swap"

    def size_bytes(self, disk_bytes: int) -> Optional[int]:
        if self.size == "fill":
            return None

        value = int(self.size[:-1])
        unit = self.size[-1].upper()

        return value * {
            "K": 1024,
            "M": 1024**2,
            "G": 1024**3,
        }[unit]
