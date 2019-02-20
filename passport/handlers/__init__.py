from typing import Dict

import ujson  # type: ignore
from aiohttp import web


async def get_payload(request: web.Request) -> Dict:
    if 'application/json' in request.content_type:
        payload = await request.json()
    else:
        payload = await request.post()
    return dict(payload)


def json_response(data, status: int = 200, **kwargs) -> web.Response:
    return web.json_response(data, dumps=ujson.dumps, status=status, **kwargs)
