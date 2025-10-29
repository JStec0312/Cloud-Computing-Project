from jose import jwt, JWTError, ExpiredSignatureError
from src.config.app_config import settings
from uuid import UUID, uuid4
from src.common.utils.time_utils import timedelta_minutes, timedelta_days, utcnow

jwt_secret = settings.jwt_secret
jwt_algorithm = settings.jwt_algorithm
jwt_expiration_minutes = settings.jwt_expiration_minutes
jwt_refresh_expiration_days = settings.jwt_refresh_expiration_days


def create_access_token(user_id: UUID):
    payload = {}
    payload['sub'] = str(user_id)
    payload['exp'] = str(timedelta_days(jwt_refresh_expiration_days))
    payload['jti'] = str(uuid4())
    payload['iat'] = int(utcnow().timestamp())
    #payload['refresh'] = refresh

    token = jwt.encode(
        payload,
        jwt_secret,
        algorithm=jwt_algorithm,
    )
    return token

def create_refresh_token(user_id: UUID):
    payload = {}
    payload['sub'] = str(user_id)
    payload['exp'] = str(timedelta_days(jwt_refresh_expiration_days))
    payload['jti'] = str(uuid4())
    payload['iat'] = int(utcnow().timestamp())
    #payload['refresh'] = True

    token = jwt.encode(
        payload,
        jwt_secret,
        algorithm=jwt_algorithm,
    )
    return token

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        return payload
    except ExpiredSignatureError as e:
        return None
    except JWTError as e:
        return None