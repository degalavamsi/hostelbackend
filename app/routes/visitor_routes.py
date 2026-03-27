from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.visitor_model import Visitor
from app.utils.middleware import role_required, handle_errors
from app.models.notification_model import Notification
from bson import ObjectId

visitor_bp = Blueprint("visitor", __name__)

@visitor_bp.route("/log", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def log_visitor():
    data = request.json
    Visitor.log_entry(data)
    return jsonify({"msg": "Visitor log entry created"}), 201

@visitor_bp.route("/exit/<visitor_id>", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def log_exit(visitor_id):
    Visitor.log_exit(ObjectId(visitor_id))
    return jsonify({"msg": "Visitor exit logged"}), 200

@visitor_bp.route("/all", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_visitors():
    visitors = Visitor.get_all()
    for v in visitors:
        v["_id"] = str(v["_id"])
        if v.get("submitted_by"):
            v["submitted_by"] = str(v["submitted_by"])
    return jsonify(visitors), 200

@visitor_bp.route("/pending", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_pending_requests():
    requests_list = Visitor.get_pending_requests()
    for v in requests_list:
        v["_id"] = str(v["_id"])
        if v.get("submitted_by"):
            v["submitted_by"] = str(v["submitted_by"])
    return jsonify(requests_list), 200

# Student: Submit a visitor request
@visitor_bp.route("/request", methods=["POST"])
@jwt_required()
@handle_errors
def submit_visitor_request():
    user_id = get_jwt_identity()
    data = request.json
    required = ["visitor_name", "phone", "relation", "visit_date", "entry_time", "exit_time"]
    for field in required:
        if not data.get(field):
            return jsonify({"msg": f"Missing field: {field}"}), 400
    Visitor.request_visitor(user_id, data)
    return jsonify({"msg": "Visitor request submitted. Awaiting approval."}), 201

# Student: View own visitor requests
@visitor_bp.route("/my-requests", methods=["GET"])
@jwt_required()
@handle_errors
def my_visitor_requests():
    user_id = get_jwt_identity()
    items = Visitor.get_by_student(user_id)
    for v in items:
        v["_id"] = str(v["_id"])
        if v.get("submitted_by"):
            v["submitted_by"] = str(v["submitted_by"])
    return jsonify(items), 200

# Admin: Approve or deny a visitor request
@visitor_bp.route("/approve/<visitor_id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def approve_visitor_request(visitor_id):
    data = request.json
    status = data.get("status", "approved")  # approved or denied
    Visitor.approve(visitor_id, status)

    # Notify the student who submitted the request
    visitor = Visitor.collection.find_one({"_id": ObjectId(visitor_id)})
    if visitor and visitor.get("submitted_by"):
        action = "approved ✅" if status == "approved" else "denied ❌"
        Notification.create(
            str(visitor["submitted_by"]),
            "visitor_update",
            f"Your visitor request for {visitor.get('visitor_name', 'your guest')} has been {action}."
        )

    return jsonify({"msg": f"Visitor request {status}"}), 200
