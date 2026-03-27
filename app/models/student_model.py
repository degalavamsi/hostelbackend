import os
from datetime import datetime
from app.config.database import db

class Student:
    collection = db["students"]

    @staticmethod
    def create_student(user_id, student_data):
        student_data.update({
            "user_id": user_id,
            "room_number": student_data.get("room_number", None),
            "bed_number": student_data.get("bed_number", None),
            "rent_amount": float(student_data.get("rent_amount", 0)),
            "join_date": student_data.get("join_date", datetime.utcnow()),
            "deposit": float(student_data.get("deposit", 0)),
            "deposit_paid_date": student_data.get("deposit_paid_date", None),
            "deposit_refund_status": student_data.get("deposit_refund_status", "not_refunded"), # not_refunded, pending, refunded
            "id_proof_path": student_data.get("id_proof_path", None),
            "photo_path": student_data.get("photo_path", None),
            "status": "pending", # pending, approved, rejected
            "created_at": datetime.utcnow()
        })
        return Student.collection.insert_one(student_data)

    @staticmethod
    def get_by_user_id(user_id):
        from bson import ObjectId
        # Check both ObjectId and string since it might be stored inconsistently
        str_id = str(user_id)
        obj_id = ObjectId(str_id) if ObjectId.is_valid(str_id) else None
        
        query = [{"user_id": str_id}]
        if obj_id:
            query.append({"user_id": obj_id})
            
        return Student.collection.find_one({"$or": query})

    @staticmethod
    def update_status(student_id, status):
        return Student.collection.update_one({"_id": student_id}, {"$set": {"status": status}})

    @staticmethod
    def remove_student(student_id):
        # We don't delete, we deactive the account in user model and update status here
        return Student.collection.update_one({"_id": student_id}, {"$set": {"status": "left"}})
