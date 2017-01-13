import functools
from datetime import datetime, timedelta

import jwt
import ujson
from aiohttp import web

from ..exceptions import ValidationError
from ..utils import encrypt_password, verify_password, register_handler
from ..validation import Validator
from . import get_payload


schema = {
    'id': {'type': 'integer'},
    'email': {'type': 'string', 'required': True, 'empty': False},
    'password': {'type': 'string', 'required': True, 'empty': False}
}


async def registration(request: web.Request) -> web.Response:
    payload = await get_payload(request)

    validator = Validator(schema)
    validator.validate_payload(payload)

    async with request.app.db.acquire() as conn:
        query = '''
          SELECT COUNT(id) FROM users WHERE users.email = '{0}'
        '''.format(payload['email'])
        count = await conn.fetchval(query)
        if count:
            raise ValidationError({'email': 'Already used'})

        query = '''
          INSERT INTO users (email, password, created_on)
            VALUES ('{0}', '{1}', '{2}')
        '''.format(payload['email'], encrypt_password(payload['password']),
                   datetime.now())
        await conn.execute(query)

    return web.json_response({
        'email': payload['email'],
    }, dumps=ujson.dumps, status=201)


async def login(request: web.Request) -> web.Response:
    payload = await get_payload(request)

    validator = Validator(schema)
    validator.validate_payload(payload)

    async with request.app.db.acquire() as conn:
        user = await conn.fetchrow('''
            SELECT id, email, password FROM users WHERE users.email = '{0}'
        '''.format(payload['email']))
        if not user:
            raise web.HTTPNotFound(text='User does not found')

        if not verify_password(payload['password'], user['password']):
            raise ValidationError({'password': 'Wrong password'})

        await conn.execute('''
            UPDATE users SET last_login = '{0}' WHERE id = {1}
        '''.format(datetime.now(), user['id']))

    # Create auth token
    app_config = request.app.config.get('app')
    auth_config = app_config.get('auth')
    access_token = jwt.encode({
        'id': user['id'],
        'exp': datetime.now() + timedelta(seconds=auth_config['token_expire'])
    }, auth_config.get('secret_key'), algorithm='HS256')

    headers = {'X-ACCESS-TOKEN': access_token.decode('utf-8')}
    redirect_to = request.rel_url.query.get('next', None)
    status = 200
    if redirect_to:
        status = 301
        headers['Location'] = redirect_to

    response = web.json_response({'email': user['email']}, dumps=ujson.dumps,
                                 status=status, headers=headers)
    response.set_cookie('access_token', access_token.decode('utf-8'),
                        httponly=True, domain=auth_config.get('domain'))
    return response


def owner_required(f):
    @functools.wraps(f)
    async def wrapped(request: web.Request):
        token = request.headers.get('X-ACCESS-TOKEN', None) or \
                request.cookies.get('access_token', None)

        if not token:
            raise web.HTTPUnauthorized(text='Access token required')

        app_config = request.app.config.get('app', {})
        auth_config = app_config.get('auth', {})

        try:
            data = jwt.decode(token, auth_config.get('secret_key'),
                              algorithms='HS256')
        except jwt.ExpiredSignatureError:
            raise web.HTTPUnauthorized(text='Token signature expired')
        except jwt.DecodeError:
            raise web.HTTPUnauthorized(text='Bad access token')

        async with request.app.db.acquire() as conn:
            user = await conn.fetchrow('''
                SELECT id, email FROM users WHERE users.id = '{0}'
            '''.format(data.get('id')))

        return await f(user, request)
    return wrapped


@owner_required
async def identify(owner, request: web.Request) -> web.Response:
    return web.json_response({
        'owner': {
            'id': owner['id'],
            'email': owner['email']
        }
    }, dumps=ujson.dumps, status=200)


async def change_password(request: web.Request) -> web.Response:
    pass


def register(app: web.Application, url_prefix: str, name_prefix: str=None):
    with register_handler(app, url_prefix, name_prefix) as add:
        add('GET', 'identify', identify, 'identify')
        add('POST', 'register', registration, 'registration')
        add('POST', 'login', login, 'login')
        add('POST', 'change_password', change_password, 'change_password')
