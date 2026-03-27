from flask import Blueprint, request, jsonify
from app.models.notice_model import FoodMenu, Notice
from app.utils.middleware import role_required, handle_errors
from bson import ObjectId

notice_bp = Blueprint("notice", __name__)

@notice_bp.route("/menu", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def update_menu():
    data = request.get_json()
    FoodMenu.update_menu(data.get("day"), data.get("menu"))
    return jsonify({"msg": "Menu updated"}), 200

@notice_bp.route("/menu", methods=["GET"])
@handle_errors
def get_menu():
    menu = FoodMenu.get_all()
    for m in menu:
        m["_id"] = str(m["_id"])
    return jsonify(menu), 200

@notice_bp.route("/", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def create_notice():
    data = request.get_json()
    Notice.create_notice(data.get("title"), data.get("content"), data.get("priority"))
    return jsonify({"msg": "Notice posted"}), 201

@notice_bp.route("/", methods=["GET"])
@handle_errors
def get_notices():
    notices = Notice.get_active()
    for n in notices:
        n["_id"] = str(n["_id"])
    return jsonify(notices), 200

@notice_bp.route("/<notice_id>", methods=["DELETE"])
@role_required(["admin", "manager"])
@handle_errors
def delete_notice(notice_id):
    Notice.delete_notice(ObjectId(notice_id))
    return jsonify({"msg": "Notice removed"}), 200

@notice_bp.route("/<notice_id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def update_notice(notice_id):
    data = request.get_json()
    from app.config.database import db
    db["notices"].update_one(
        {"_id": ObjectId(notice_id)},
        {"$set": {
            "title": data.get("title"),
            "content": data.get("content"),
            "priority": data.get("priority", "normal")
        }}
    )
    return jsonify({"msg": "Notice updated"}), 200

# ─── Student Complaints / Raised Notices ─────────────────────────────────

from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notice_model import Complaint

@notice_bp.route("/complaints", methods=["POST"])
@jwt_required()
@handle_errors
def raise_complaint():
    user_id = get_jwt_identity()
    data = request.get_json()
    Complaint.create(
        user_id=user_id,
        title=data.get("title"),
        content=data.get("content"),
        category=data.get("category", "general")
    )
    return jsonify({"msg": "Complaint raised successfully"}), 201

@notice_bp.route("/complaints/mine", methods=["GET"])
@jwt_required()
@handle_errors
def get_my_complaints():
    user_id = get_jwt_identity()
    complaints = Complaint.get_by_user(user_id)
    for c in complaints:
        c["_id"] = str(c["_id"])
    return jsonify(complaints), 200

@notice_bp.route("/complaints/all", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_all_complaints():
    from app.models.user_model import User
    complaints = Complaint.get_all()
    for c in complaints:
        c["_id"] = str(c["_id"])
        # enrich with user name
        try:
            u = User.collection.find_one({"_id": ObjectId(c["user_id"])})
            c["student_name"] = u.get("username", "Unknown") if u else "Unknown"
        except Exception:
            c["student_name"] = "Unknown"
    return jsonify(complaints), 200

@notice_bp.route("/complaints/<complaint_id>/status", methods=["PATCH"])
@role_required(["admin", "manager"])
@handle_errors
def update_complaint_status(complaint_id):
    data = request.get_json()
    Complaint.update_status(ObjectId(complaint_id), data.get("status"))
    return jsonify({"msg": "Complaint status updated"}), 200
