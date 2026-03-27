from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.payment_model import Payment
from app.models.notification_model import Notification
from app.utils.middleware import role_required, handle_errors
from bson import ObjectId
import os
from datetime import datetime
from werkzeug.utils import secure_filename

payment_bp = Blueprint("payment", __name__)

UPLOAD_FOLDER = 'uploads/receipts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@payment_bp.route("/upload-receipt", methods=["POST"])
@jwt_required()
@handle_errors
def upload_receipt():
    user_id = get_jwt_identity()
    
    if 'receipt' not in request.files:
        return jsonify({"msg": "No receipt file"}), 400
        
    file = request.files['receipt']
    if file.filename == '':
        return jsonify({"msg": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user_id}_{datetime.now().strftime('%Y%m')}_{file.filename}")
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        
        payment_data = {
            "student_id": ObjectId(user_id),
            "month": request.form.get("month"),
            "year": request.form.get("year"),
            "amount": float(request.form.get("amount")),
            "type": request.form.get("type", "rent"),
            "receipt_path": filename
        }
        
        Payment.create_payment(payment_data)
        return jsonify({"msg": "Receipt uploaded successfully"}), 201
    
    return jsonify({"msg": "Invalid file type"}), 400

@payment_bp.route("/history", methods=["GET"])
@jwt_required()
@handle_errors
def get_payment_history():
    user_id = get_jwt_identity()
    history = Payment.get_history(ObjectId(user_id))
    for h in history:
        h["_id"] = str(h["_id"])
        h["student_id"] = str(h["student_id"])
    return jsonify(history), 200

@payment_bp.route("/all", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_all_payments():
    from app.models.student_model import Student
    from app.models.user_model import User
    payments = list(Payment.collection.find().sort("created_at", -1))
    for p in payments:
        p["_id"] = str(p["_id"])
        sid = p.get("student_id")
        p["student_id"] = str(sid) if sid else ""
        # Enrich with student name + room info
        if sid:
            try:
                student = Student.collection.find_one({"user_id": ObjectId(str(sid))})
                user = User.collection.find_one({"_id": ObjectId(str(sid))})
                p["student_name"] = user.get("username", "Unknown") if user else "Unknown"
                p["student_room"] = student.get("room_number", "—") if student else "—"
                p["student_bed"] = student.get("bed_number", "") if student else ""
            except Exception:
                p["student_name"] = "Unknown"
                p["student_room"] = "—"
                p["student_bed"] = ""
    return jsonify(payments), 200

@payment_bp.route("/verify/<payment_id>", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def verify_payment(payment_id):
    Payment.verify_payment(ObjectId(payment_id))
    return jsonify({"msg": "Payment verified"}), 200

@payment_bp.route("/<payment_id>/status", methods=["PATCH"])
@role_required(["admin", "manager"])
@handle_errors
def update_payment_status(payment_id):
    data = request.get_json()
    amount_paid = float(data.get("amount_paid", 0))
    status = data.get("status", "pending")
    
    payment = Payment.collection.find_one({"_id": ObjectId(payment_id)})
    if payment and payment.get("type", "rent") == "deposit":
        from app.models.student_model import Student
        if status in ["paid", "verified"]:
            Student.collection.update_one({"user_id": payment["student_id"]}, {"$set": {"deposit_refund_status": "paid"}})
        else:
            Student.collection.update_one({"user_id": payment["student_id"]}, {"$set": {"deposit_refund_status": "not_paid"}})
            
    Payment.update_payment_details(ObjectId(payment_id), amount_paid, status)
    return jsonify({"msg": "Payment details updated"}), 200

@payment_bp.route("/<payment_id>/remind", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def send_payment_reminder(payment_id):
    payment = Payment.collection.find_one({"_id": ObjectId(payment_id)})
    if not payment:
        return jsonify({"msg": "Payment not found"}), 404

    due_amount = payment.get("balance", payment.get("amount", 0))
    month = payment.get("month", "")
    year = payment.get("year", "")

    custom_message = request.form.get("message", "")
    upi_id = request.form.get("upi_id", "")
    qr_url = ""

    # Handle QR image upload
    if "qr_image" in request.files:
        qr_file = request.files["qr_image"]
        if qr_file and qr_file.filename != "" and allowed_file(qr_file.filename):
            qr_filename = secure_filename(f"qr_{payment_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{qr_file.filename}")
            qr_save_path = os.path.join("uploads/qr_codes", qr_filename)
            os.makedirs("uploads/qr_codes", exist_ok=True)
            qr_file.save(qr_save_path)
            qr_url = f"/uploads/qr_codes/{qr_filename}"

    # Build readable message text
    base_msg = f"💰 Payment Reminder: ₹{due_amount} due for {month} {year}."
    if custom_message:
        base_msg += f" Note: {custom_message}"

    # Store upi_id and qr_url as dedicated fields on the notification
    extra = {}
    if upi_id:
        extra["upi_id"] = upi_id
    if qr_url:
        extra["qr_url"] = qr_url

    Notification.create(str(payment["student_id"]), "payment_reminder", base_msg, extra=extra if extra else None)
    return jsonify({"msg": "Reminder sent with QR code"}), 200

@payment_bp.route("/generate-monthly-rent", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def generate_rent():
    data = request.json
    month = data.get("month")
    year = data.get("year")
    amount = float(data.get("amount"))
    due_date_str = data.get("due_date")
    student_id_val = data.get("student_id")
    upi_id = data.get("upi_id", "")
    qr_url = data.get("qr_url", "")
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')

    from app.models.student_model import Student
    query = {"status": "approved"}
    if student_id_val and student_id_val != "all":
        query["user_id"] = ObjectId(student_id_val) if ObjectId.is_valid(student_id_val) else str(student_id_val)

    students = list(Student.collection.find(query))
    created_count = 0
    for s in students:
        exists = Payment.collection.find_one({
            "student_id": s["user_id"], "month": month, "year": year, "type": "rent"
        })
        if not exists:
            Payment.create_payment({
                "student_id": s["user_id"], "month": month, "year": year,
                "amount": s.get("rent_amount", amount),
                "due_date": due_date, "is_paid": False, "status": "unpaid", "type": "rent"
            })
            msg = f"Monthly rent generated for {month} {year}: \u20b9{s.get('rent_amount', amount)}. Due by {due_date.strftime('%Y-%m-%d')}."
            extra = {}
            if upi_id:
                extra["upi_id"] = upi_id
            if qr_url:
                extra["qr_url"] = qr_url
            Notification.create(s["user_id"], "rent_due", msg, extra=extra if extra else None)
            created_count += 1

    return jsonify({"msg": f"Rent generated for {created_count} students"}), 201

@payment_bp.route("/dues", methods=["GET"])
@role_required(["admin", "manager"])
@handle_errors
def get_all_dues():
    dues = list(Payment.collection.find({"is_paid": False}))
    for d in dues:
        d["_id"] = str(d["_id"])
        d["student_id"] = str(d["student_id"])
    return jsonify(dues), 200
