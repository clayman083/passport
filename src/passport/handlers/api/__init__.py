from aiohttp import web
from aiohttp_micro.handlers import json_response
from aiohttp_openapi import JSONResponse, register_operation
from marshmallow import fields, Schema


class KeysResponseSchema(Schema):
    public = fields.Str()


@register_operation(
    description="Get access token for user by session",
    responses=(
        JSONResponse(
            description="User access token",
            schema=KeysResponseSchema,  # type: ignore
        ),
    ),
)
async def keys(request: web.Request) -> web.Response:
    config = request.app["config"]

    schema = KeysResponseSchema()
    response = schema.dump({"public": config.tokens.public_key})

    return json_response(response)
