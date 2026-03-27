from flask import Blueprint, request, jsonify
from app.models.washing_model import WashingMachine
from app.models.water_model import WaterMachine
from app.models.wifi_model import WiFiConfig
from app.models.student_model import Student
from app.utils.middleware import role_required, handle_errors
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId

utility_bp = Blueprint("utility", __name__)

# --- Washing Machines ---

@utility_bp.route("/washing", methods=["GET"])
@jwt_required()
@handle_errors
def get_washing_machines():
    machines = WashingMachine.get_all()
    for m in machines:
        m["_id"] = str(m["_id"])
    return jsonify(machines), 200

@utility_bp.route("/washing", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def add_washing_machine():
    data = request.get_json()
    WashingMachine.create(data)
    return jsonify({"msg": "Washing machine added"}), 201

@utility_bp.route("/washing/<id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def update_washing_machine(id):
    data = request.get_json()
    WashingMachine.update(id, data)
    return jsonify({"msg": "Washing machine updated"}), 200

@utility_bp.route("/washing/<id>", methods=["DELETE"])
@role_required(["admin", "manager"])
@handle_errors
def delete_washing_machine(id):
    WashingMachine.delete(id)
    return jsonify({"msg": "Washing machine deleted"}), 200

# --- Water Machines ---

@utility_bp.route("/water", methods=["GET"])
@jwt_required()
@handle_errors
def get_water_machines():
    machines = WaterMachine.get_all()
    for m in machines:
        m["_id"] = str(m["_id"])
    return jsonify(machines), 200

@utility_bp.route("/water", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def add_water_machine():
    data = request.get_json()
    WaterMachine.create(data)
    return jsonify({"msg": "Water machine added"}), 201

@utility_bp.route("/water/<id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def update_water_machine(id):
    data = request.get_json()
    WaterMachine.update(id, data)
    return jsonify({"msg": "Water machine updated"}), 200

@utility_bp.route("/water/<id>", methods=["DELETE"])
@role_required(["admin", "manager"])
@handle_errors
def delete_water_machine(id):
    WaterMachine.delete(id)
    return jsonify({"msg": "Water machine deleted"}), 200

# --- WiFi Configs ---

@utility_bp.route("/wifi", methods=["GET"])
@jwt_required()
@handle_errors
def get_wifi_configs():
    configs = WiFiConfig.get_all()
    for c in configs:
        c["_id"] = str(c["_id"])
    return jsonify(configs), 200

@utility_bp.route("/wifi", methods=["POST"])
@role_required(["admin", "manager"])
@handle_errors
def add_wifi_config():
    data = request.get_json()
    WiFiConfig.create(data)
    return jsonify({"msg": "WiFi config added"}), 201

@utility_bp.route("/wifi/<id>", methods=["PUT"])
@role_required(["admin", "manager"])
@handle_errors
def update_wifi_config(id):
    data = request.get_json()
    WiFiConfig.update(id, data)
    return jsonify({"msg": "WiFi config updated"}), 200

@utility_bp.route("/wifi/<id>", methods=["DELETE"])
@role_required(["admin", "manager"])
@handle_errors
def delete_wifi_config(id):
    WiFiConfig.delete(id)
    return jsonify({"msg": "WiFi config deleted"}), 200
