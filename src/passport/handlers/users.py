import functools

from aiohttp import web

from passport.domain import TokenType
from passport.exceptions import BadToken, TokenExpired
from passport.services.tokens import TokenService


def user_required(token_type=TokenType.access, token_headers="X-ACCESS-TOKEN"):
    if token_type not in (TokenType.access, TokenType.refresh):
        raise ValueError(f"Unsupported token type: {token_type}")

    service = TokenService()

    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(request: web.Request):
            token = request.headers.get(token_headers, "")

            if not token:
                raise web.HTTPUnauthorized(text="Auth token required")

            try:
                user = service.decode_token(
                    token,
                    token_type,
                    public_key=request.app["config"].tokens.public_key,
                )
            except (BadToken, TokenExpired):
                raise web.HTTPForbidden

            request["user"] = user

            return await f(request)

        return wrapped

    return wrapper
