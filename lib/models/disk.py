from dataclasses import dataclass
from .partition import Partition

VALID_SCHEMES = {"gpt", "mbr"}


@dataclass
class Disk:
    device: str

    scheme: str
    wipe: bool
    partitions: list[Partition]

    def __post_init__(self):
        if not self.device.startswith("/dev/"):
            raise ValueError(f"Invalid disk device: {self.device}")

        if self.scheme not in VALID_SCHEMES:
            raise ValueError(f"Invalid partition scheme: {self.scheme}")

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
            plan.append((fill, disk_bytes - used)) 
        return plan
