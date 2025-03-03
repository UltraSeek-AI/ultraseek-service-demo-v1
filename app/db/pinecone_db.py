import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load biến môi trường từ file .env
load_dotenv()
# Lấy API key từ biến môi trường
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")

# Khởi tạo Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Tạo index nếu chưa có
index_name = "ultraseekdemo"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # Số chiều của vector embedding (ví dụ: OpenAI text-embedding-ada-002)
        metric="cosine",  # Hoặc "euclidean", "dotproduct"
    )

# Kết nối đến index
index = pc.Index(index_name)
