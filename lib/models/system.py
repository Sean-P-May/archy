from dataclasses import dataclass
from typing import List


@dataclass
class User:
    username: str
    sudo: bool = False


@dataclass
class SystemSettings:
    hostname: str
    timezone: str
    locale: str
    users: List[User]

    @classmethod
    def from_config(cls, config: dict) -> "SystemSettings":
        return cls(
            hostname=config["hostname"],
            timezone=config["timezone"],
            locale=config["locale"],
            users=[
                User(username=user["username"], sudo=user.get("sudo", False))
                for user in config.get("users", [])
            ],
        )
