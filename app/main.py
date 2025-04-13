from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import upload, product, category, chat, auth
import os

os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "pr-essential-incense-25"

app = FastAPI()

app.add_middleware(middleware_class=CORSMiddleware, allow_origins=["http://localhost:5173","http://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# Đăng ký API
app.include_router(upload.router, prefix="/v1", tags=["upload"])
app.include_router(product.router, prefix="/v1", tags=["products"])
app.include_router(category.router, prefix="/v1", tags=["categories"])
app.include_router(chat.router, prefix="/v1", tags=["chats"])
app.include_router(auth.router, prefix="/v1", tags=["auth"])