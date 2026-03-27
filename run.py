import os
from dotenv import load_dotenv
from app.main import app

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5005))
    app.run(host='0.0.0.0', port=port)
