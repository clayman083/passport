import ujson
from typing import Dict

from aiohttp import web


async def get_payload(request: web.Request) -> Dict:
    if 'application/json' in request.content_type:
        payload = await request.json()
    else:
        payload = await request.post()
    return dict(payload)


async def index(request):
    app_config = request.app.config['app']
    return web.json_response({
        'project': app_config['name'],
        'host': app_config['hostname']
    }, dumps=ujson.dumps)
