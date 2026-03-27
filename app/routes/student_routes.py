from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.student_model import Student
from app.models.user_model import User
from app.models.notification_model import Notification
from app.utils.middleware import role_required, handle_errors
from bson import ObjectId
from datetime import datetime
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint("student", __name__)

UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_bp.route("/register-details", methods=["POST"])
@jwt_required()
@handle_errors
def register_details():
    user_id = get_jwt_identity()
    
    # Check if student profile already exists
    if Student.get_by_user_id(user_id):
        return jsonify({"msg": "Profile already exists"}), 400

    # Handle file uploads
    if 'id_document' not in request.files or 'photo' not in request.files:
        return jsonify({"msg": "ID document and photo are required"}), 400
    
    id_doc = request.files['id_document']
    photo = request.files['photo']
    
    if id_doc.filename == '' or photo.filename == '':
        return jsonify({"msg": "No selected file"}), 400
        
    if id_doc and allowed_file(id_doc.filename) and photo and allowed_file(photo.filename):
        id_filename = secure_filename(f"{user_id}_id_{id_doc.filename}")
        photo_filename = secure_filename(f"{user_id}_photo_{photo.filename}")
        
        id_doc.save(os.path.join(UPLOAD_FOLDER, id_filename))
        photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))
        
        student_data = {
            "phone": request.form.get("phone"),
            "emergency_contact": request.form.get("emergency_contact"),
            "id_document_path": id_filename,
            "photo_path": photo_filename,
        }
        
        Student.create_student(user_id, student_data)
        return jsonify({"msg": "Student details submitted for approval"}), 201
    
    return jsonify({"msg": "Invalid file types"}), 400

@student_bp.route("/approve/<student_id>", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def approve_student(student_id):
    student = Student.collection.find_one({"_id": ObjectId(student_id)})
    if not student:
        return jsonify({"msg": "Student record not found"}), 404
        
    # Update student status to approved
    Student.update_status(ObjectId(student_id), "approved")
    # Activate user account
    User.activate_user(ObjectId(student["user_id"]))
    
    return jsonify({"msg": "Student approved and account activated"}), 200

@student_bp.route("/remove/<student_id>", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def remove_student(student_id):
    student = Student.collection.find_one({"_id": ObjectId(student_id)})
    if not student:
        return jsonify({"msg": "Student not found"}), 404
        
    # Deactivate user account
    User.deactivate_user(ObjectId(student["user_id"]))
    # Update student status
    Student.remove_student(ObjectId(student_id))
    
    return jsonify({"msg": "Student removed and account deactivated"}), 200

@student_bp.route("/allocate-room", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def allocate_room():
    from app.models.room_model import Room, Bed
    data = request.json
    student_id = data.get("student_id")
    room_number = data.get("room_number")
    bed_number = data.get("bed_number")
    rent_amount = float(data.get("rent_amount", 0))
    deposit = float(data.get("deposit", 0))
    join_date = data.get("join_date", datetime.utcnow().strftime('%Y-%m-%d'))
    
    room = Room.collection.find_one({"room_number": room_number})
    block = room.get("block", "NA") if room else "NA"
    floor = room.get("floor", "NA") if room else "NA"

    # Update Student
    Student.collection.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {
            "room_number": str(room_number),
            "bed_number": str(bed_number),
            "block": str(block),
            "floor": str(floor),
            "rent_amount": float(rent_amount),
            "deposit": float(deposit),
            "join_date": datetime.strptime(join_date, '%Y-%m-%d'),
            "status": "approved" # Automatically approve if allocating a room
        }}
    )
    
    # Update Room and Bed
    room = Room.collection.find_one({"room_number": room_number})
    if room:
        Bed.assign_bed(room["_id"], bed_number, ObjectId(student_id))
        Room.update_occupancy(room["_id"], 1)
        
    # Send notification to student
    student = Student.collection.find_one({"_id": ObjectId(student_id)})
    if student:
        Notification.create(
            student["user_id"], 
            "room_allocation", 
            f"You have been allocated Room {room_number}, Bed {bed_number}. Monthly rent: ₹{rent_amount}."
        )

    return jsonify({"msg": f"Student allocated to room {room_number}, bed {bed_number}"}), 200

@student_bp.route("/search", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def search_students():
    query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    
    students_cursor = Student.collection.find({
        "$or": [
            {"username": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
            {"phone": {"$regex": query, "$options": "i"}},
            {"room_number": {"$regex": query, "$options": "i"}},
            {"status": {"$regex": query, "$options": "i"}}
        ]
    }).skip((page - 1) * per_page).limit(per_page)
    
    students = list(students_cursor)
    for s in students:
        s["_id"] = str(s["_id"])
        s["user_id"] = str(s["user_id"])
    return jsonify(students), 200

@student_bp.route("/update-deposit-status/<student_id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def update_deposit_status(student_id):
    data = request.json
    status = data.get("status") # refunded, pending, not_refunded
    
    Student.collection.update_one(
        {"_id": ObjectId(student_id)},
        {"$set": {"deposit_refund_status": status}}
    )
    
    return jsonify({"msg": f"Deposit status updated to {status}"}), 200
