from datetime import timedelta
import jwt
import pytest
from luco.auth import create_access_token, create_refresh_token, decode_token, hash_password, verify_password


def test_password_hashing():
    pwd = "RahasiaUntan2026!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("SalahPassword", hashed)


def test_jwt_tokens():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    email = "mahasiswa@untan.ac.id"
    access_tok = create_access_token(user_id, email, expires_delta=timedelta(minutes=15))
    payload = decode_token(access_tok)
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["type"] == "access"

    refresh_tok = create_refresh_token(user_id, expires_delta=timedelta(days=1))
    payload_ref = decode_token(refresh_tok)
    assert payload_ref["sub"] == user_id
    assert payload_ref["type"] == "refresh"


def test_invalid_token():
    with pytest.raises(jwt.PyJWTError):
        decode_token("token.palsu.ngawur")

