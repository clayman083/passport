from contextlib import contextmanager

from aiohttp import web
from passlib.handlers.pbkdf2 import pbkdf2_sha512


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


def encrypt_password(password: str) -> str:
    return pbkdf2_sha512.encrypt(password, rounds=10000, salt_size=10)


def verify_password(password: str, encrypted_password: str) -> bool:
    try:
        valid = pbkdf2_sha512.verify(password, encrypted_password)
    except ValueError:
        valid = False
    return valid
