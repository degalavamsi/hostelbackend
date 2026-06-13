import os
import base64
from datetime import datetime
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.config.database import db

class GmailService:
    @classmethod
    def save_credentials(cls, creds):
        """
        Saves the serialized credentials to MongoDB.
        """
        creds_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "updated_at": datetime.utcnow()
        }
        db["gmail_credentials"].update_one(
            {"_id": "system_gmail_credentials"},
            {"$set": creds_data},
            upsert=True
        )

    @classmethod
    def load_credentials(cls):
        """
        Loads credentials from MongoDB. Refreshes them if they have expired.
        """
        doc = db["gmail_credentials"].find_one({"_id": "system_gmail_credentials"})
        if not doc:
            return None
            
        creds = Credentials(
            token=doc.get("token"),
            refresh_token=doc.get("refresh_token"),
            token_uri=doc.get("token_uri"),
            client_id=doc.get("client_id"),
            client_secret=doc.get("client_secret"),
            scopes=doc.get("scopes")
        )
        
        # Check if the credentials need to be refreshed
        if creds.expired or not creds.valid:
            if creds.refresh_token:
                print("Gmail credentials expired. Refreshing token...")
                try:
                    creds.refresh(Request())
                    # Save the refreshed credentials back to MongoDB
                    cls.save_credentials(creds)
                    print("Gmail credentials refreshed and updated in database successfully.")
                except Exception as e:
                    print(f"Error refreshing Gmail credentials: {e}")
            else:
                print("Gmail credentials expired, but no refresh_token was found. Please re-authenticate.")
                
        return creds

    @classmethod
    def is_authenticated(cls):
        """
        Checks if credentials exist and are valid (or can be refreshed).
        """
        creds = cls.load_credentials()
        return creds is not None and creds.valid

    @classmethod
    def get_sender_email(cls):
        """
        Returns the sender email configured in environment.
        """
        return os.getenv("GOOGLE_SENDER_EMAIL", "degalasaivmsidegalasaivamsi2@gmail.com")

    @classmethod
    def send_email(cls, to, subject, body_text):
        """
        Sends an email using the stored Google credentials.
        """
        creds = cls.load_credentials()
        if not creds:
            raise ValueError("Gmail service is not authenticated. Please run the OAuth flow first.")
            
        service = build('gmail', 'v1', credentials=creds)
        
        message = MIMEText(body_text)
        message['to'] = to
        message['subject'] = subject
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        
        result = service.users().messages().send(userId='me', body=body).execute()
        return result
