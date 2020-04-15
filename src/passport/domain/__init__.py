from enum import Enum

import attr


class TokenType(Enum):
    access = "access"
    refresh = "refresh"


@attr.dataclass(slots=True, kw_only=True)
class User:
    key: int
    email: str
    password: str = ""
