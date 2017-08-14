from aiohttp import web

from passport.handlers import json_response
from passport.validation import ValidationError


class ResourceNotFound(Exception):
    pass


async def catch_exceptions_middleware(app, handler):
    async def middleware_handler(request: web.Request):
        try:
            return await handler(request)
        except ResourceNotFound:
            raise web.HTTPNotFound
        except ValidationError as exc:
            return json_response(exc.errors, status=400)
        except Exception as exc:
            if isinstance(exc, (web.HTTPClientError, )):
                raise

            # send error to sentry
            if request.app.raven:
                request.app.raven.captureException()
            raise web.HTTPInternalServerError

    return middleware_handler
