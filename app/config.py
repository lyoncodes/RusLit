import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Environment variables
DATABASE_URI = os.environ.get("DATABASE_URI")
SECRET_KEY = os.environ.get("SECRET_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_4O_ENDPOINT = os.environ.get("OPENAI_4O_ENDPOINT")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_BOOKS_ENDPOINT = os.environ.get("GOOGLE_BOOKS_ENDPOINT")
PW_ENCODE = os.environ.get("PW_ENCODE")
PW_HASH_METHOD = os.environ.get("PW_HASH_METHOD")
IA_BOOKS_COLLECTION = os.environ.get("IA_BOOKS")
GOOGLE_CONSUMER_KEY = os.environ.get("GOOGLE_CONSUMER_KEY")
GOOGLE_CONSUMER_SECRET = os.environ.get("GOOGLE_CONSUMER_SECRET")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_BASE_URL = os.environ.get("GOOGLE_BASE_URL")
GOOGLE_ACCESS_TOKEN_URL = os.environ.get("GOOGLE_ACCESS_TOKEN_URL")
GOOGLE_AUTH_ENDPOINT = os.environ.get("GOOGLE_AUTH_ENDPOINT")
