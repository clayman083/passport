from aiohttp import web
import ujson

from passport.exceptions import ResourceNotFound, ValidationError


async def catch_exceptions_middleware(app, handler):
    async def middleware_handler(request: web.Request):
        try:
            return await handler(request)
        except ResourceNotFound:
            raise web.HTTPNotFound
        except ValidationError as exc:
            return web.json_response(exc.errors, status=400, dumps=ujson.dumps)
        except Exception as exc:
            if isinstance(exc, (web.HTTPClientError, )):
                raise

            # if not app.config['app'].get('debug', False):
            #     app.logger.error(exc)
            # else:
            raise exc

            # raise web.HTTPInternalServerError()
    return middleware_handler
