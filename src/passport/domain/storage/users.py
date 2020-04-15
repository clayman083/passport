from abc import ABC, abstractmethod

from passport.domain import User


class UsersRepo(ABC):
    @abstractmethod
    async def fetch_by_key(self, key: int) -> User:
        pass

    @abstractmethod
    async def fetch_by_email(self, email: str) -> User:
        pass

    @abstractmethod
    async def exists(self, email: str) -> bool:
        pass

    @abstractmethod
    async def save_user(self, email: str, password: str) -> int:
        pass
