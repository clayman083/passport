from contextlib import contextmanager

from aiohttp import web


@contextmanager
def register_handler(app: web.Application, url_prefix: str=None,
                     name_prefix: str=None):
    def register(method: str, url: str, handler, name: str=None):
        if url_prefix:
            if not url:
                url = url_prefix
            else:
                url = '/'.join((url_prefix.rstrip('/'), url.lstrip('/')))

        if name_prefix:
            name = '.'.join((name_prefix, name))

        app.router.add_route(method, url, handler, name=name)
    yield register
