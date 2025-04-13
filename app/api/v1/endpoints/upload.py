import getpass
from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, Query, HTTPException,FastAPI
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session
from app.services.extract import extract_price_nlp
from app.models import Product
from app.db.database import get_db
from app.config import vector_store  # Import cấu hình từ config.py
from openai import OpenAI
import json


router = APIRouter()

client = OpenAI(api_key="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")
def generate_sql_search_query(user_query: str):
    """
    Gửi truy vấn người dùng đến ChatGPT để tạo câu lệnh SQL phù hợp.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý AI giúp tạo câu SQL tìm kiếm sản phẩm."
                    " Hãy phân tích truy vấn của người dùng để xác định từ khóa tìm kiếm và khoảng giá (nếu có)."
                    " Trả về đầu ra dưới dạng JSON với các trường:"
                    " - query (chuỗi): từ khóa tìm kiếm"
                    " - min_price (số hoặc null): giá tối thiểu nếu có"
                    " - max_price (số hoặc null): giá tối đa nếu có"
                    "\n\nCách xử lý:"
                    " - Nếu chỉ có giá tối thiểu, đặt max_price = null."
                    " - Nếu chỉ có giá tối đa, đặt min_price = null."
                    " - Nếu không có thông tin giá, đặt cả hai giá trị null."
                    " - Nếu khoảng giá không chính xác, cố gắng suy luận dựa trên ngữ cảnh."
                    "\n\n🔹 Ví dụ:\n"
                    "1️⃣ Người dùng: 'Tìm laptop gaming dưới 20 triệu'"
                    "  → Kết quả: { 'query': 'laptop gaming', 'min_price': null, 'max_price': 20000000 }\n"
                    "2️⃣ Người dùng: 'Điện thoại từ 5 triệu đến 10 triệu'"
                    "  → Kết quả: { 'query': 'điện thoại', 'min_price': 5000000, 'max_price': 10000000 }\n"
                    "3️⃣ Người dùng: 'Mua giày thể thao'"
                    "  → Kết quả: { 'query': 'giày thể thao', 'min_price': null, 'max_price': null }\n"
                    "4️⃣ Người dùng: 'Laptop trên 15 triệu'"
                    "  → Kết quả: { 'query': 'laptop', 'min_price': 15000000, 'max_price': null }\n"
                    "5️⃣ Người dùng: 'Điện thoại không quá 8 triệu'"
                    "  → Kết quả: { 'query': 'điện thoại', 'min_price': null, 'max_price': 8000000 }\n"
                    "6️⃣ Người dùng: 'Macbook giá từ 20 triệu'"
                    "  → Kết quả: { 'query': 'Macbook', 'min_price': 20000000, 'max_price': null }\n"
                    "7️⃣ Người dùng: 'Tìm tivi khoảng 10 đến 15 triệu'"
                    "  → Kết quả: { 'query': 'tivi', 'min_price': 10000000, 'max_price': 15000000 }\n"
                    "8️⃣ Người dùng: 'Mua tai nghe khoảng 2 triệu'"
                    "  → Kết quả: { 'query': 'tai nghe', 'min_price': 1800000, 'max_price': 2200000 }\n"
                    "9️⃣ Người dùng: 'Bàn phím cơ tầm 1 triệu rưỡi'"
                    "  → Kết quả: { 'query': 'bàn phím cơ', 'min_price': 1350000, 'max_price': 1650000 }\n"
                    "🔟 Người dùng: 'Tủ lạnh từ 5 triệu đến dưới 12 triệu'"
                    "  → Kết quả: { 'query': 'tủ lạnh', 'min_price': 5000000, 'max_price': 11999999 }\n"
                    "\n📌 Lưu ý:\n"
                    " - 'Dưới X triệu' hoặc 'Không quá X triệu' → { 'min_price': null, 'max_price': X }\n"
                    " - 'Trên X triệu' hoặc 'Từ X triệu' → { 'min_price': X, 'max_price': null }\n"
                    " - 'Khoảng X triệu' hoặc 'Tầm X triệu' → khoảng ±10% quanh giá trị đó."
                )
            },
            {"role": "user", "content": f"Tạo câu lệnh SQL tìm kiếm sản phẩm phù hợp với truy vấn: '{user_query}'"}
        ],

        functions=[
            {
                "name": "search_by_sql",
                "description": "Tạo câu SQL tìm kiếm sản phẩm theo từ khóa và giá cả.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Từ khóa tìm kiếm."},
                        "min_price": {"type": "number", "description": "Giá tối thiểu (nếu có)."},
                        "max_price": {"type": "number", "description": "Giá tối đa (nếu có)."}
                    },
                    "required": ["query"]
                }
            }
        ]
    )
    
    print(response)
    
    if response.choices[0].message.function_call:
        # Parse JSON từ function_call.arguments
        sql_params = json.loads(response.choices[0].message.function_call.arguments)
        return sql_params
    else:
        return None  # Tránh lỗi nếu không có function_call

def _search_by_sql(query: str, min_price: float = None, max_price: float = None, db: Session = None):
    """
    Tìm kiếm sản phẩm bằng SQL theo từ khóa và khoảng giá.
    """
    products_query = db.query(Product)

    search_terms = query.split()
    for term in search_terms:
        products_query = products_query.filter(
            (Product.name.ilike(f"%{term}%")) |
            (Product.short_description.ilike(f"%{term}%")) |
            (Product.description.ilike(f"%{term}%"))
        )

    if min_price is not None:
        products_query = products_query.filter(Product.price >= min_price)
    if max_price is not None:
        products_query = products_query.filter(Product.price <= max_price)

    products = products_query.all()
    return [
        {
            "id": str(product.id),
            "name": product.name,
            "short_description": product.short_description,
            "price": str(product.price),
            "quantity_sold": str(product.quantity_sold),
            "images": product.images,
            "description": product.description,
            "source": "sql"
        }
        for product in products
    ]

@router.get("/search/")
def search_products(
    query: str = Query(..., description="Truy vấn tìm kiếm sản phẩm"), 
    top_k: int = 10,
    db: Session = Depends(get_db)
):
    """
    API tìm kiếm sản phẩm kết hợp SQL và vector embeddings.
    """
    try:
        # ChatGPT tạo truy vấn SQL phù hợp
        sql_params = generate_sql_search_query(query)

        # Gọi hàm tìm kiếm SQL
        sql_results = _search_by_sql(sql_params["query"], sql_params.get("min_price"), sql_params.get("max_price"), db)

        return {"results": sql_results[:top_k]}  # Giới hạn top_k kết quả

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
