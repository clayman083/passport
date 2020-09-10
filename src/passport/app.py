import os

import config  # type: ignore
from aiohttp import web
from aiohttp_metrics import setup as setup_metrics  # type: ignore
from aiohttp_micro import (  # type: ignore
    AppConfig as BaseConfig,
    setup as setup_micro,
)
from aiohttp_storage import setup as setup_storage, StorageConfig

from passport.handlers import api, auth


class TokenConfig(config.Config):
    access_token_expire = config.IntField(
        default=900, env="ACCESS_TOKEN_EXPIRE"
    )
    refresh_token_expire = config.IntField(
        default=43200, env="REFRESH_TOKEN_EXPIRE"
    )
    private_key = config.StrField(path="passport.key", env="TOKEN_PRIVATE_KEY")
    public_key = config.StrField(
        path="passport.key.pub", env="TOKEN_PUBLIC_KEY"
    )


class AppConfig(BaseConfig):
    db = config.NestedField[StorageConfig](StorageConfig)
    tokens = config.NestedField(TokenConfig)


async def init(app_name: str, config: AppConfig) -> web.Application:
    app = web.Application()

    app["app_root"] = os.path.dirname(__file__)

    setup_micro(app, app_name, config)
    setup_metrics(app, app_name=app_name)
    setup_storage(
        app,
        root=os.path.join(app["app_root"], "storage"),
        config=app["config"].db,
    )

    app.router.add_routes(
        [
            web.put("/auth/identify", auth.identify, name="auth.identify"),
            web.post("/auth/login", auth.login, name="auth.login"),
            web.post("/auth/logout", auth.logout, name="auth.logout"),
            web.get("/auth/profile", auth.profile, name="auth.profile"),
        ]
    )

    app.router.add_routes(
        [
            web.get("/api/me", api.me, name="api.me"),
            web.post("/api/login", api.login, name="api.login"),
            web.post(
                "/api/register", api.registration, name="api.registration"
            ),
            web.post("/api/tokens/refresh", api.refresh, name="api.refresh"),
        ]
    )

    return app
