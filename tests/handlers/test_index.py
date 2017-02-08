import pytest


@pytest.mark.handlers
async def test_index(client):
    resp = await client.get('/')
    assert resp.status == 200
