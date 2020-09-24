from passport.domain import User
from passport.services.users import UserService
from passport.storage import DBStorage
from passport.use_cases import UseCase


class LoginUseCase(UseCase):
    async def execute(self, email: str, password: str) -> User:
        storage = DBStorage(self.app["db"])

        service = UserService(storage)
        user = await service.login(email, password)

        return user


class RegisterUserUseCase(UseCase):
    async def execute(self, email: str, password: str) -> User:
        storage = DBStorage(self.app["db"])

        service = UserService(storage)
        user = await service.register(email, password)

        return user
