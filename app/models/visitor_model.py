from datetime import datetime
from app.config.database import db
from bson import ObjectId

class Visitor:
    collection = db["visitors"]

    @staticmethod
    def log_entry(data):
        """Admin-direct entry log."""
        data.update({
            "time_in": datetime.utcnow(),
            "time_out": None,
            "status": "approved",
            "type": "admin_log",
            "created_at": datetime.utcnow()
        })
        return Visitor.collection.insert_one(data)

    @staticmethod
    def request_visitor(user_id, data):
        """Student submits a visitor pre-request."""
        data.update({
            "submitted_by": ObjectId(user_id),
            "status": "pending",
            "type": "student_request",
            "time_in": None,
            "time_out": None,
            "created_at": datetime.utcnow()
        })
        return Visitor.collection.insert_one(data)

    @staticmethod
    def approve(visitor_id, status):
        """Admin approves or denies a student visitor request."""
        update = {"status": status}
        if status == "approved":
            update["time_in"] = datetime.utcnow()
        return Visitor.collection.update_one(
            {"_id": ObjectId(visitor_id)},
            {"$set": update}
        )

    @staticmethod
    def log_exit(visitor_id):
        return Visitor.collection.update_one(
            {"_id": visitor_id},
            {"$set": {"time_out": datetime.utcnow()}}
        )

    @staticmethod
    def get_all():
        return list(Visitor.collection.find().sort("created_at", -1))

    @staticmethod
    def get_by_student(user_id):
        """Get all visitor requests submitted by a specific student."""
        return list(Visitor.collection.find({"submitted_by": ObjectId(user_id)}).sort("created_at", -1))

    @staticmethod
    def get_pending_requests():
        """Get all pending student visitor requests."""
        return list(Visitor.collection.find({"type": "student_request", "status": "pending"}).sort("created_at", -1))
