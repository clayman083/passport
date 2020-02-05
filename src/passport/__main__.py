import asyncio

import click
import uvloop  # type: ignore
from aiohttp_micro.management.server import server  # type: ignore

from passport.app import AppConfig, init


@click.group()
@click.option("--debug", default=False)
@click.pass_context
def cli(ctx, debug):
    uvloop.install()
    loop = asyncio.get_event_loop()

    config = AppConfig()
    config.load_from_env()

    config.debug = debug

    app = loop.run_until_complete(init("passport", config))

    ctx.obj["app"] = app
    ctx.obj["config"] = config
    ctx.obj["loop"] = loop


cli.add_command(server, name="server")


if __name__ == "__main__":
    cli(obj={})
