from dataclasses import dataclass
from .partition import Partition


@dataclass
class Disk:
    device: str
    wipe: bool
    partitions: list[Partition]

    @classmethod
    def from_config(cls, config: dict) -> "Disk":
        return cls(
            device=config["disk"],
            wipe=config["wipe"],
            partitions=[
                Partition.from_config(part, config["disk"], index + 1)
                for index, part in enumerate(config["partitions"])
            ],
        )

    @classmethod
    def from_storage(cls, storage: list[dict]) -> list["Disk"]:
        return [cls.from_config(disk) for disk in storage]

    def __post_init__(self):
        if not self.device.startswith("/dev/"):
            raise ValueError(f"Invalid disk device: {self.device}")

        # Allow disks without root — only check for duplicates inside THIS disk
        roots = [p for p in self.partitions if p.is_root()]
        if len(roots) > 1:
            raise ValueError("Disk cannot contain more than one root (/) partition")

        fills = [p for p in self.partitions if p.size == "fill"]
        if len(fills) > 1:
            raise ValueError("Only one 'fill' partition is allowed on a disk")

    def partition_plan(self, disk_bytes: int): 
        fixed = [] 
        fill = None 
        for p in self.partitions: 
            size = p.size_bytes(disk_bytes) 
            if size is None: 
                fill = p 
            else: 
                fixed.append((p, size))

        used = sum(size for _, size in fixed) 
        if used > disk_bytes: 
            raise ValueError("Partition sizes exceed disk size") 

        plan = fixed[:]
        if fill:
            remaining = disk_bytes - used
            if remaining <= 0:
                raise ValueError("No space left for 'fill' partition")

            # Let sgdisk allocate the remainder of the disk for the fill
            # partition by leaving its size as ``None``. Calculating an exact
            # byte size here can overshoot the last usable sector because
            # sgdisk aligns partition starts and reserves space for GPT
            # metadata, which leads to failures like exit code 4 when the end
            # LBA is past the disk boundary. Keeping ``None`` preserves the
            # ``0`` placeholder in the sgdisk command so it uses the disk's
            # reported last-usable sector instead of our calculation.
            plan.append((fill, None))
        return plan
