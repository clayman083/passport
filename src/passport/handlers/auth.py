import secrets
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict

from aiohttp import web
from aiohttp_micro.exceptions import EntityNotFound
from aiohttp_micro.handlers import json_response, validate_payload
from marshmallow import fields, pre_dump, Schema

from passport.domain import TokenType, User
from passport.exceptions import BadToken, Forbidden, TokenExpired
from passport.services.tokens import TokenService
from passport.services.users import UserService
from passport.storage import DBStorage


class LoginPayloadSchema(Schema):
    email = fields.Email(required=True, description="Email пользователя")
    password = fields.Str(required=True, description="Пароль пользователя")


@validate_payload(LoginPayloadSchema)
async def login(payload: Dict[str, str], request: web.Request) -> web.Response:
    storage = DBStorage(request.app["db"])

    try:
        service = UserService(storage)
        user = await service.login(payload["email"], payload["password"])
    except Forbidden:
        raise web.HTTPForbidden()
    except EntityNotFound:
        raise web.HTTPNotFound()

    session_key = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=30)

    await storage.sessions.add(user, session_key, expires)

    request.app["logger"].info("User logged in", user=user.email)

    redirect = web.Response(status=200)
    redirect.set_cookie(
        name="session",
        value=session_key,
        max_age=30 * 24 * 60 * 60,
        domain=".clayman.pro",
        httponly=True,
    )

    return redirect


def user_required(f):
    async def wrapper(request: web.Request) -> web.Response:
        storage = DBStorage(request.app["db"])

        user = None

        session_key = request.cookies.get("session", None)
        if session_key:
            user_key = await storage.sessions.fetch(key=session_key)

            if user_key:
                try:
                    user = await storage.users.fetch_by_key(key=user_key)
                except EntityNotFound:
                    raise web.HTTPForbidden

        token = request.headers.get("X-ACCESS-TOKEN", None)
        if token:
            service = TokenService()

            try:
                user = service.decode_token(
                    token,
                    TokenType.access,
                    public_key=request.app["config"].tokens.public_key,
                )
            except (BadToken, TokenExpired):
                raise web.HTTPForbidden

        if user:
            request["user"] = user
            return await f(request)
        else:
            raise web.HTTPUnauthorized(text="Auth required")

    return wrapper


@user_required
async def identify(request: web.Request) -> web.Response:
    token_service = TokenService()
    config = request.app["config"]

    access_token = token_service.generate_token(
        request["user"],
        token_type=TokenType.access,
        private_key=config.tokens.private_key,
        expire=config.tokens.access_token_expire,
    )

    return web.Response(status=200, headers={"X-ACCESS-TOKEN": access_token})


class UserSchema(Schema):
    entity_cls = User

    key = fields.Int(data_key="id")
    email = fields.Str(required=True)

    @pre_dump
    def serialize_entity(self, entity, **kwargs):
        if isinstance(entity, self.entity_cls):
            return asdict(entity)
        else:
            return entity


@user_required
async def profile(request: web.Request) -> web.Response:
    schema = UserSchema()

    return json_response(schema.dump(request["user"]), status=200)


@user_required
async def logout(request: web.Request) -> web.Response:
    request.app["logger"].info("User logged out", user=request["user"].email)

    redirect = web.HTTPFound(location="/")
    redirect.del_cookie(name="session", domain=".clayman.pro")

    raise redirect
