import pytest


@pytest.mark.handlers
async def test_index(aiohttp_client, app):
    client = await aiohttp_client(app)

    resp = await client.get('/')
    assert resp.status == 200
