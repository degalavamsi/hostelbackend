from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.notification_model import Notification
from app.utils.middleware import handle_errors, role_required
from bson import ObjectId

notification_bp = Blueprint("notification", __name__)

@notification_bp.route("/", methods=["GET"])
@jwt_required()
@handle_errors
def get_notifications():
    user_id = get_jwt_identity()
    notifications = Notification.get_by_user(user_id)
    result = []
    for n in notifications:
        item = {
            "_id": str(n["_id"]),
            "recipient_id": str(n["recipient_id"]),
            "type": n.get("type"),
            "message": n.get("message"),
            "is_read": n.get("is_read", False),
            "response": n.get("response"),
            "created_at": n.get("created_at").isoformat() if n.get("created_at") else None,
            # Include optional payment reminder fields
            "upi_id": n.get("upi_id"),
            "qr_url": n.get("qr_url"),
        }
        result.append(item)
    return jsonify(result), 200

@notification_bp.route("/unread-count", methods=["GET"])
@jwt_required()
@handle_errors
def get_unread_count():
    user_id = get_jwt_identity()
    count = Notification.get_unread_count(user_id)
    return jsonify({"count": count}), 200

@notification_bp.route("/read/<notification_id>", methods=["POST"])
@jwt_required()
@handle_errors
def mark_as_read(notification_id):
    Notification.mark_as_read(notification_id)
    return jsonify({"msg": "Notification marked as read"}), 200

@notification_bp.route("/<notification_id>", methods=["DELETE"])
@jwt_required()
@handle_errors
def delete_notification(notification_id):
    user_id = get_jwt_identity()
    result = Notification.delete(notification_id, user_id)
    if result.deleted_count == 0:
        return jsonify({"msg": "Notification not found or not yours"}), 404
    return jsonify({"msg": "Notification deleted"}), 200

@notification_bp.route("/<notification_id>/respond", methods=["POST"])
@jwt_required()
@handle_errors
def respond_to_notification(notification_id):
    user_id = get_jwt_identity()
    data = request.json
    response_text = data.get("response", "").strip()
    if not response_text:
        return jsonify({"msg": "Response cannot be empty"}), 400
    Notification.respond(notification_id, user_id, response_text)
    return jsonify({"msg": "Response saved"}), 200

@notification_bp.route("/broadcast", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def broadcast_notification():
    data = request.json
    n_type = data.get("type")
    message = data.get("message")
    from app.models.student_model import Student
    students = list(Student.collection.find({"status": "approved"}))
    for student in students:
        Notification.create(student["user_id"], n_type, message)
    return jsonify({"msg": f"Broadcast sent to {len(students)} students"}), 200

@notification_bp.route("/responses/read/<notification_id>", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def mark_admin_read(notification_id):
    from bson import ObjectId
    Notification.collection.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"admin_read": True}}
    )
    return jsonify({"msg": "Response marked as read"}), 200

@notification_bp.route("/responses", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_student_responses():
    """Admin-only: returns all notifications that have a student response."""
    from app.models.user_model import User
    raw = list(Notification.collection.find(
        {"response": {"$ne": None}, "admin_read": {"$ne": True}},
        sort=[("responded_at", -1)]
    ))
    result = []
    for n in raw:
        from bson import ObjectId
        user = None
        try:
            user = User.collection.find_one({"_id": ObjectId(str(n["recipient_id"]))})
        except:
            pass
            
        username = user.get("username", "Unknown") if user else str(n["recipient_id"])
        result.append({
            "_id": str(n["_id"]),
            "recipient_id": str(n["recipient_id"]),
            "student_name": username,
            "type": n.get("type"),
            "message": n.get("message"),
            "response": n.get("response"),
            "responded_at": n.get("responded_at").isoformat() if n.get("responded_at") else None,
            "created_at": n.get("created_at").isoformat() if n.get("created_at") else None,
        })
    return jsonify(result), 200
