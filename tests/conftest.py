import faker
import pytest  # type: ignore
from aiohttp import web
from aiohttp_storage.tests import storage

from passport.app import AppConfig, init


@pytest.fixture(scope="session")
def config():
    conf = AppConfig()

    conf.tokens.public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQDBqkP6h/7LMOAaWuVAqjPcrOdUCiMhyykbMaDji8odBKtCam1MyBxq1I87LFiAbHx7r5biBMUC/nyTzPiYF5II+g4MDLgV5S8/6uTmtCL40FsuIOClFPqbAiitvRFYDuBTJx3w1Fr4zWWIVtaUFqer5nAsnr4sovOG+zRVtfXJ8w=="  # noqa
    conf.tokens.private_key = """
-----BEGIN RSA PRIVATE KEY-----
MIICXgIBAAKBgQDBqkP6h/7LMOAaWuVAqjPcrOdUCiMhyykbMaDji8odBKtCam1M
yBxq1I87LFiAbHx7r5biBMUC/nyTzPiYF5II+g4MDLgV5S8/6uTmtCL40FsuIOCl
FPqbAiitvRFYDuBTJx3w1Fr4zWWIVtaUFqer5nAsnr4sovOG+zRVtfXJ8wIDAQAB
AoGBAKiSIQuwVmrdByRJnCU2QWBDLDQtgrkGkqg2AZou8mVhzARKiQr9YCbpECds
iTh3tb8fbtEbX7UkeKFaF8SjN5uPCIX6MVoQDoH8VTmsj6lFIXpeCjfqEXEFdE/p
AAJVGZBxN0VNmpVYpp1XhGQE4iI7WBUZtJ7stP0WcjkXkzsRAkEA4h9aGY7bbHru
lX7PgguP+FMMcOSc+Ax7oQuBZ0x0zXO1YVE1vl4KHeDSuATI6bT4LYGJFa3soUnF
PMFi6MacGwJBANtBCP1h7LdOFWRtVpOCNCjNYGeuRzxJ3APiolnMpTsUQ8qDWa+M
UrcO0WhUy7Z+swicEDuKO0CoOjkOQFhZtwkCQQCTFFmCrk1DLmLpkmZe7C5lE3/Q
HqOLJHN1uQoeqrh+uniMKEqQ3JIwBQCK+XHFshSLZOpJ06tK7bUBY7h2OFlpAkBK
EOcziXAI4ETTvyfe/r4WBoMJo1MHJ8A+Q8IqabprgcYA1GxopBORKV1OTE7g4F4k
i2vkYSbxCaNZgNn1vqDZAkEAvBFt/ERW1UnV6fwOTa9x6yxNVNpd3tKRD4li+u0x
oAvGVHdn+B1JJBkTJccu9hOAWjyXX5C2QuuC/fNKmsqxyQ==
-----END RSA PRIVATE KEY-----
    """

    return conf


@pytest.yield_fixture(scope="function")
def app(loop, pg_server, config):
    config.db.host = pg_server["params"]["host"]
    config.db.port = pg_server["params"]["port"]
    config.db.user = pg_server["params"]["user"]
    config.db.password = pg_server["params"]["password"]
    config.db.database = pg_server["params"]["database"]

    app = loop.run_until_complete(init("passport", config))

    with storage(config=app["config"].db, root=app["storage_root"]):
        yield app


@pytest.yield_fixture(scope="function")
def prepared_app(loop, app):
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())

    yield app

    loop.run_until_complete(runner.cleanup())


@pytest.fixture(scope="function")
async def client(app, aiohttp_client):
    client = await aiohttp_client(app)

    return client


@pytest.fixture(scope="session")
def fake():
    return faker.Faker()
