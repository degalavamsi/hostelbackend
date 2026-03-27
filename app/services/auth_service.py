import os
from werkzeug.utils import secure_filename
from app.models.user_model import User
from app.utils.jwt_helper import JWTHelper
from bson import ObjectId

class AuthService:
    # Use absolute path so files are saved correctly regardless of working directory
    UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'documents'))
    
    @staticmethod
    def _is_strong_password(password):
        """
        Validate password strength:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter."
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter."
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit."
        special_chars = "!@#$%^&*(),.?\":{}|<>"
        if not any(char in special_chars for char in password):
            return False, "Password must contain at least one special character (!@#$%^&* etc.)."
        return True, ""

    @staticmethod
    def login(email, password):
        try:
            print(f"DEBUG: Login attempt for {email}")
            user = User.find_by_email(email)
            if not user:
                print(f"DEBUG: Login failed - User not found: {email}")
                return {"msg": "User not found"}, 401
                
            if not user.get("is_active"):
                print(f"DEBUG: Login failed - Account inactive: {email}")
                return {"msg": "Your account is currently inactive. Please contact the administrator for approval."}, 401
                
            if User.verify_password(password, user["password"]):
                token = JWTHelper.generate_token(str(user["_id"]), user["roles"])
                print(f"DEBUG: Login successful for {email}")
                return {"token": token, "user": {"username": user["username"], "roles": user["roles"]}}, 200
                
            print(f"DEBUG: Login failed - Invalid password: {email}")
            return {"msg": "Invalid credentials"}, 401
        except Exception as e:
            print(f"DEBUG: CRITICAL Login Error: {str(e)}")
            return {"msg": f"Database Connection Error: {str(e)}"}, 500

    @staticmethod
    def register_request(data, files=None):
        print(f"DEBUG: Registration request received: {data.get('email')}")
        from app.models.student_model import Student
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone")
        roles = data.get("roles", ["student"])
        
        is_strong, msg = AuthService._is_strong_password(password)
        if not is_strong:
            return {"msg": msg}, 400
            
        if User.find_by_email(email):
            print(f"DEBUG: Registration failed - Email already exists: {email}")
            return {"msg": "This email is already registered. Try logging in."}, 400
            
        try:
            # Create user as inactive for students
            is_active = False if "student" in roles else True
            user_result = User.create_user(username, email, password, roles, phone=phone, is_active=is_active)
            user_id = user_result.inserted_id
            print(f"DEBUG: User record created with ID: {user_id}")
            
            # If student, create a pending student record
            if "student" in roles:
                student_data = {
                    "username": username,
                    "phone": phone,
                    "email": email
                }
                
                # Handle files if provided
                if files:
                    # Ensure the directory exists before saving
                    os.makedirs(AuthService.UPLOAD_FOLDER, exist_ok=True)
                    if 'photo' in files:
                        photo = files['photo']
                        if photo.filename != '':
                            photo_filename = secure_filename(f"{user_id}_photo_{photo.filename}")
                            photo.save(os.path.join(AuthService.UPLOAD_FOLDER, photo_filename))
                            student_data['photo_path'] = photo_filename
                            
                    if 'id_proof' in files:
                        id_proof = files['id_proof']
                        if id_proof.filename != '':
                            id_filename = secure_filename(f"{user_id}_id_{id_proof.filename}")
                            id_proof.save(os.path.join(AuthService.UPLOAD_FOLDER, id_filename))
                            student_data['id_proof_path'] = id_filename

                Student.create_student(user_id, student_data)
                print(f"DEBUG: Student record created for user {user_id}")
                
            return {"msg": "Registration request submitted. Wait for approval."}, 201
        except Exception as e:
            print(f"DEBUG: ERROR during registration: {str(e)}")
            return {"msg": f"Internal server error: {str(e)}"}, 500

    @staticmethod
    def get_profile(user_id):
        user = User.collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None, 404
            
        profile = {
            "username": user["username"],
            "email": user["email"],
            "phone": user.get("phone"),
            "roles": user["roles"],
            "photo_path": user.get("photo_path"),
            "id_proof_path": user.get("id_proof_path")
        }
        
        if "student" in user.get("roles", []):
            from app.models.student_model import Student
            student = Student.get_by_user_id(user_id)
            if student:
                profile.update({
                    "room_number": str(student.get("room_number")) if student.get("room_number") else "NA",
                    "bed_number": str(student.get("bed_number")) if student.get("bed_number") else "NA",
                    "block": str(student.get("block")) if student.get("block") else "NA",
                    "floor": str(student.get("floor")) if student.get("floor") else "NA",
                    "rent_amount": student.get("rent_amount"),
                    "deposit": student.get("deposit"),
                    "deposit_paid_date": student.get("deposit_paid_date"),
                    "deposit_refund_status": student.get("deposit_refund_status"),
                    "join_date": student.get("join_date"),
                    "status": student.get("status"),
                    "photo_path": student.get("photo_path"),
                    "id_proof_path": student.get("id_proof_path")
                })
        
        return profile, 200

    @staticmethod
    def upload_documents(user_id, files):
        if not files:
            return {"msg": "No files provided"}, 400
        try:
            from app.models.student_model import Student
            os.makedirs(AuthService.UPLOAD_FOLDER, exist_ok=True)
            update_data = {}

            if 'photo' in files:
                photo = files['photo']
                if photo.filename:
                    filename = secure_filename(f"{user_id}_photo_{photo.filename}")
                    photo.save(os.path.join(AuthService.UPLOAD_FOLDER, filename))
                    update_data['photo_path'] = filename

            if 'id_proof' in files:
                id_proof = files['id_proof']
                if id_proof.filename:
                    filename = secure_filename(f"{user_id}_id_{id_proof.filename}")
                    id_proof.save(os.path.join(AuthService.UPLOAD_FOLDER, filename))
                    update_data['id_proof_path'] = filename

            if update_data:
                user = User.collection.find_one({"_id": ObjectId(user_id)})
                if user and ("admin" in user.get("roles", []) or "manager" in user.get("roles", [])):
                    User.collection.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$set": update_data}
                    )
                else:
                    Student.collection.update_one(
                        {"user_id": ObjectId(user_id)},
                        {"$set": update_data}
                    )
            return {"msg": "Documents uploaded successfully"}, 200
        except Exception as e:
            print(f"DEBUG: Upload error: {str(e)}")
            return {"msg": f"Upload failed: {str(e)}"}, 500

    @staticmethod
    def upload_loader(files):
        if not files or 'loader_image' not in files:
            return {"msg": "No loader image provided"}, 400
        
        try:
            loader_image = files['loader_image']
            if loader_image.filename:
                # Path to the frontend logo asset
                frontend_asset_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'public', 'assets')
                os.makedirs(frontend_asset_dir, exist_ok=True)
                
                # Overwrite codegnan-logo.png directly
                target_path = os.path.join(frontend_asset_dir, 'codegnan-logo.png')
                loader_image.save(target_path)
                return {"msg": "Loader logo uploaded successfully via file overwrite!"}, 200
                
            return {"msg": "Invalid file format"}, 400
            
        except Exception as e:
            print(f"DEBUG: Loader Upload error: {str(e)}")
            return {"msg": f"Loader upload failed: {str(e)}"}, 500

    @staticmethod
    def update_profile(user_id, data):
        allowed_fields = ["username", "phone", "block", "floor"]
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        from app.models.student_model import Student
        
        # Split updates between User and Student collections
        user_updates = {k: v for k, v in update_data.items() if k in ["username", "phone"]}
        student_updates = {k: v for k, v in update_data.items() if k in ["block", "floor"]}
        
        if user_updates:
            User.collection.update_one({"_id": ObjectId(user_id)}, {"$set": user_updates})
        if student_updates:
            Student.collection.update_one({"user_id": ObjectId(user_id)}, {"$set": student_updates})
            
        return {"msg": "Profile updated successfully"}, 200

    @staticmethod
    def change_password(user_id, data):
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        is_strong, msg = AuthService._is_strong_password(new_password)
        if not is_strong:
            return {"msg": msg}, 400
            
        user = User.collection.find_one({"_id": ObjectId(user_id)})
        
        if not User.verify_password(old_password, user["password"]):
            return {"msg": "Incorrect old password"}, 400
            
        hashed_password = User.hash_password(new_password)
        User.collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})
        return {"msg": "Password changed successfully"}, 200

    @staticmethod
    def admin_reset_password(data):
        student_id = data.get("student_id")
        new_password = data.get("new_password")
        
        is_strong, msg = AuthService._is_strong_password(new_password)
        if not is_strong:
            return {"msg": msg}, 400
            
        hashed_password = User.hash_password(new_password)
        User.collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"password": hashed_password}})
        return {"msg": "Student password reset successfully"}, 200
