from datetime import datetime
from app.config.database import db
from bson import ObjectId

class Notification:
    collection = db["notifications"]

    @staticmethod
    def create(recipient_id, n_type, message, extra=None):
        """
        Types: rent_due, menu_update, notice, maintenance, approval, payment_reminder
        extra: dict with optional keys like upi_id, qr_url
        """
        notification = {
            "recipient_id": ObjectId(recipient_id),
            "type": n_type,
            "message": message,
            "is_read": False,
            "response": None,
            "created_at": datetime.utcnow()
        }
        if extra:
            notification.update(extra)
        return Notification.collection.insert_one(notification)

    @staticmethod
    def get_by_user(user_id):
        return list(Notification.collection.find({"recipient_id": ObjectId(user_id)}).sort("created_at", -1))

    @staticmethod
    def mark_as_read(notification_id):
        return Notification.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True}}
        )

    @staticmethod
    def delete(notification_id, user_id):
        """Delete a notification only if it belongs to the requesting user."""
        return Notification.collection.delete_one({
            "_id": ObjectId(notification_id),
            "recipient_id": ObjectId(user_id)
        })

    @staticmethod
    def respond(notification_id, user_id, response_text):
        """Student adds a response text to a notification."""
        return Notification.collection.update_one(
            {"_id": ObjectId(notification_id), "recipient_id": ObjectId(user_id)},
            {"$set": {"response": response_text, "is_read": True, "responded_at": datetime.utcnow()}}
        )

    @staticmethod
    def get_unread_count(user_id):
        return Notification.collection.count_documents({"recipient_id": ObjectId(user_id), "is_read": False})
