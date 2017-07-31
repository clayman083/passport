import asyncio
import logging
import logging.config

import click
import uvloop

from passport import configure, init
from passport.management.server import server


class Context(object):

    def __init__(self):
        self.conf = configure()
        self.init_app = init

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        self.loop = asyncio.get_event_loop()

        logging.config.dictConfig(self.conf['logging'])

        self.logger = logging.getLogger('app')


@click.group()
@click.pass_context
def cli(context):
    context.obj = Context()


cli.add_command(server, name='server')
