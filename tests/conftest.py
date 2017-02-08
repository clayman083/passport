import logging
import os

import pytest

from alembic import command
from alembic.config import Config as AlembicConfig

from passport import create_config, init


@pytest.fixture(scope='session')
def config():
    conf = create_config()

    conf['app']['auth'] = {
        'domain': 'clayman.pro',
        'secret_key': 'secret',
        'token_expire': 3600
    }

    return conf


@pytest.yield_fixture(scope='function')
def client(loop, test_client, pg_server, config):
    logger = logging.getLogger('passport')

    config['postgres']['host'] = pg_server['pg_params']['host']
    config['postgres']['port'] = pg_server['pg_params']['port']

    app = loop.run_until_complete(init(config, logger, loop=loop))

    conf = pg_server['pg_params']
    directory = config['app'].get('migrations_root')
    print(directory)
    db_uri = 'postgres://%s:%s@%s:%s/%s' % (
        conf.get('user'), conf.get('password'), conf.get('host'),
        conf.get('port'), conf.get('database')
    )

    conf = AlembicConfig(os.path.join(directory, 'alembic.ini'))
    conf.set_main_option('script_location', directory)
    conf.set_main_option('sqlalchemy.url', db_uri)

    command.upgrade(conf, revision='head')

    yield loop.run_until_complete(test_client(app))

    command.downgrade(conf, revision='base')

    loop.run_until_complete(app.cleanup())
