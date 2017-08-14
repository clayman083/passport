import functools
from datetime import datetime
from typing import Dict

import jwt
from aiohttp import web

from passport.handlers import get_payload, json_response, register_handler
from passport.storage.users import create_user, generate_token, verify_password
from passport.validation import ValidationError, Validator


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

        await create_user(payload['email'], payload['password'], True, conn)

    return json_response({'email': payload['email']}, status=201)


async def login(request: web.Request) -> web.Response:
    payload = await get_payload(request)

    validator = Validator(schema)
    validator.validate_payload(payload)

    async with request.app.db.acquire() as conn:
        user = await conn.fetchrow('''
            SELECT id, email, password FROM users WHERE (
                users.email = $1 AND is_active = TRUE
            )
        ''', payload['email'])
        if not user:
            raise web.HTTPNotFound(text='User does not found')

        if not verify_password(payload['password'], user['password']):
            raise ValidationError({'password': 'Wrong password'})

        await conn.execute('''
            UPDATE users SET last_login = $1 WHERE id = $2
        ''', datetime.now(), user['id'])

    # Create auth token
    access_token = generate_token(
        user['id'], request.app.config['secret_key'], 'access',
        request.app.config['access_token_expire']
    )

    refresh_token = generate_token(
        user['id'], request.app.config['secret_key'], 'refresh',
        request.app.config['refresh_token_expire']
    )

    headers = {
        'X-ACCESS-TOKEN': access_token.decode('utf-8'),
        'X-REFRESH-TOKEN': refresh_token.decode('utf-8')
    }

    return json_response({'email': user['email']}, headers=headers)


def token_required(token_type, token_name):
    if token_type not in ('access', 'refresh'):
        raise ValueError('Unsupported token type: {token_type}')

    def wrapper(f):
        @functools.wraps(f)
        async def wrapped(request: web.Request):
            token = request.headers.get(token_name, '')

            if not token:
                raise web.HTTPUnauthorized(text='Token required')

            try:
                token_data = jwt.decode(token, request.app.config['secret_key'],
                                        algorithms='HS256')
            except jwt.ExpiredSignatureError:
                raise web.HTTPUnauthorized(text='Token signature expired')
            except jwt.DecodeError:
                raise web.HTTPUnauthorized(text='Bad token')

            if token_data.get('token_type', None) != token_type:
                raise web.HTTPUnauthorized(text='Bad token')

            return await f(token_data, request)
        return wrapped
    return wrapper


@token_required('refresh', 'X-REFRESH-TOKEN')
async def refresh(token: Dict, request: web.Request) -> web.Response:
    async with request.app.db.acquire() as conn:
        user = await conn.fetchrow('''
            SELECT id, email, is_active FROM users WHERE (
                id = $1 AND is_active = TRUE
            )
        ''', token['id'])

        if not user:
            raise web.HTTPNotFound(text='User does not found')

    access_token = generate_token(
        user['id'], request.app.config['secret_key'], 'access',
        request.app.config['access_token_expire']
    )

    headers = {
        'X-ACCESS-TOKEN': access_token.decode('utf-8'),
    }

    return json_response({'email': user['email']}, headers=headers)


@token_required('access', 'X-ACCESS-TOKEN')
async def identify(token: Dict, request: web.Request) -> web.Response:
    async with request.app.db.acquire() as conn:
        user = await conn.fetchrow('''
            SELECT id, email FROM users WHERE (
                id = $1 AND is_active = TRUE
            )
        ''', token['id'])

    return json_response({'owner': {'id': user['id'], 'email': user['email']}})


def register(app: web.Application, url_prefix: str, name_prefix: str=None):
    with register_handler(app, url_prefix, name_prefix) as add:
        add('GET', 'identify', identify, 'identify')
        add('POST', 'register', registration, 'registration')
        add('POST', 'login', login, 'login')
        add('POST', 'refresh', refresh, 'refresh')
