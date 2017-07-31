from datetime import datetime, timedelta

import jwt
from passlib.handlers.pbkdf2 import pbkdf2_sha512


def encrypt_password(password: str) -> str:
    return pbkdf2_sha512.encrypt(password, rounds=10000, salt_size=10)


def verify_password(password: str, encrypted_password: str) -> bool:
    try:
        valid = pbkdf2_sha512.verify(password, encrypted_password)
    except ValueError:
        valid = False
    return valid


def generate_token(owner: int, secret_key: str, token_type: str='access',
                   expires: int=900, algorithm: str='HS256') -> bytes:

    token = jwt.encode({
        'id': owner,
        'token_type': token_type,
        'exp': datetime.now() + timedelta(seconds=expires)
    }, secret_key, algorithm=algorithm)

    return token


async def create_user(email, password, is_active, connection):
    user = {'email': email, 'password': password}

    query = """
      INSERT INTO users (email, password, is_active, created_on)
        VALUES ('{0}', '{1}', '{2}', '{3}')
      RETURNING id
    """.format(email, encrypt_password(password), is_active, datetime.now())
    user['id'] = await connection.fetchval(query)

    return user
