from datetime import datetime
from app.config.database import db


class FoodMenu:
    collection = db["food_menu"]

    @staticmethod
    def update_menu(day, menu_data):
        return FoodMenu.collection.update_one(
            {"day": day},
            {"$set": {"menu": menu_data}},
            upsert=True
        )

    @staticmethod
    def get_all():
        return list(FoodMenu.collection.find())

class Notice:
    collection = db["notices"]

    @staticmethod
    def create_notice(title, content, priority):
        return Notice.collection.insert_one({
            "title": title,
            "content": content,
            "priority": priority, # urgent, normal
            "created_at": datetime.utcnow()
        })

    @staticmethod
    def get_active():
        return list(Notice.collection.find().sort("created_at", -1))

    @staticmethod
    def delete_notice(notice_id):
        return Notice.collection.delete_one({"_id": notice_id})


class Complaint:
    collection = db["complaints"]

    @staticmethod
    def create(user_id, title, content, category="general"):
        now = datetime.utcnow()
        day = now.strftime("%A")
        return Complaint.collection.insert_one({
            "user_id": user_id,
            "title": title,
            "content": content,
            "category": category,      # general, maintenance, food, other
            "status": "open",          # open, in_progress, resolved
            "day": day,
            "created_at": now
        })

    @staticmethod
    def get_all():
        return list(Complaint.collection.find().sort("created_at", -1))

    @staticmethod
    def get_by_user(user_id):
        return list(Complaint.collection.find({"user_id": user_id}).sort("created_at", -1))

    @staticmethod
    def update_status(complaint_id, status):
        return Complaint.collection.update_one(
            {"_id": complaint_id},
            {"$set": {"status": status}}
        )
