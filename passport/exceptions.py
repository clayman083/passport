class ImproperlyConfigured(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, errors):
        self._errors = errors

    @property
    def errors(self):
        return self._errors


class DatabaseError(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class MultipleResourcesFound(Exception):
    pass
