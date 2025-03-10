from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import upload, product, category

app = FastAPI()

app.add_middleware(middleware_class=CORSMiddleware, allow_origins=["http://localhost:5173","http://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# Đăng ký API
app.include_router(upload.router, prefix="/v1", tags=["upload"])
app.include_router(product.router, prefix="/v1", tags=["products"])
app.include_router(category.router, prefix="/v1", tags=["categories"])
