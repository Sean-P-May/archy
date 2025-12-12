from dataclasses import dataclass, field
from typing import Optional

VALID_MOUNTS = {"/", "/boot", "swap"}
VALID_FS = {"ext4", "vfat", "btrfs", "xfs"}
VALID_FLAGS = {"esp", "boot"}
SIZE_SUFFIXES = {"K", "M", "G"}


@dataclass
class Partition:
    mount: str
    size: str
    fs: Optional[str] = None
    flags: list[str] = field(default_factory=list)

    def __post_init__(self):
        # mount validation
        if self.mount not in VALID_MOUNTS:
            raise ValueError(f"Invalid mount point: {self.mount}")

        # size validation
        if self.size != "fill":
            if len(self.size) < 2:
                raise ValueError(f"Invalid size format: {self.size}")

            value, suffix = self.size[:-1], self.size[-1].upper()
            if not value.isdigit() or suffix not in SIZE_SUFFIXES:
                raise ValueError(f"Invalid size format: {self.size}")

        # filesystem rules
        if self.mount == "swap":
            if self.fs is not None:
                raise ValueError("Swap partition must not define fs")
        else:
            if not self.fs:
                raise ValueError(f"Filesystem required for mount {self.mount}")

            if self.fs not in VALID_FS:
                raise ValueError(f"Invalid filesystem: {self.fs}")

        # flags validation
        for flag in self.flags:
            if flag not in VALID_FLAGS:
                raise ValueError(f"Invalid partition flag: {flag}")

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

