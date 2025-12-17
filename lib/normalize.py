from lib.models import Disk, Partition, SystemSettings, User, PackageGroup

from pathlib import Path


def parse_system(s: dict) -> SystemSettings:
    return SystemSettings(
        hostname=s["hostname"],
        timezone=s["timezone"],
        locale=s["locale"],
        users=[
            User(
                username=u["username"],
                sudo=u.get("sudo", False),
            )
            for u in s.get("users", [])
        ],
    )

def parse_packages(entries: list[dict]) -> list[PackageGroup]:
    groups: list[PackageGroup] = []

    for entry in entries:
        pacman = entry.get("pacman")
        aur = entry.get("aur")

        if not pacman and not aur:
            raise ValueError("Package group must contain pacman and/or aur")

        group = PackageGroup(
            pacman=Path(pacman).resolve() if pacman else None,
            aur=Path(aur).resolve() if aur else None,
        )

        if group.pacman and not group.pacman.exists():
            raise FileNotFoundError(group.pacman)

        if group.aur and not group.aur.exists():
            raise FileNotFoundError(group.aur)

        groups.append(group)

    return groups


def parse_partition(p: dict, parent_path: str, index) -> Partition:
    path = ""
    if "nvme" in parent_path:
        path =  parent_path + f"p{index}"
    else:
        path =  parent_path + str(index)

    return Partition(
        mount=p["mount"],
        dev_path = path,
        size=p["size"],
        fs=p.get("fs"),
        flags=p.get("flags", []),
    )


def parse_disk(d: dict) -> Disk:
    return Disk(
        device=d["disk"],
        scheme=d["scheme"],
        wipe=d["wipe"],
        partitions=[parse_partition(p, d["disk"], index+1) for index, p in enumerate(d["partitions"])],
    )


def parse_storage(storage: list[dict]) -> list[Disk]:
    return [parse_disk(d) for d in storage]

