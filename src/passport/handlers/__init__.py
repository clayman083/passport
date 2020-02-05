import functools
from typing import Type

from aiohttp import web
from marshmallow import Schema, ValidationError

from passport.handlers import get_payload, json_response
from passport.services.tokens import TokenService


def validate_payload(schema_cls: Type[Schema]):
    def wrapper(f):
        async def wrapped(request: web.Request) -> web.Response:
            payload = await get_payload(request)

            try:
                schema = schema_cls()
                document = schema.load(payload)
            except ValidationError as exc:
                return json_response({"errors": exc.messages}, status=422)

            return await f(document, request)

        return wrapped

    return wrapper


def token_required(token_type, token_name):
    if token_type not in ("access", "refresh"):
        raise ValueError("Unsupported token type: {token_type}")

    service = TokenService()

    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(request: web.Request):
            token = request.headers.get(token_name, "")

            if not token:
                raise web.HTTPUnauthorized(text="Token required")

            user = service.decode_token(
                token,
                token_type,
                public_key=request.app["config"].tokens.public_key,
            )

            return await f(user, request)

        return wrapped

    return wrapper
