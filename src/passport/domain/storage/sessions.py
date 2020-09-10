from datetime import datetime
from typing import Protocol

from passport.domain import User


class SessionRepo(Protocol):
    async def fetch(self, key: str) -> int:
        ...

    async def add(self, user: User, key: str, expires: datetime) -> None:
        ...

    async def remove(self, key: str) -> None:
        ...
