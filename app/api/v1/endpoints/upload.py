import getpass
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, Query, HTTPException
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from app.services.extract import extract_price_nlp
from app.models import Product
from app.db.database import get_db
from app.config import vector_store  # Import cấu hình từ config.py



router = APIRouter()


@router.get("/search/")
def search_products(
    query: str = Query(..., description="Truy vấn tìm kiếm sản phẩm"), 
    top_k: int = 10,  # Tăng top_k để lấy nhiều đoạn hơn
    db: Session = Depends(get_db)
):
    """
    API tìm kiếm sản phẩm dựa trên mô hình vector embeddings và lọc theo giá nếu có.
    """
    try:
        # Trích xuất khoảng giá từ truy vấn người dùng
        min_price, max_price = extract_price_nlp(query)

        # Tạo bộ lọc dựa trên giá
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price

        # Tạo filter cho Pinecone
        filter_conditions = {"price": price_filter} if price_filter else None
        print(f"Filter conditions: {filter_conditions}")

        # Lấy các đoạn mô tả liên quan từ Pinecone (tăng top_k để có dữ liệu tốt hơn)
        retrieved_chunks = vector_store.similarity_search(
            query, k=top_k, filter=filter_conditions
        )

        # Nhóm kết quả theo product_id
        product_chunks = {}
        for chunk in retrieved_chunks:
            product_id = chunk.metadata["product_id"]
            if product_id not in product_chunks:
                product_chunks[product_id] = []
            product_chunks[product_id].append(chunk)

        # Lấy danh sách các sản phẩm duy nhất từ kết quả tìm kiếm
        unique_product_ids = list(product_chunks.keys())

        # Truy vấn thông tin sản phẩm từ database
        products_data = _get_product_by_id(unique_product_ids, db)

        # Gộp thông tin sản phẩm vào kết quả
        results = []
        for product_id, chunks in product_chunks.items():
            product_info = next((p for p in products_data if p["id"] == product_id), None)
            if product_info:
                combined_content = " ".join([chunk.page_content for chunk in chunks])  # Ghép mô tả
                results.append({
                    "id": product_id,
                    "name": product_info["name"],
                    "short_description": product_info["short_description"],
                    "price": product_info["price"],
                    "quantity_sold": product_info["quantity_sold"],
                    "images": product_info["images"],
                    "description": combined_content,  # Gộp lại mô tả đầy đủ
                })

        return {"results": results[:1]}  # Chỉ lấy 2 sản phẩm liên quan nhất
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tìm kiếm: {str(e)}")


def _get_product_by_id(product_ids: List[str], db: Session):
    """
    Truy vấn thông tin sản phẩm từ danh sách product_id
    """
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()

    return [
        {
            "id": str(product.id),
            "name": product.name,
            "short_description": product.short_description,
            "price": str(product.price),
            "quantity_sold": str(product.quantity_sold),
            "images": product.images,  # Giả sử lưu dạng JSON/List
        }
        for product in products
    ]

@router.post("/embed-category/{category_id}")
async def embed_category_products(category_id: int, db: Session = Depends(get_db)):
    """
    API lấy danh sách sản phẩm theo category_id và nhúng vào Pinecone nếu chưa tồn tại.
    """
    # Truy vấn tất cả sản phẩm theo category_id
    products = db.query(Product).filter(Product.category_id == category_id).all()

    if not products:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy sản phẩm trong danh mục này."
        )

    # Chỉ lấy những sản phẩm chưa tồn tại trong Pinecone
    documents = []
    uuids = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,  # Chia description thành đoạn 300 ký tự
        chunk_overlap=50,  # Cho phép trùng lặp 50 ký tự để giữ ngữ cảnh
    )

    for product in products:
        product_id = str(product.id)

        # Bỏ qua sản phẩm không có mô tả
        if not product.description:
            continue
        
        # Chia nhỏ mô tả sản phẩm
        chunks = text_splitter.split_text(product.description)

        for idx, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "product_id": product_id,
                        "name": product.name,
                        "short_description": product.short_description,
                        "price": str(product.price),
                        "quantity_sold": str(product.quantity_sold),
                        "chunk_index": idx  # Đánh số thứ tự từng đoạn
                    },
                )
            )
            uuids.append(f"{product_id}_{idx}")  # Mỗi đoạn có ID riêng để không bị ghi đè


    # Nhúng dữ liệu vào Pinecone
    if documents:
        vector_store.add_documents(documents=documents, ids=uuids)

    return {
        "message": "Nhúng dữ liệu sản phẩm thành công!",
        "total_embedded": len(documents),
    }
