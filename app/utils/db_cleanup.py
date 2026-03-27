import os
from datetime import datetime
from bson import ObjectId
from app.config.database import db

def fix_vamsi():
    user = db.users.find_one({"username": "vamsi"})
    if user:
        print("Found user:", user["_id"])
        res = db.students.update_one({"username": "vamsi"}, {"$set": {"user_id": user["_id"]}})
        print("Updated students for vamsi:", res.modified_count)
    else:
        print("User vamsi not found")

if __name__ == "__main__":
    fix_vamsi()
