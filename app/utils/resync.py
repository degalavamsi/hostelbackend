import os
from pprint import pprint
from app.config.database import db

def resync():
    rooms = db.rooms.find()
    for room in rooms:
        # find how many students have this room
        # count it
        cnt = db.students.count_documents({"room_number": room["room_number"], "status": "approved"})
        db.rooms.update_one({"_id": room["_id"]}, {"$set": {"occupied_beds": cnt, "available_beds": room["capacity"] - cnt}})
        print(f"Room {room['room_number']} occupational beds set to {cnt}")

        # ensure bed entities exist for these students
        students_in_room = db.students.find({"room_number": room["room_number"], "status": "approved"})
        for st in students_in_room:
            # check if bed exists
            bed = db.beds.find_one({"room_id": room["_id"], "bed_number": st.get("bed_number")})
            if not bed:
                db.beds.insert_one({
                    "room_id": room["_id"],
                    "bed_number": st.get("bed_number"),
                    "student_id": st["_id"],
                    "status": "occupied"
                })
                print(f"Assigned missing bed {st.get('bed_number')} for {st.get('username')}")

if __name__ == "__main__":
    resync()
