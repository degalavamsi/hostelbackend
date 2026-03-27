from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

from app.routes.auth_routes import auth_bp
from app.routes.student_routes import student_bp
from app.routes.room_routes import room_bp
from app.routes.facility_routes import facility_bp
from app.routes.notice_routes import notice_bp
from app.routes.payment_routes import payment_bp
from app.routes.visitor_routes import visitor_bp
from app.routes.notification_routes import notification_bp
from app.routes.utility_routes import utility_bp
from app.routes.chatbot_routes import chatbot_bp
from app.config.database import db

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "hostel-pro-super-secret-key-123")
if not os.getenv("JWT_SECRET_KEY"):
    print("⚠️ WARNING: JWT_SECRET_KEY not found in environment. Using default fallback.")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # 16MB file limit

# Configure CORS globally for all routes
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
jwt = JWTManager(app)

@app.before_request
def log_request_info():
    print(f"DEBUG: Incoming {request.method} request to {request.path}")
    if request.method == 'OPTIONS':
        print(f"DEBUG: OPTIONS preflight for {request.path}")

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(student_bp, url_prefix="/students")
app.register_blueprint(room_bp, url_prefix="/rooms")
app.register_blueprint(facility_bp, url_prefix="/facilities")
app.register_blueprint(notice_bp, url_prefix="/notices")
app.register_blueprint(payment_bp, url_prefix="/payments")
app.register_blueprint(visitor_bp, url_prefix="/visitors")
app.register_blueprint(notification_bp, url_prefix="/notifications")
app.register_blueprint(utility_bp, url_prefix="/utilities")
app.register_blueprint(chatbot_bp, url_prefix="/chatbot")

@app.route("/")
def index():
    return jsonify({"msg": "Hostel Management System API is running"}), 200

@app.route("/health")
def health_check():
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "environment": os.getenv("FLASK_ENV", "production")
    }
    try:
        from app.config.database import Database
        # Check if Database.db is a MockDatabase
        from app.config.database import MockDatabase
        if isinstance(db, MockDatabase):
            health_status["database"] = "offline (Mocking Enabled)"
            health_status["status"] = "degraded"
        else:
            # Try to ping
            db.command('ping')
            health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return jsonify(health_status), 200 if health_status["status"] == "healthy" else 500

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    from flask import send_from_directory
    upload_folder = os.path.abspath("uploads")
    return send_from_directory(upload_folder, filename)

# Ensure uploads directory exists (Safe for read-only environments like Vercel)
try:
    os.makedirs("uploads/documents", exist_ok=True)
except Exception as e:
    print(f"⚠️ Could not create uploads directory: {e}")

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=bool(os.getenv("DEBUG", True)))
