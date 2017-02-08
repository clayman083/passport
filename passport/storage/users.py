from datetime import datetime

from passlib.handlers.pbkdf2 import pbkdf2_sha512


def encrypt_password(password: str) -> str:
    return pbkdf2_sha512.encrypt(password, rounds=10000, salt_size=10)


def verify_password(password: str, encrypted_password: str) -> bool:
    try:
        valid = pbkdf2_sha512.verify(password, encrypted_password)
    except ValueError:
        valid = False
    return valid


async def create_user(email, password, connection):
    query = '''
      INSERT INTO users (email, password, created_on)
        VALUES ('{0}', '{1}', '{2}')
    '''.format(email, encrypt_password(password), datetime.now())
    await connection.execute(query)
