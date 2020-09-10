from aiohttp_storage.storage import DBStorage as AbstractDBStorage
from databases import Database

from passport.domain.storage import Storage
from passport.storage.sessions import SessionDBStorage
from passport.storage.users import UsersDBRepo


class DBStorage(Storage, AbstractDBStorage):
    def __init__(self, database: Database) -> None:
        super().__init__(database=database)

        self.sessions = SessionDBStorage(database=database)
        self.users = UsersDBRepo(database=database)
