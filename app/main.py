from fastapi import FastAPI
from app.api.v1.endpoints import upload, product, category

app = FastAPI()

# Đăng ký API
app.include_router(upload.router, prefix="/v1", tags=["upload"])
app.include_router(product.router, prefix="/v1", tags=["products"])
app.include_router(category.router, prefix="/v1", tags=["categories"])
