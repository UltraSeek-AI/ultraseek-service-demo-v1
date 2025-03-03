import os
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-west1-gcp")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = "ultraseekdemo"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
