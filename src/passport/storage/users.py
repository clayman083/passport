from datetime import datetime

from aiohttp_micro.exceptions import EntityNotFound  # type: ignore
from asyncpg import Record  # type: ignore
from asyncpg.connection import Connection  # type: ignore

from passport.domain import User
from passport.domain.storage.users import UsersRepo


class UsersDBRepo(UsersRepo):
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def _process_row(self, row: Record) -> User:
        return User(key=row["id"], email=row["email"], password=row["password"])

    async def fetch_by_key(self, key: int) -> User:
        query = """
          SELECT
            id, email, password
          FROM users
          WHERE id = $1 AND is_active = TRUE
        """
        row = await self._conn.fetchrow(query, key)

        if not row:
            raise EntityNotFound()

        return self._process_row(row)

    async def fetch_by_email(self, email: str) -> User:
        query = """
          SELECT
            id, email, password
          FROM users
          WHERE email = $1 AND is_active = TRUE
        """
        row = await self._conn.fetchrow(query, email)

        if not row:
            raise EntityNotFound()

        return self._process_row(row)

    async def exists(self, email: str) -> bool:
        query = """
          SELECT COUNT(id) FROM users WHERE users.email = $1
        """
        count = await self._conn.fetchval(query, email)

        return count > 0

    async def save_user(self, email: str, password: str) -> int:
        now = datetime.now()

        query = """
          INSERT INTO users (email, password, is_active, created_on)
            VALUES ($1, $2, $3, $4)
          RETURNING id
        """
        key = await self._conn.fetchval(query, email, password, True, now)

        return key
