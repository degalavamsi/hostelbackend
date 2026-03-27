from flask import Blueprint, request, jsonify
from app.models.facility_model import Facility
from app.models.student_model import Student
from app.utils.middleware import role_required, handle_errors
from flask_jwt_extended import jwt_required, get_jwt_identity

facility_bp = Blueprint("facility", __name__)

@facility_bp.route("/update", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def update_facilities():
    data = request.get_json()
    floor = data.get("floor")
    facilities = data.get("facilities")
    Facility.update_floor_facilities(floor, facilities)
    return jsonify({"msg": "Facilities updated"}), 200

@facility_bp.route("/all", methods=["GET"])
@jwt_required()
@handle_errors
def get_all_facilities():
    facilities = Facility.get_all()
    for f in facilities:
        f["_id"] = str(f["_id"])
    return jsonify(facilities), 200

@facility_bp.route("/floor/<int:floor>", methods=["GET"])
@jwt_required()
@handle_errors
def get_floor_facilities(floor):
    facility = Facility.get_by_floor(floor)
    if facility:
        facility["_id"] = str(facility["_id"])
    return jsonify(facility), 200
