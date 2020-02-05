import config
from aiohttp import web
from aiohttp_metrics import setup as setup_metrics  # type: ignore
from aiohttp_micro import setup as setup_micro  # type: ignore
from asyncpg.pool import create_pool  # type: ignore

from passport.handlers import api


class DBConfig(config.PostgresConfig):
    min_pool_size = config.IntField(default=1, env="POSTGRES_MIN_POOL_SIZE")
    max_pool_size = config.IntField(default=1, env="POSTGRES_MAX_POOL_SIZE")


class TokenConfig(config.Config):
    expire = config.IntField()
    secret_key = config.StrField()


class AppConfig(config.Config):
    consul = config.NestedField(config.ConsulConfig, key="consul")
    db = config.NestedField(DBConfig, key="db")
    debug = config.BoolField(default=False)
    sentry_dsn = config.StrField()
    tokens = config.NestedField(TokenConfig, key="tokens")


async def db_engine(app: web.Application) -> None:
    config: AppConfig = app["config"]

    app["db"] = await create_pool(
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
        database=config.db.name,
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
