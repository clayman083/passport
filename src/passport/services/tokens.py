from datetime import datetime, timedelta

import jwt

from passport.entities import TokenType, User
from passport.exceptions import BadToken, TokenExpired


class TokenService:
    def generate_token(
        self, user: User, token_type: TokenType, private_key: str, expire: int
    ) -> str:
        now = datetime.utcnow()

        return jwt.encode(
            {
                "id": user.key,
                "email": user.email,
                "token_type": token_type.value,
                "iss": "urn:passport",
                "exp": now + timedelta(seconds=expire),
                "iat": now,
            },
            private_key,
            algorithm="RS256",
        )

    def decode_token(
        self, token: str, token_type: TokenType, public_key: str
    ) -> User:
        try:
            token_data = jwt.decode(
                token, public_key, issuer="urn:passport", algorithms="RS256"
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpired()
        except jwt.DecodeError:
            raise BadToken()

        if token_data.get("token_type", None) != token_type:
            raise BadToken()

        return User(key=token_data["id"], email=token_data["email"])
