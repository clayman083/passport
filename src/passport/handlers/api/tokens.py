from aiohttp import web
from aiohttp_micro.exceptions import EntityNotFound
from aiohttp_micro.handlers import json_response
from aiohttp_openapi import JSONResponse, register_operation

from passport.domain import TokenType
from passport.exceptions import BadToken
from passport.handlers import (
    RefreshTokenParameter,
    session_required,
    SessionParameter,
    UserResponseSchema,
)
from passport.services.tokens import TokenDecoder, TokenGenerator
from passport.services.users import UserService
from passport.storage import DBStorage


@register_operation(
    description="Get access token for user by session",
    parameters=(SessionParameter,),
    responses=(
        JSONResponse(
            description="User access token",
            schema=UserResponseSchema,  # type: ignore
        ),
    ),
)
@session_required
async def access(request: web.Request) -> web.Response:
    config = request.app["config"]
    generator = TokenGenerator(private_key=config.tokens.private_key)

    access_token = generator.generate(
        request["user"], expire=config.tokens.access_token_expire
    )

    schema = UserResponseSchema()
    response = schema.dump({"user": request["user"]})

    return json_response(response, headers={"X-ACCESS-TOKEN": access_token})


@register_operation(
    description="Refresh user's access token",
    parameters=(RefreshTokenParameter,),
    responses=(
        JSONResponse(
            description="User access token",
            schema=UserResponseSchema,  # type: ignore
        ),
    ),
)
async def refresh(request: web.Request) -> web.Response:
    config = request.app["config"]

    token = request.headers.get("X-REFRESH-TOKEN", "")

    if not token:
        raise web.HTTPUnauthorized(text="Refresh token required")

    try:
        decoder = TokenDecoder(public_key=config.tokens.public_key)
        user = decoder.decode(token, TokenType.refresh)
    except BadToken:
        raise web.HTTPForbidden

    try:
        storage = DBStorage(request.app["db"])

        service = UserService(storage)
        user = await service.fetch(key=user.key, active=True)
    except EntityNotFound:
        raise web.HTTPForbidden

    generator = TokenGenerator(private_key=config.tokens.private_key)

    access_token = generator.generate(
        user=user, expire=config.tokens.access_token_expire
    )

    schema = UserResponseSchema()
    response = schema.dump({"user": user})

    return json_response(response, headers={"X-ACCESS-TOKEN": access_token})
