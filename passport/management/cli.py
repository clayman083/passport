import asyncio
import logging
import logging.config

import click
import uvloop

from .. import create_config, init
from ..management.server import server


class Context(object):
    def __init__(self, config: str):
        self.conf = create_config(config)
        self.init_app = init

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = asyncio.get_event_loop()

        logging.config.dictConfig(self.conf['logging'])

        self.logger = logging.getLogger('passport')


@click.group()
@click.option('-c', '--config', default='config.yml')
@click.pass_context
def cli(context, config: str):
    context.obj = Context(config)


cli.add_command(server, name='server')
