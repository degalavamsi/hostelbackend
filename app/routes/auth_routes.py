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

@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    import os
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    from app.models.user_model import User
    from flask_jwt_extended import create_access_token
    
    data = request.json or {}
    token = data.get("token")
    if not token:
        return jsonify({"msg": "Token is required"}), 400
        
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        # Verify the Google ID Token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
        
        email = idinfo.get("email")
        if not email:
            return jsonify({"msg": "Email not found in Google profile"}), 400
            
        # Look up user in MongoDB
        user = User.find_by_email(email)
        
        if not user:
            # Auto-register new users as students
            username = idinfo.get("name") or email.split("@")[0]
            insert_result = User.create_user(
                username=username,
                email=email,
                password="",  # No password for Google SSO users
                roles=["student"],
                is_active=True
            )
            user = User.collection.find_one({"_id": insert_result.inserted_id})
            
            # Auto-create the Student document
            from app.models.student_model import Student
            student_data = {
                "username": username,
                "email": email,
                "phone": user.get("phone", "")
            }
            Student.create_student(user["_id"], student_data)
            
        if not user.get("is_active", True):
            return jsonify({"msg": "User account is inactive"}), 400
            
        # Create access token using flask-jwt-extended
        access_token = create_access_token(identity=str(user["_id"]))
        
        return jsonify({
            "token": access_token,
            "user": {
                "id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "roles": user.get("roles", ["student"]),
                "phone": user.get("phone")
            }
        }), 200
        
    except ValueError as e:
        return jsonify({"msg": f"Invalid Google token: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"msg": f"Google authentication failed: {str(e)}"}), 500


@auth_bp.route("/github-login", methods=["POST"])
def github_login():
    import os
    import requests
    from app.models.user_model import User
    from app.utils.jwt_helper import JWTHelper
    
    data = request.json or {}
    code = data.get("code")
    if not code:
        return jsonify({"msg": "Authorization code is required"}), 400
        
    try:
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        
        # 1. Exchange authorization code for access token
        token_url = "https://github.com/login/oauth/access_token"
        token_response = requests.post(
            token_url,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code
            }
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return jsonify({"msg": f"Failed to retrieve access token from GitHub: {token_data.get('error_description', 'Unknown error')}"}), 400
            
        # 2. Get user profile details
        user_url = "https://api.github.com/user"
        user_response = requests.get(
            user_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_profile = user_response.json()
        
        # 3. Get user email list (since email might be private/hidden)
        emails_url = "https://api.github.com/user/emails"
        emails_response = requests.get(
            emails_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        emails_list = emails_response.json()
        
        # Find primary or first verified email
        email = None
        if isinstance(emails_list, list):
            for e in emails_list:
                if e.get("primary") and e.get("verified"):
                    email = e.get("email")
                    break
            if not email:
                for e in emails_list:
                    if e.get("verified"):
                        email = e.get("email")
                        break
            if not email and emails_list:
                email = emails_list[0].get("email")
                
        if not email:
            email = user_profile.get("email")
            
        if not email:
            return jsonify({"msg": "Email address not found in GitHub profile. Please ensure you have a verified email on GitHub."}), 400
            
        # 4. Check if user already exists in MongoDB
        user = User.find_by_email(email)
        
        if not user:
            # Auto-register new users as students
            username = user_profile.get("name") or user_profile.get("login") or email.split("@")[0]
            insert_result = User.create_user(
                username=username,
                email=email,
                password="",  # No password for OAuth users
                roles=["student"],
                is_active=True
            )
            user = User.collection.find_one({"_id": insert_result.inserted_id})
            
            # Auto-create the Student document
            from app.models.student_model import Student
            student_data = {
                "username": username,
                "email": email,
                "phone": user.get("phone", "")
            }
            Student.create_student(user["_id"], student_data)
            
        if not user.get("is_active", True):
            return jsonify({"msg": "User account is inactive"}), 400
            
        # 5. Generate application JWT token
        roles = user.get("roles", ["student"])
        app_token = JWTHelper.generate_token(str(user["_id"]), roles)
        
        return jsonify({
            "token": app_token,
            "user": {
                "id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "roles": roles,
                "phone": user.get("phone")
            }
        }), 200
        
    except Exception as e:
        print(f"ERROR: GitHub authentication failed: {str(e)}")
        return jsonify({"msg": f"GitHub authentication failed: {str(e)}"}), 500


