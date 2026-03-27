import os
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, decode_token
from dotenv import load_dotenv

load_dotenv()

class JWTHelper:
    @staticmethod
    def generate_token(identity, roles, expires_in=24):
        expires = timedelta(hours=expires_in)
        additional_claims = {"roles": roles}
        return create_access_token(identity=identity, additional_claims=additional_claims, expires_delta=expires)

    @staticmethod
    def decode_token(token):
        try:
            return decode_token(token)
        except Exception:
            return None
