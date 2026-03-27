from datetime import datetime
from app.config.database import db

class Payment:
    collection = db["payments"]

    @staticmethod
    def create_payment(payment_data):
        amount = float(payment_data.get("amount", 0))
        amount_paid = float(payment_data.get("amount_paid", 0))
        payment_data.update({
            "status": payment_data.get("status", "pending"), # pending, paid, partial, unpaid
            "amount_paid": amount_paid,
            "balance": amount - amount_paid,
            "is_paid": payment_data.get("is_paid", False),
            "type": payment_data.get("type", "rent"), # rent, deposit, other
            "due_date": payment_data.get("due_date"),
            "late_fee": float(payment_data.get("late_fee", 0)),
            "created_at": datetime.utcnow()
        })
        return Payment.collection.insert_one(payment_data)

    @staticmethod
    def get_history(student_id):
        from bson import ObjectId
        str_id = str(student_id)
        obj_id = ObjectId(str_id) if ObjectId.is_valid(str_id) else None
        
        query = [{"student_id": str_id}]
        if obj_id:
            query.append({"student_id": obj_id})
            
        return list(Payment.collection.find({"$or": query}).sort("created_at", -1))

    @staticmethod
    def verify_payment(payment_id):
        return Payment.collection.update_one(
            {"_id": payment_id},
            {"$set": {"status": "paid", "is_paid": True}}
        )

    @staticmethod
    def update_payment_details(payment_id, amount_paid, status):
        payment = Payment.collection.find_one({"_id": payment_id})
        if not payment:
            return None
        
        balance = float(payment.get("amount", 0)) - float(amount_paid)
        is_paid = (balance <= 0) or (status == "paid")
        
        if is_paid:
            status = "paid"
            balance = 0.0

        return Payment.collection.update_one(
            {"_id": payment_id},
            {"$set": {
                "amount_paid": float(amount_paid),
                "balance": balance,
                "status": status,
                "is_paid": is_paid,
                "updated_at": datetime.utcnow()
            }}
        )
