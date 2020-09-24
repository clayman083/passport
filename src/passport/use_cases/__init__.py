from aiohttp import web


class UseCase:
    def __init__(self, app: web.Application) -> None:
        self.app = app
