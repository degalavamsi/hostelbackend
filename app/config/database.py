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
        if not Database.client:
            # Set SSL environment variables
            os.environ['SSL_CERT_FILE'] = certifi.where()
            os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())
            
            try:
                uri = os.getenv("MONGO_URI", "").strip()
                if not uri:
                    print("❌ MISSING MONGO_URI: Deployment will fail without a database connection.")
                    Database.db = MockDatabase()
                    return Database.db

                print(f"🔍 Connecting to MongoDB Atlas...")
                
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
                print("💡 HINT: If on Vercel, ensure you have whitelisted 0.0.0.0/0 in MongoDB Atlas.")
                Database.db = MockDatabase()
                
        return Database.db

# Initialize database
db = Database.connect()
