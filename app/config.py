import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load biến môi trường từ file .env
load_dotenv()

# Thiết lập đường dẫn credentials Google Cloud
TOKEN_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "token.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = TOKEN_PATH

# Lấy API key của Pinecone từ biến môi trường
pinecone_api_key = os.getenv("PINECONE_API_KEY")

# Khởi tạo Pinecone
pc = Pinecone(api_key=pinecone_api_key)

# Tên index của Pinecone
INDEX_NAME = "ultraseekdemov1"
index = pc.Index(INDEX_NAME)

# Khởi tạo embeddings model của Google
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Khởi tạo Pinecone Vector Store
vector_store = PineconeVectorStore(index=index, embedding=embeddings)
