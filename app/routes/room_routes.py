from flask import Blueprint, request, jsonify
from app.models.room_model import Room, Bed
from app.utils.middleware import role_required, handle_errors
from bson import ObjectId

room_bp = Blueprint("room", __name__)

@room_bp.route("/", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def create_room():
    data = request.get_json()
    Room.create_room(data)
    return jsonify({"msg": "Room created successfully"}), 201

@room_bp.route("/", methods=["GET"])
@handle_errors
def get_rooms():
    rooms = Room.get_all()
    for r in rooms:
        r["_id"] = str(r["_id"])
    return jsonify(rooms), 200

@room_bp.route("/assign-bed", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def assign_bed():
    data = request.get_json()
    room_id = ObjectId(data.get("room_id"))
    bed_number = data.get("bed_number")
    student_id = ObjectId(data.get("student_id"))
    
    # Check room capacity
    room = Room.collection.find_one({"_id": room_id})
    if room["available_beds"] <= 0:
        return jsonify({"msg": "No beds available in this room"}), 400
        
    Bed.assign_bed(room_id, bed_number, student_id)
    Room.update_occupancy(room_id, 1)
    
    return jsonify({"msg": "Bed assigned successfully"}), 200

@room_bp.route("/analytics/occupancy", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_occupancy_analytics():
    pipeline = [
        {"$group": {
            "_id": None,
            "total_capacity": {"$sum": "$capacity"},
            "total_occupied": {"$sum": "$occupied_beds"},
            "total_available": {"$sum": "$available_beds"}
        }}
    ]
    analytics = list(Room.collection.aggregate(pipeline))
    return jsonify(analytics[0] if analytics else {}), 200

@room_bp.route("/<room_id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def update_room(room_id):
    data = request.get_json()
    room = Room.collection.find_one({"_id": ObjectId(room_id)})
    if not room:
        return jsonify({"msg": "Room not found"}), 404
        
    new_capacity = int(data.get("capacity", room["capacity"]))
    occupied = room.get("occupied_beds", 0)
    
    if new_capacity < occupied:
        return jsonify({"msg": f"Cannot reduce capacity below currently occupied beds ({occupied})"}), 400
        
    update_data = {
        "room_number": data.get("number", room.get("room_number")),
        "floor": int(data.get("floor", room.get("floor"))),
        "capacity": new_capacity,
        "room_type": data.get("type", room.get("room_type")),
        "ac": data.get("ac", room.get("ac")),
        "available_beds": new_capacity - occupied
    }
    
    Room.collection.update_one({"_id": ObjectId(room_id)}, {"$set": update_data})
    return jsonify({"msg": "Room updated successfully"}), 200

@room_bp.route("/<room_id>", methods=["DELETE"])
@role_required(["admin", "manager"])
@handle_errors
def delete_room(room_id):
    room = Room.collection.find_one({"_id": ObjectId(room_id)})
    if not room:
        return jsonify({"msg": "Room not found"}), 404
    if room.get("occupied_beds", 0) > 0:
        return jsonify({"msg": "Cannot delete room with assigned students"}), 400
        
    Room.collection.delete_one({"_id": ObjectId(room_id)})
    # Clean up empty beds
    Bed.collection.delete_many({"room_id": ObjectId(room_id)})
    
    return jsonify({"msg": "Room deleted successfully"}), 200

@room_bp.route("/<room_id>/beds", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_room_beds(room_id):
    beds = list(Bed.collection.find({"room_id": ObjectId(room_id)}))
    from app.models.user_model import User
    
    for b in beds:
        b["_id"] = str(b["_id"])
        b["room_id"] = str(b["room_id"])
        b["student_id"] = str(b["student_id"])
        
        # Fetch the student username directly from exactly where it lives
        # A student record might have user_id pointing to User collection
        from app.models.student_model import Student
        student = Student.get_by_user_id(b["student_id"])
        if student:
            user = User.collection.find_one({"_id": student["user_id"]})
            b["student_name"] = user.get("username", "Unknown") if user else "Unknown"
        else:
            # Fallback if student_id in Bed points directly to User (it shouldn't, but just in case)
            user = User.collection.find_one({"_id": ObjectId(b["student_id"])})
            b["student_name"] = user.get("username", "Unknown") if user else "Unknown"
            
    return jsonify(beds), 200

@room_bp.route("/<room_id>/beds/<bed_id>", methods=["DELETE"])
@role_required(["admin", "manager"])
@handle_errors
def remove_bed_assignment(room_id, bed_id):
    bed = Bed.collection.find_one({"_id": ObjectId(bed_id)})
    if not bed:
        return jsonify({"msg": "Bed assignment not found"}), 404
        
    # Find the matching student and clear their room logic
    from app.models.student_model import Student
    # student_id could be pointing to User collection depending on how memory was mapped, let's look up all ways:
    Student.collection.update_many(
        {"user_id": bed["student_id"]},
        {"$set": {"room_number": None, "bed_number": None}}
    )
    
    Bed.collection.delete_one({"_id": ObjectId(bed_id)})
    Room.update_occupancy(ObjectId(room_id), -1)
    
    return jsonify({"msg": "Student unassigned from bed successfully"}), 200
