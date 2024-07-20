import jwt

from app.schemas.login import JWTPayload
from app.settings.base_config import base_settings


def create_access_token(*, data: JWTPayload):
    payload = data.model_dump().copy()
    encoded_jwt = jwt.encode(payload, base_settings.SECRET_KEY, algorithm=base_settings.JWT_ALGORITHM)
    return encoded_jwt
