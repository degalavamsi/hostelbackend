from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.middleware import role_required

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    result, status = AuthService.login(email, password)
    return jsonify(result), status

@auth_bp.route("/register-request", methods=["POST"])
def register_request():
    # Support both JSON and Form (for file uploads)
    if request.is_json:
        data = request.json
    else:
        data = request.form.to_dict()
        
    files = request.files if request.files else None
    result, status = AuthService.register_request(data, files)
    return jsonify(result), status

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    result, status = AuthService.get_profile(user_id)
    return jsonify(result), status

@auth_bp.route("/upload-documents", methods=["POST"])
@jwt_required()
def upload_documents():
    user_id = get_jwt_identity()
    files = request.files if request.files else None
    result, status = AuthService.upload_documents(user_id, files)
    return jsonify(result), status

@auth_bp.route("/upload-loader", methods=["POST"])
@role_required(["admin", "manager"])
def upload_loader():
    files = request.files if request.files else None
    result, status = AuthService.upload_loader(files)
    return jsonify(result), status

@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.json
    result, status = AuthService.update_profile(user_id, data)
    return jsonify(result), status

@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.json
    result, status = AuthService.change_password(user_id, data)
    return jsonify(result), status

@auth_bp.route("/admin/reset-password", methods=["POST"])
@role_required(["admin", "manager"])
def admin_reset_password():
    data = request.json
    result, status = AuthService.admin_reset_password(data)
    return jsonify(result), status
