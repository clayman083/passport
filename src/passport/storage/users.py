from datetime import datetime

import sqlalchemy
from aiohttp_micro.exceptions import EntityNotFound  # type: ignore
from aiohttp_storage.storage import metadata
from databases import Database
from sqlalchemy import func
from sqlalchemy.orm.query import Query

from passport.domain import User
from passport.domain.storage.users import UsersRepo


users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "email", sqlalchemy.String(255), nullable=False, unique=True
    ),
    sqlalchemy.Column("password", sqlalchemy.String(255), nullable=False),
    sqlalchemy.Column("is_active", sqlalchemy.Boolean, default=True),
    sqlalchemy.Column(
        "last_login", sqlalchemy.DateTime, default=datetime.utcnow
    ),
    sqlalchemy.Column(
        "created_on", sqlalchemy.DateTime, default=datetime.utcnow
    ),
)


class UsersDBRepo(UsersRepo):
    def __init__(self, database: Database) -> None:
        self._database = database

    def get_query(self) -> Query:
        return sqlalchemy.select(
            [users.c.id, users.c.email, users.c.password]
        ).where(
            users.c.is_active == True  # noqa: E712
        )

    def _process_row(self, row) -> User:
        return User(key=row["id"], email=row["email"], password=row["password"])

    async def fetch_by_key(self, key: int) -> User:
        query = self.get_query().where(users.c.id == key)
        row = await self._database.fetch_one(query)

        if not row:
            raise EntityNotFound()

        return self._process_row(row)

    async def fetch_by_email(self, email: str) -> User:
        query = self.get_query().where(users.c.email == email)
        row = await self._database.fetch_one(query)

        if not row:
            raise EntityNotFound()

        return self._process_row(row)

    async def exists(self, email: str) -> bool:
        query = sqlalchemy.select([func.count(users.c.id)]).where(
            users.c.email == email
        )
        count = await self._database.fetch_val(query)

        return count > 0

    async def save_user(self, email: str, password: str) -> int:
        key = await self._database.execute(
            users.insert().returning(users.c.id),
            values={
                "email": email,
                "password": password,
                "is_active": True,
                "created_on": datetime.now(),
            },
        )

        return key
