import functools
from typing import AsyncGenerator

from aiohttp import ClientSession, web
from config import Config, StrField

from passport.domain import User
from passport.exceptions import BadToken, TokenExpired
from passport.services.tokens import TokenDecoder


class PassportConfig(Config):
    host = StrField(env="PASSPORT_HOST")
    public_key = StrField()


def user_required(header: str = "X-ACCESS-TOKEN"):
    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(request):
            token = request.headers.get(header, "")

            if not token:
                raise web.HTTPUnauthorized(text="Auth token required")

            try:
                config = request.app["config"]
                decoder = TokenDecoder(public_key=config.passport.public_key)
                user: User = decoder.decode(token)
            except (BadToken, TokenExpired):
                raise web.HTTPForbidden

            request["user"] = user

            return await f(request)

        return wrapped

    return wrapper


async def passport_ctx(app: web.Application) -> AsyncGenerator[None, None]:
    config = app["config"]

    app["logger"].debug("Fetch passport keys")

    if not config.passport.host:
        app["logger"].error("Passport host should be defined")
        raise RuntimeError("Passport host should be defined")

    async with ClientSession() as session:
        async with session.get(f"{config.passport.host}/api/keys") as resp:
            if resp.status != 200:
                app["logger"].error(
                    "Fetch passport keys failed", status=resp.status
                )
                raise RuntimeError("Could not fetch passport keys")

            keys = await resp.json()

            config.passport.public_key = keys["public"]

    yield


def setup(app: web.Application) -> None:
    app.cleanup_ctx.append(passport_ctx)
