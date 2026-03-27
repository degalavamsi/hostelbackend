from werkzeug.security import generate_password_hash, check_password_hash
from app.config.database import db

class User:
    collection = db["users"]

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def create_user(username, email, password, roles, phone=None, is_active=True):
        hashed_password = User.hash_password(password)
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "phone": phone,
            "roles": roles, # ['admin', 'manager', 'student']
            "is_active": is_active
        }
        return User.collection.insert_one(user_data)

    @staticmethod
    def activate_user(user_id):
        return User.collection.update_one({"_id": user_id}, {"$set": {"is_active": True}})

    @staticmethod
    def find_by_email(email):
        return User.collection.find_one({"email": email})

    @staticmethod
    def verify_password(password, hashed_password):
        return check_password_hash(hashed_password, password)

    @staticmethod
    def deactivate_user(user_id):
        return User.collection.update_one({"_id": user_id}, {"$set": {"is_active": False}})
