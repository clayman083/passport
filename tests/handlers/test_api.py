from typing import Dict

import jwt
import pytest
import ujson

from passport.storage.users import create_user, generate_token


def prepare_request(data, json=False):
    headers = {}
    if json:
        data = ujson.dumps(data)
        headers = {'Content-Type': 'application/json'}

    return {'data': data, 'headers': headers}


@pytest.fixture(scope='function')
def prepare_user():
    async def go(user: Dict, app):
        async with app['db'].acquire() as conn:
            data: Dict = user.copy()
            data.setdefault('is_active', True)
            instance = await create_user(**data, connection=conn)
        return instance
    return go


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_registration_success(aiohttp_client, app, prepare_user, json):
    data = {'email': 'john@testing.com', 'password': 'top-secret'}
    client = await aiohttp_client(app)

    url = app.router.named_resources()['api.registration'].url_for()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 201

    async with app['db'].acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM users')
        assert count == 1


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_registration_failed_without_password(aiohttp_client, app, prepare_user, json):  # noqa: E501
    data = {'email': 'john@testing.com'}
    client = await aiohttp_client(app)

    url = app.router.named_resources()['api.registration'].url_for()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 400


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_registration_failed_already_existed(aiohttp_client, app, prepare_user, json):  # noqa: E501
    data = {'email': 'john@testing.com', 'password': 'top-secret'}
    client = await aiohttp_client(app)

    await prepare_user({
        'email': 'john@testing.com', 'password': 'top-secret'
    }, app)

    url = app.router.named_resources()['api.registration'].url_for()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 400


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_login_success(aiohttp_client, app, prepare_user, json):
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.login'].url_for()

    data = {'email': 'john@testing.com', 'password': 'top-secret'}
    await prepare_user(data, app)

    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 200
    assert 'X-ACCESS-TOKEN' in resp.headers
    assert 'X-REFRESH-TOKEN' in resp.headers


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
@pytest.mark.parametrize('password', ['', 'wrong-password'])
async def test_login_failed(aiohttp_client, app, prepare_user, json, password):
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.login'].url_for()

    email = 'john@testing.com'

    await prepare_user({'email': email, 'password': 'top-secret'}, app)

    payload = {'email': email, 'password': password}
    resp = await client.post(url, **prepare_request(payload, json))
    assert resp.status == 400


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_login_unregistered(aiohttp_client, app, prepare_user, json):
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.login'].url_for()

    payload = {'email': 'peter@missing.com', 'password': 'some-secret'}
    resp = await client.post(url, **prepare_request(payload, json))
    assert resp.status == 404


@pytest.mark.handlers
async def test_refresh_success(aiohttp_client, app, prepare_user):
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.refresh'].url_for()

    user = await prepare_user({
        'email': 'john@testing.com', 'password': 'top-secret'
    }, app)

    refresh_token = generate_token(user['id'], app['config']['secret_key'],
                                   'refresh', expires=3600)

    headers = {'X-REFRESH-TOKEN': refresh_token.decode('utf-8')}
    resp = await client.post(url, headers=headers)
    assert resp.status == 200
    assert 'X-ACCESS-TOKEN' in resp.headers

    access_token = resp.headers['X-ACCESS-TOKEN']
    token = jwt.decode(access_token, app['config']['secret_key'],
                       algorithms='HS256')
    assert token['id'] == user['id']
    assert token['token_type'] == 'access'


@pytest.mark.handler
@pytest.mark.parametrize('token_type', ['', 'wrong', 'access', None])
@pytest.mark.parametrize('user_id', ['', 0, '2', None])
async def test_refresh_failed(aiohttp_client, app, prepare_user, token_type, user_id):  # noqa: E501
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.refresh'].url_for()

    refresh_token = generate_token(user_id, app['config']['secret_key'],
                                   token_type)
    headers = {'X-REFRESH-TOKEN': refresh_token.decode('utf-8')}
    resp = await client.post(url, headers=headers)
    assert resp.status == 401


@pytest.mark.handler
async def test_refresh_failed_for_inactive(aiohttp_client, app, prepare_user):
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.refresh'].url_for()

    user = await prepare_user({
        'email': 'john@testing.com',
        'password': 'top-secret',
        'is_active': False
    }, app)

    refresh_token = generate_token(user['id'], app['config']['secret_key'],
                                   'refresh', expires=3600)

    headers = {'X-REFRESH-TOKEN': refresh_token.decode('utf-8')}
    resp = await client.post(url, headers=headers)
    assert resp.status == 404


@pytest.mark.handlers
async def test_identify_success(aiohttp_client, app, prepare_user):
    client = await aiohttp_client(app)
    url = app.router.named_resources()['api.identify'].url_for()

    data = {'email': 'john@testing.com', 'password': 'top-secret'}

    user = await prepare_user({
        'email': 'john@testing.com', 'password': 'top-secret'
    }, app)

    access_token = generate_token(user['id'], app['config']['secret_key'],
                                  'access', expires=3600)

    headers = {'X-ACCESS-TOKEN': access_token.decode('utf-8')}
    resp = await client.get(url, headers=headers)
    assert resp.status == 200
    result = await resp.json()
    assert result['owner']['email'] == data['email']
