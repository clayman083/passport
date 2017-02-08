from datetime import datetime

import pytest
import ujson

from passport import App
from passport.storage.users import create_user


def prepare_request(data, json=False):
    headers = {}
    if json:
        data = ujson.dumps(data)
        headers = {'Content-Type': 'application/json'}

    return {'data': data, 'headers': headers}


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_registration_success(client, json):
    data = {'email': 'john@testing.com', 'password': 'top-secret'}
    app: App = client.server.app

    url = app.router.named_resources()['api.registration'].url()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 201

    async with app.db.acquire() as conn:
        count = await conn.fetchval('SELECT COUNT(*) FROM users')
        assert count == 1


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_registration_failed_without_password(client, json):
    data = {'email': 'john@testing.com'}
    app: App = client.server.app

    url = app.router.named_resources()['api.registration'].url()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 400


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_registration_failed_when_already_existed(client, json):
    data = {'email': 'john@testing.com', 'password': 'top-secret'}
    app: App = client.server.app

    async with app.db.acquire() as conn:
        await create_user(data['email'], data['password'], connection=conn)

    url = app.router.named_resources()['api.registration'].url()
    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 400


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_login_success(client, json):
    app: App = client.server.app
    url = app.router.named_resources()['api.login'].url()

    data = {'email': 'john@testing.com', 'password': 'top-secret'}

    async with app.db.acquire() as conn:
        await create_user(data['email'], data['password'], connection=conn)

    resp = await client.post(url, **prepare_request(data, json))
    assert resp.status == 200
    assert 'X-ACCESS-TOKEN' in resp.headers


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
@pytest.mark.parametrize('password', ['', 'wrong-password'])
async def test_login_failed(client, json, password):
    app: App = client.server.app
    url = app.router.named_resources()['api.login'].url()

    email = 'john@testing.com'

    async with app.db.acquire() as conn:
        await create_user(email, 'top-secret', connection=conn)

    payload = {'email': email, 'password': password}
    resp = await client.post(url, **prepare_request(payload, json))
    assert resp.status == 400


@pytest.mark.handlers
@pytest.mark.parametrize('json', [True, False])
async def test_login_unregistered(client, json):
    app: App = client.server.app
    url = app.router.named_resources()['api.login'].url()

    payload = {'email': 'peter@missing.com', 'password': 'some-secret'}
    resp = await client.post(url, **prepare_request(payload, json))
    assert resp.status == 404


@pytest.mark.handlers
async def test_identify_success(client):
    app: App = client.server.app
    url = app.router.named_resources()['api.login'].url()

    data = {'email': 'john@testing.com', 'password': 'top-secret'}

    async with app.db.acquire() as conn:
        await create_user(data['email'], data['password'], connection=conn)

    resp = await client.post(url, data=data)
    assert resp.status == 200
    assert 'X-ACCESS-TOKEN' in resp.headers

    url = app.router.named_resources()['api.identify'].url()
    headers = {'X-ACCESS-TOKEN': resp.headers['X-ACCESS-TOKEN']}
    resp = await client.get(url, headers=headers)
    assert resp.status == 200
    result = await resp.json()
    assert result['owner']['email'] == data['email']
