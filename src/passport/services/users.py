from aiohttp_micro.exceptions import EntityAlreadyExist  # type: ignore
from passlib.handlers.pbkdf2 import pbkdf2_sha512  # type: ignore

from passport.domain import User
from passport.domain.storage import Storage
from passport.exceptions import Forbidden


class UserService:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    def encrypt_password(self, password: str) -> str:
        return pbkdf2_sha512.encrypt(password, rounds=10000, salt_size=10)

    def verify_password(self, password: str, encrypted_password: str) -> bool:
        try:
            valid = pbkdf2_sha512.verify(password, encrypted_password)
        except ValueError:
            valid = False
        return valid

    async def register(self, email: str, password: str) -> User:
        exist = await self.storage.users.exists(email)

        if exist:
            raise EntityAlreadyExist()

        key = await self.storage.users.save_user(
            email, self.encrypt_password(password)
        )

        return User(key=key, email=email)

    async def login(self, email: str, password: str) -> User:
        user = await self.storage.users.fetch_by_email(email)

        is_valid = self.verify_password(password, user.password)
        if not is_valid:
            raise Forbidden()

        return user

    async def fetch(self, key: int, active: bool) -> User:
        user = await self.storage.users.fetch_by_key(key)

        return user
