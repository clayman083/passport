import logging
import os

import pkg_resources
from aiohttp import web
from asyncpg.pool import create_pool
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from raven import Client as Raven
from raven_aiohttp import AioHttpTransport

from passport import middlewares
from passport.config import Config
from passport.handlers import api, service


async def db_engine(app) -> None:
    config = app['config']

    app['db'] = await create_pool(
        user=config.get('db_user'), database=config.get('db_name'),
        host=config.get('db_host'), password=config.get('db_password'),
        port=config.get('db_port'), min_size=1, max_size=10
    )

    yield

    await app['db'].close()


async def init(config: Config, logger: logging.Logger=None) -> web.Application:
    app = web.Application(logger=logger, middlewares=[
        middlewares.catch_exceptions_middleware,
        middlewares.prometheus_middleware
    ])

    app['config'] = config

    if config.get('sentry_dsn', None):
        app['raven'] = Raven(config['sentry_dsn'], transport=AioHttpTransport)

    app['distribution'] = pkg_resources.get_distribution('passport')

    app['metrics_registry'] = CollectorRegistry()
    app['metrics'] = {
        'REQUEST_COUNT': Counter(
            'requests_total', 'Total request count',
            ['app_name', 'method', 'endpoint', 'http_status'],
            registry=app['metrics_registry']
        ),
        'REQUEST_LATENCY': Histogram(
            'requests_latency_seconds', 'Request latency',
            ['app_name', 'endpoint'], registry=app['metrics_registry']
        ),
        'REQUEST_IN_PROGRESS': Gauge(
            'requests_in_progress_total', 'Requests in progress',
            ['app_name', 'endpoint', 'method'], registry=app['metrics_registry']
        )
    }

    app.cleanup_ctx.append(db_engine)

    app.router.add_get('/', service.index, name='index')

    app.router.add_get('/-/health', service.health, name='health')
    app.router.add_get('/-/metrics', service.metrics, name='metrics')

    app.router.add_get('/api/identify', api.identify, name='api.identify')
    app.router.add_post('/api/login', api.login, name='api.login')
    app.router.add_post('/api/refresh', api.refresh, name='api.refresh')
    app.router.add_post('/api/register', api.registration,
                        name='api.registration')

    return app


config_schema = {
    'app_name': {'type': 'string', 'required': True},
    'app_root': {'type': 'string', 'required': True},
    'app_hostname': {'type': 'string'},
    'app_host': {'type': 'string'},
    'app_port': {'type': 'string'},

    'secret_key': {'type': 'string', 'required': True},
    'access_token_expire': {'type': 'integer', 'required': True, 'coerce': int},
    'refresh_token_expire': {'type': 'integer', 'required': True,
                             'coerce': int},

    'access_log': {'type': 'string', 'required': True},

    'db_name': {'type': 'string', 'required': True},
    'db_user': {'type': 'string', 'required': True},
    'db_password': {'type': 'string', 'required': True},
    'db_host': {'type': 'string', 'required': True},
    'db_port': {'type': 'integer', 'required': True, 'coerce': int},

    'consul_host': {'type': 'string', 'required': True},
    'consul_port': {'type': 'integer', 'required': True, 'coerce': int},

    'sentry_dsn': {'type': 'string'},

    'logging': {'type': 'dict', 'required': True}
}


def configure(config_file: str=None) -> Config:
    app_root = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))

    config = Config(config_schema, {
        'app_name': 'passport',
        'app_root': app_root,

        'access_token_expire': 900,  # 5 minutes
        'refresh_token_expire': 2592000,  # 30 days
        'secret_key': 'secret',

        'db_name': 'passport',
        'db_user': 'passport',
        'db_password': 'passport'
    })

    if config_file:
        config.update_from_yaml(config_file, silent=True)

    for key in iter(config_schema.keys()):
        config.update_from_env_var(key)

    config.validate()

    return config
