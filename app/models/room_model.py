from app.config.database import db

class Room:
    collection = db["rooms"]

    @staticmethod
    def create_room(room_data):
        room_data.update({
            "occupied_beds": 0,
            "available_beds": room_data["capacity"]
        })
        return Room.collection.insert_one(room_data)

    @staticmethod
    def get_all():
        return list(Room.collection.find())

    @staticmethod
    def find_by_floor(floor):
        return list(Room.collection.find({"floor": floor}))

    @staticmethod
    def update_occupancy(room_id, change):
        return Room.collection.update_one(
            {"_id": room_id},
            {"$inc": {"occupied_beds": change, "available_beds": -change}}
        )

class Bed:
    collection = db["beds"]

    @staticmethod
    def assign_bed(room_id, bed_number, student_id):
        bed_data = {
            "room_id": room_id,
            "bed_number": bed_number,
            "student_id": student_id,
            "status": "occupied" # available, occupied, reserved
        }
        return Bed.collection.insert_one(bed_data)

    @staticmethod
    def get_by_room(room_id):
        return list(Bed.collection.find({"room_id": room_id}))
