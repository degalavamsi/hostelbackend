import os
from flask import Blueprint, redirect, request, jsonify, session
from google_auth_oauthlib.flow import Flow
from app.services.gmail_service import GmailService

gmail_bp = Blueprint("gmail", __name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Enable insecure transport for local HTTP testing
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

@gmail_bp.route("/gmail/auth")
def gmail_auth():
    """
    Initiates Google OAuth 2.0 flow and redirects the user to the Google Consent Screen.
    """
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri='http://127.0.0.1:5000/callback'
    )
    # prompt='consent' forces Google to supply a refresh_token
    # access_type='offline' enables background refreshing
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true'
    )
    session['oauth_state'] = state
    session['code_verifier'] = flow.code_verifier
    return redirect(auth_url)

@gmail_bp.route("/callback")
def oauth_callback():
    """
    Receives the callback from Google OAuth, retrieves the token credentials,
    saves them to MongoDB, and sends a test email to the configured sender address.
    """
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri='http://127.0.0.1:5000/callback',
        state=session.get('oauth_state')
    )
    flow.fetch_token(
        authorization_response=request.url,
        code_verifier=session.get('code_verifier')
    )
    creds = flow.credentials
    
    # Save credentials securely to database
    GmailService.save_credentials(creds)
    
    # Send a confirmation test email to the configured sender to verify it works
    sender = GmailService.get_sender_email()
    test_sent_status = ""
    try:
        GmailService.send_email(
            to=sender,
            subject="Hostel Management System - Gmail Authorization Successful",
            body_text="Your Gmail SMTP Sender is successfully configured and authorized!"
        )
        test_sent_status = f"and a confirmation test email has been sent to {sender}."
    except Exception as e:
        test_sent_status = f"but failed to send a confirmation test email: {str(e)}."
        
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <h2 style="color: #2b6cb0; margin-top: 0;">Authorization Successful!</h2>
        <p style="color: #4a5568; line-height: 1.6;">Gmail credentials have been successfully authenticated and saved in MongoDB. The system can now send automated emails in the background.</p>
        <p style="color: #4a5568; line-height: 1.6; font-weight: bold;">{test_sent_status}</p>
        <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="font-size: 0.875rem; color: #a0aec0;">You can close this tab now.</p>
    </div>
    """

@gmail_bp.route("/gmail/status")
def gmail_status():
    """
    Returns the current Gmail authorization status and the configured sender email.
    """
    is_auth = GmailService.is_authenticated()
    sender = GmailService.get_sender_email()
    return jsonify({
        "authenticated": is_auth,
        "sender_email": sender
    }), 200

@gmail_bp.route("/gmail/send", methods=["POST"])
def send_email():
    """
    Exposes an endpoint to send emails for notification and testing.
    JSON payload expected:
    {
        "to": "recipient@example.com",
        "subject": "Subject Line",
        "body": "Body Content"
    }
    """
    data = request.json or {}
    to = data.get("to")
    subject = data.get("subject", "Notification")
    body = data.get("body", "")
    
    if not to:
        return jsonify({"error": "Recipient email ('to') is required"}), 400
    if not body:
        return jsonify({"error": "Email body is required"}), 400
        
    try:
        result = GmailService.send_email(to, subject, body)
        return jsonify({
            "msg": "Email sent successfully",
            "details": result
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500
