async def test_metrics(aiohttp_client, app):
    client = await aiohttp_client(app)

    url = app.router.named_resources()['metrics'].url_for()
    resp = await client.get(url)
    assert resp.status == 200
