from flask import Blueprint, request, jsonify
from app.services.chatbot_service import ChatbotService
from flask_jwt_extended import jwt_required, get_jwt_identity

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/message', methods=['POST'])
def get_message():
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    # Optional JWT identity for personalized responses (room, fees)
    user_id = None
    try:
        from flask_jwt_extended import decode_token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            decoded = decode_token(token)
            user_id = decoded.get('sub')
    except:
        pass
        
    response = ChatbotService.get_response(message, user_id=user_id)
    return jsonify(response), 200
