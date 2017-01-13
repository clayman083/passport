import asyncio
import logging

import os

from aiohttp import web
from asyncpg.pool import create_pool, Pool

from passport.config import Config, schema as config_schema
from passport.exceptions import ImproperlyConfigured, ValidationError
from passport.handlers import api, index
from passport.middlewares import catch_exceptions_middleware
from passport.utils import register_handler


class App(web.Application):
    def __init__(self, *args, config=None, **kwargs):
        super(App, self).__init__(**kwargs)

        self._config = config  # type: Config
        self._db = None  # type: Pool

    @property
    def config(self) -> Config:
        return self._config

    @property
    def db(self) -> Pool:
        return self._db

    def copy(self):
        raise NotImplementedError


async def cleanup(instance: App):
    instance.logger.info('Closing app')

    await instance.db.close()


async def init(config: Config, logger: logging.Logger=None,
               loop: asyncio.BaseEventLoop=None) -> App:
    app = App(config=config, middlewares=[catch_exceptions_middleware],
              logger=logger, loop=loop)
    app.on_cleanup.append(cleanup)

    db_conf = app.config.get('postgres')
    app._db = await create_pool(
        user=db_conf.get('user'), database=db_conf.get('database'),
        host=db_conf.get('host'), password=db_conf.get('password'),
        port=db_conf.get('port'), min_size=1, max_size=10, loop=loop
    )

    with register_handler(app, '/') as add:
        add('GET', '', index, 'index')

    api.register(app, '/api/', 'api')

    return app


def create_config(config_file: str=None) -> Config:
    app_root = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))

    config = Config({
        'app': {
            'name': 'passport',
            'root': app_root,
            'migrations_root': os.path.join(app_root, 'storage', 'migrations'),
            'templates_root': os.path.join(app_root, 'templates')
        },
        'postgres': {
            'user': 'postgres',
            'password': 'postgres',
            'name': 'postgres',
        }
    })

    if config_file:
        config.update_from_yaml(config_file)

    variables = (
        'app_name', 'app_host', 'app_port'
        'postgres_host', 'postgres_port', 'postgres_name', 'postgres_user',
        'postgres_password',
        'consul_host', 'consul_port',
        'sentry_dsn'
    )
    for variable_name in variables:
        config.update_from_env_var(variable_name)

    schema = config_schema.copy()
    schema['app']['schema']['auth'] = {
        'type': 'dict',
        'schema': {
            'domain': {'required': True, 'type': 'string'},
            'secret_key': {'type': 'string'},
            'token_expire': {'required': True, 'type': 'integer'},
        }
    }

    try:
        config.validate()
    except ValidationError as exc:
        raise ImproperlyConfigured('Config has some errors: %s' % exc.errors)

    return config
