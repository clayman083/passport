from datetime import datetime

from aiohttp import web
from aiohttp_micro.handlers import json_response
from marshmallow import fields, Schema, ValidationError

from passport.entities import TokenType, User
from passport.handlers import token_required, validate_payload
from passport.services.tokens import TokenService
from passport.storage.users import create_user, verify_password


class CredentialsSchema(Schema):
    email = fields.Str(required=True)
    password = fields.Str(required=True)


@validate_payload(CredentialsSchema)
async def registration(payload, request: web.Request) -> web.Response:
    async with request.app["db"].acquire() as conn:
        query = """
          SELECT COUNT(id) FROM users WHERE users.email = '{0}'
        """.format(
            payload["email"]
        )
        count = await conn.fetchval(query)
        if count:
            raise ValidationError({"email": "Already used"})

        await create_user(payload["email"], payload["password"], True, conn)

    return json_response({"email": payload["email"]}, status=201)


@validate_payload(CredentialsSchema)
async def login(payload, request: web.Request) -> web.Response:
    config = request.app["config"]
    service = TokenService()

    async with request.app["db"].acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, password FROM users WHERE (
                users.email = $1 AND is_active = TRUE
            )
        """,
            payload["email"],
        )
        if not user:
            raise web.HTTPNotFound(text="User does not found")

        if not verify_password(payload["password"], user["password"]):
            raise ValidationError({"password": "Wrong password"})

        await conn.execute(
            """
            UPDATE users SET last_login = $1 WHERE id = $2
        """,
            datetime.now(),
            user["id"],
        )

    access_token = service.generate_token(
        user,
        token_type=TokenType.access,
        private_key=config.tokens.private_key,
        expire=config.tokens.expire,
    )

    refresh_token = service.generate_token(
        user,
        token_type=TokenType.refresh,
        private_key=config.tokens.private_key,
        expire=config.tokens.expire,
    )

    headers = {
        "X-ACCESS-TOKEN": access_token.decode("utf-8"),
        "X-REFRESH-TOKEN": refresh_token.decode("utf-8"),
    }

    return json_response({"email": user["email"]}, headers=headers)


@token_required("refresh", "X-REFRESH-TOKEN")
async def refresh(user: User, request: web.Request) -> web.Response:
    config = request.app["config"]
    service = TokenService()

    async with request.app["db"].acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, is_active FROM users WHERE (
                id = $1 AND is_active = TRUE
            )
        """,
            user.key,
        )

        if not user:
            raise web.HTTPNotFound(text="User does not found")

    access_token = service.generate_token(
        user,
        token_type=TokenType.access,
        private_key=config.tokens.private_key,
        expire=config.tokens.expire,
    )

    headers = {
        "X-ACCESS-TOKEN": access_token.decode("utf-8"),
    }

    return json_response({"email": user.email}, headers=headers)
