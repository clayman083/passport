class BadToken(Exception):
    pass


class TokenExpired(Exception):
    pass


class InvalidPayload(Exception):
    def __init__(self, errors):
        self._errors = errors

    @property
    def errors(self):
        return self._errors
