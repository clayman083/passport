from typing import AsyncGenerator

import config  # type: ignore
from aiohttp import web
from aiohttp_metrics import setup as setup_metrics  # type: ignore
from aiohttp_micro import (  # type: ignore
    AppConfig as BaseConfig,
    setup as setup_micro,
)
from asyncpg.pool import create_pool  # type: ignore

from passport.handlers import api


class TokenConfig(config.Config):
    expire = config.IntField(default=900, env="TOKEN_EXPIRE")
    private_key = config.StrField(path="passport.key", env="TOKEN_PRIVATE_KEY")
    public_key = config.StrField(
        path="passport.key.pub", env="TOKEN_PUBLIC_KEY"
    )


class AppConfig(BaseConfig):
    db = config.NestedField(config.PostgresConfig)
    tokens = config.NestedField(TokenConfig)


async def db_engine(app: web.Application) -> AsyncGenerator[None, None]:
    config: AppConfig = app["config"]

    app["db"] = await create_pool(
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
        database=config.db.database,
        min_size=config.db.min_pool_size,
        max_size=config.db.max_pool_size,
    )

    yield

    await app["db"].close()


async def init(app_name: str, config: AppConfig) -> web.Application:
    app = web.Application()

    setup_micro(app, app_name, config)
    setup_metrics(app, app_name=app_name)

    app.cleanup_ctx.append(db_engine)

    app.router.add_routes(
        [
            web.post("/api/login", api.login, name="api.login"),
            web.post(
                "/api/register", api.registration, name="api.registration"
            ),
            web.post("/api/tokens/refresh", api.refresh, name="api.refresh"),
        ]
    )

    return app
