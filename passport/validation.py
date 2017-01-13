from typing import Dict

import cerberus

from .exceptions import ValidationError


class Validator(cerberus.Validator):
    def validate_payload(self, payload: Dict, update: bool=False) -> Dict:
        if not self.validate(payload, update=update):
            raise ValidationError(self.errors)

        return self.document


def to_bool(value):
    if isinstance(value, bool):
        return value
    else:
        return str(value).lower() in ['true', '1', 'yes']
