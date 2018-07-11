import time

from aiohttp import web

from passport.handlers import json_response
from passport.validation import ValidationError


class ResourceNotFound(Exception):
    pass


@web.middleware
async def catch_exceptions_middleware(request: web.Request, handler):
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


@web.middleware
async def prometheus_middleware(request: web.Request, handler):
    app_name = request.app.config.get('app_name')

    start_time = time.time()
    request.app['metrics']['REQUEST_IN_PROGRESS'].labels(
        app_name, request.path, request.method).inc()

    response = await handler(request)

    resp_time = time.time() - start_time
    request.app['metrics']['REQUEST_LATENCY'].labels(
        app_name, request.path).observe(resp_time)
    request.app['metrics']['REQUEST_IN_PROGRESS'].labels(
        app_name, request.path, request.method).dec()
    request.app['metrics']['REQUEST_COUNT'].labels(
        app_name, request.method, request.path, response.status).inc()

    return response
