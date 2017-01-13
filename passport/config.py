import os
import socket
from collections import abc
from typing import Dict

import yaml
from cerberus import Validator

from .exceptions import ValidationError


schema = {
    'app': {
        'type': 'dict',
        'schema': {
            'name': {'required': True, 'type': 'string'},
            'hostname': {'type': 'string'},
            'host': {'type': 'string'},
            'port': {'type': 'integer', 'coerce': int},
            'root': {'required': True, 'type': 'string'},
            'migrations_root': {'required': True, 'type': 'string'},
            'templates_root': {'type': 'string'},
            'secret_key': {'required': True, 'type': 'string'},
            'access_log': {'required': True, 'type': 'string'},
        }
    },
    'postgres': {
        'type': 'dict',
        'schema': {
            'name': {'required': True, 'type': 'string'},
            'host': {'required': True, 'type': 'string'},
            'port': {'required': True, 'type': 'integer', 'coerce': int},
            'user': {'required': True, 'type': 'string'},
            'password': {'required': True, 'type': 'string'}
        }
    },
    'consul': {
        'type': 'dict',
        'schema': {
            'host': {'required': True, 'type': 'string'},
            'port': {'required': True, 'type': 'integer', 'coerce': int}
        }
    },
    'sentry': {
        'type': 'dict',
        'schema': {
            'dsn': {'required': True, 'type': 'string'}
        }
    },
    'logging': {
        'type': 'dict'
    }
}


class Config(abc.MutableMapping):
    def __init__(self, defaults=None):
        access_log = '%a %s %Tf %b "%r" "%{Referrer}i" "%{User-Agent}i"'
        self.__dict__.update(
            app={
                'hostname': socket.gethostname(),
                'access_log': access_log,
                'secret_key': 'secret'
            },
            postgres={
                'host': '127.0.0.1',
                'port': 5432,
            },
            consul={
                'host': '127.0.0.1',
                'port': 8500
            }
        )

        if defaults and isinstance(defaults, dict):
            for key, value in iter(defaults.items()):
                if isinstance(value, (str, int, float)):
                    self[key] = value
                elif isinstance(value, dict):
                    if key in self:
                        if isinstance(self[key], dict):
                            self[key].update(**value)
                    else:
                        self[key] = value

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def validate(self, schema: Dict=schema) -> bool:
        config_validator = Validator(schema=schema)

        valid = config_validator.validate(self.__dict__)
        if not valid:
            raise ValidationError(config_validator.errors)

        self.__dict__.update(**config_validator.document)

    def update_from_env_var(self, variable_name: str) -> None:
        value = os.environ.get(variable_name.upper())
        if value:
            if '_' in variable_name:
                section, key = variable_name.split('_')
                if section in self:
                    if isinstance(self[section], dict):
                        self[section][key] = value
                else:
                    self[section] = {key: value}
            else:
                self[variable_name] = value

    def update_from_yaml(self, filename: str) -> None:
        if not filename.endswith('yml'):
            raise RuntimeError('Config should be in yaml format')

        try:
            with open(filename, 'r') as fp:
                data = fp.read()
                conf = yaml.load(data)
        except IOError as exc:
            exc.strerror = 'Unable to load configuration file `{}`'.format(
                exc.strerror
            )
            raise

        for key, value in iter(conf.items()):
            if isinstance(value, (str, int, float)):
                self[key] = value
            elif isinstance(value, dict):
                if key in self:
                    if isinstance(self[key], dict):
                        self[key].update(**value)
                else:
                    self[key] = value
