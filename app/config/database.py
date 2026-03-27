import os
from pymongo import MongoClient
from dotenv import load_dotenv
import ssl
import certifi

load_dotenv()

class MockCollection:
    def insert_one(self, data):
        raise ConnectionError("Database not connected")

    def update_one(self, filter, update):
        raise ConnectionError("Database not connected")

    def find_one(self, filter):
        raise ConnectionError("Database not connected")

    def find(self, filter=None):
        raise ConnectionError("Database not connected")

    def delete_one(self, filter):
        raise ConnectionError("Database not connected")

    def delete_many(self, filter):
        raise ConnectionError("CRITICAL: Database connection is offline. Operation failed.")

class MockDatabase:
    def __getitem__(self, key):
        return MockCollection()

class Database:
    client = None
    db = None

    @staticmethod
    def connect():
        # If already connected to a real database, return it
        if Database.client and not isinstance(Database.db, MockDatabase):
            return Database.db
            
        try:
            # Set SSL environment variables
            os.environ['SSL_CERT_FILE'] = certifi.where()
            os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())
            
            uri = os.getenv("MONGO_URI", "").strip()
            if not uri:
                print("❌ ERROR: MONGO_URI is empty/missing in environment.")
                Database.db = MockDatabase()
                return Database.db

            # Log a sanitized version of the URI for debugging
            sanitized_uri = uri.split('@')[-1] if '@' in uri else "HIDDEN"
            print(f"🔍 Attempting to connect to MongoDB: ...@{sanitized_uri}")
            
            # Standard TLS Connection
            Database.client = MongoClient(
                uri,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True
            )
            
            # Verify connection immediately
            Database.client.admin.command('ping')
            Database.db = Database.client.get_database()
            print("✅ Successfully connected to MongoDB!")
                
        except Exception as e:
            print(f"❌ MongoDB Connection Failed: {str(e)}")
            import traceback
            traceback.print_exc()
            Database.db = MockDatabase()
            
        return Database.db

class DatabaseProxy:
    def __getitem__(self, key):
        return Database.connect()[key]

    def __getattr__(self, name):
        return getattr(Database.connect(), name)

# This proxy ensures all modules always use the latest connection state
db = DatabaseProxy()
