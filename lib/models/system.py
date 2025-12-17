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

