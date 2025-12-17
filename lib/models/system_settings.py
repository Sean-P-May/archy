from dataclasses import dataclass
from typing import List

@dataclass
class SystemSettings:
    hostname : str
    timezone : str
    locale: str
    users: List[str]



