import functools
from datetime import datetime

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


async def refresh(request: web.Request) -> web.Response:
    token = request.headers.get('X-REFRESH-TOKEN', None)

    if not token:
        raise web.HTTPUnauthorized(text='Refresh token required')

    try:
        data = jwt.decode(token, request.app.config.get('secret_key'),
                          algorithms='HS256')
    except jwt.ExpiredSignatureError:
        raise web.HTTPUnauthorized(text='Token expired')
    except jwt.DecodeError:
        raise web.HTTPUnauthorized(text='Bad token')

    if data['token_type'] != 'refresh':
        raise web.HTTPUnauthorized(text='Bad token')

    async with request.app.db.acquire() as conn:
        user = await conn.fetchrow('''
            SELECT id, email, is_active FROM users WHERE users.id = '{0}'
        '''.format(data.get('id')))

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


def owner_required(f):
    @functools.wraps(f)
    async def wrapped(request: web.Request):
        token = request.headers.get('X-ACCESS-TOKEN', None) or \
                request.cookies.get('access_token', None)

        if not token:
            raise web.HTTPUnauthorized(text='Access token required')

        try:
            data = jwt.decode(token, request.app.config['secret_key'],
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
    return json_response({
        'owner': {
            'id': owner['id'],
            'email': owner['email']
        }
    })


async def change_password(request: web.Request) -> web.Response:
    pass


def register(app: web.Application, url_prefix: str, name_prefix: str=None):
    with register_handler(app, url_prefix, name_prefix) as add:
        add('GET', 'identify', identify, 'identify')
        add('POST', 'register', registration, 'registration')
        add('POST', 'login', login, 'login')
        add('POST', 'refresh', refresh, 'refresh')
        add('POST', 'change_password', change_password, 'change_password')
