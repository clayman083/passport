from asyncpg.connection import Connection  # type: ignore

from passport.domain.storage import Storage
from passport.storage.users import UsersDBRepo


class DBStorage(Storage):
    __slots__ = ("_conn", "_tr", "_accounts", "_operations", "_tags")

    def __init__(self, conn: Connection) -> None:
        self._conn = conn

        self.users = UsersDBRepo(self._conn)

    async def __aenter__(self):
        self._tr = self._conn.transaction()
        await self._tr.start()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()

    async def commit(self):
        await self._tr.commit()

    async def rollback(self):
        await self._tr.rollback()
