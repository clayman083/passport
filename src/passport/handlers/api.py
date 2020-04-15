import attr
from aiohttp import web
from aiohttp_micro.exceptions import (  # type:ignore
    EntityAlreadyExist,
    EntityNotFound,
)
from aiohttp_micro.handlers import (  # type:ignore
    json_response,
    validate_payload,
)
from marshmallow import fields, pre_dump, Schema

from passport.domain import TokenType, User
from passport.exceptions import BadToken, Forbidden
from passport.services.tokens import TokenService
from passport.services.users import UserService
from passport.storage import DBStorage


class CredentialsSchema(Schema):
    entity_cls = User

    key = fields.Int(data_key="id")
    email = fields.Str(required=True)
    password = fields.Str(required=True)

    @pre_dump
    def serialize_entity(self, entity, **kwargs):
        if isinstance(entity, self.entity_cls):
            return attr.asdict(entity, recurse=False)
        else:
            return entity


@validate_payload(CredentialsSchema)
async def registration(payload, request: web.Request) -> web.Response:
    try:
        async with request.app["db"].acquire() as conn:
            storage = DBStorage(conn=conn)
            service = UserService(storage)

            user = await service.register(payload["email"], payload["password"])
    except EntityAlreadyExist:
        return json_response({"errors": {"email": "Already exist"}}, status=422)

    schema = CredentialsSchema(only=("key", "email"))
    response = schema.dump(user)

    return json_response(response, status=201)


@validate_payload(CredentialsSchema)
async def login(payload, request: web.Request) -> web.Response:
    config = request.app["config"]
    token_service = TokenService()

    try:
        async with request.app["db"].acquire() as conn:
            storage = DBStorage(conn=conn)
            service = UserService(storage)

            user = await service.login(payload["email"], payload["password"])
    except Forbidden:
        raise web.HTTPForbidden()
    except EntityNotFound:
        raise web.HTTPNotFound()

    access_token = token_service.generate_token(
        user,
        token_type=TokenType.access,
        private_key=config.tokens.private_key,
        expire=config.tokens.expire,
    )

    refresh_token = token_service.generate_token(
        user,
        token_type=TokenType.refresh,
        private_key=config.tokens.private_key,
        expire=config.tokens.expire,
    )

    schema = CredentialsSchema(only=("key", "email"))
    response = schema.dump(user)

    return json_response(
        response,
        headers={
            "X-ACCESS-TOKEN": access_token,
            "X-REFRESH-TOKEN": refresh_token,
        },
    )


async def refresh(request: web.Request) -> web.Response:
    config = request.app["config"]
    tokens = TokenService()

    token = request.headers.get("X-REFRESH-TOKEN", "")

    if not token:
        raise web.HTTPUnauthorized(text="Auth token required")

    try:
        user = tokens.decode_token(
            token, TokenType.refresh, public_key=config.tokens.public_key
        )
    except BadToken:
        raise web.HTTPForbidden

    try:
        async with request.app["db"].acquire() as conn:
            storage = DBStorage(conn=conn)
            service = UserService(storage)

            user = await service.fetch(key=user.key, active=True)
    except EntityNotFound:
        raise web.HTTPForbidden

    access_token = tokens.generate_token(
        user,
        token_type=TokenType.access,
        private_key=config.tokens.private_key,
        expire=config.tokens.expire,
    )

    schema = CredentialsSchema(only=("key", "email"))
    response = schema.dumps(user)

    return json_response(response, headers={"X-ACCESS-TOKEN": access_token})
