
from typing import List, Optional
import json
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.models import Product
from app.models.chat_history import ChatHistory
from app.db.database import get_db
from openai import OpenAI
from langsmith import traceable
from app.config import vector_store
import uuid


import uuid

router = APIRouter()
# vector_store = PineconeVectorStore(index=index, embedding=embeddings)

client = OpenAI(api_key="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")

def generate_search_params(user_query: str) -> dict:
    """
    Phân tích truy vấn người dùng để xác định phương pháp tìm kiếm (RAG hoặc SQL).
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        'Bạn là trợ lý AI phân tích truy vấn tìm kiếm sản phẩm để chọn phương pháp tìm kiếm: RAG (dựa trên ngữ cảnh) hoặc SQL (dựa trên giá). Phân tích truy vấn và trả về JSON với các trường:\n'
                        '- method: "rag" (nếu không có giá) hoặc "sql" (nếu có giá).\n'
                        '- query: Từ khóa ngữ cảnh (chuỗi, loại bỏ từ liên quan đến giá, rỗng nếu không có ngữ cảnh).\n'
                        '- min_price: Giá tối thiểu (số hoặc null).\n'
                        '- max_price: Giá tối đa (số hoặc null).\n\n'
                        '**Hướng dẫn**:\n'
                        '1. Nếu truy vấn chỉ chứa ngữ cảnh (không có giá):\n'
                        '   - method = "rag", query = toàn bộ truy vấn, min_price = null, max_price = null.\n'
                        '2. Nếu truy vấn có giá (dù kèm ngữ cảnh):\n'
                        '   - method = "sql", query = ngữ cảnh (loại bỏ từ liên quan đến giá), min_price/max_price dựa trên giá.\n'
                        '3. Nếu chỉ có giá, không có ngữ cảnh:\n'
                        '   - method = "sql", query = "", min_price/max_price dựa trên giá.\n'
                        '4. Nếu truy vấn mơ hồ:\n'
                        '   - method = "rag", query = toàn bộ truy vấn, min_price = null, max_price = null.\n\n'
                        '**Quy tắc giá** (đơn vị: triệu đồng, chuyển thành số, ví dụ: 1 triệu = 1000000):\n'
                        '- "Dưới X triệu" hoặc "Không quá X triệu" → min_price = null, max_price = X * 1000000.\n'
                        '- "Trên X triệu" hoặc "Từ X triệu" → min_price = X * 1000000, max_price = null.\n'
                        '- "Từ X triệu đến Y triệu" → min_price = X * 1000000, max_price = Y * 1000000.\n'
                        '- "Khoảng X triệu" hoặc "Tầm X triệu" → min_price = X * 0.9 * 1000000, max_price = X * 1.1 * 1000000.\n'
                        '- Nếu giá không rõ (e.g., "rẻ", "đắt"), đặt min_price = null, max_price = null.\n\n'
                        '**Lưu ý**:\n'
                        '- Loại bỏ từ liên quan đến giá (e.g., "dưới", "khoảng") khỏi query.\n'
                        '- min_price và max_price phải là số hoặc null, không phải chuỗi.\n'
                        '- Nếu không chắc chắn, ưu tiên method = "rag" với query là toàn bộ truy vấn.\n\n'
                        '**Ví dụ**:\n'
                        '1. "Laptop gaming mạnh mẽ" → {"method": "rag", "query": "laptop gaming mạnh mẽ", "min_price": null, "max_price": null}\n'
                        '2. "Điện thoại dưới 10 triệu" → {"method": "sql", "query": "điện thoại", "min_price": null, "max_price": 10000000}\n'
                        '3. "Laptop từ 15 triệu đến 25 triệu" → {"method": "sql", "query": "laptop", "min_price": 15000000, "max_price": 25000000}\n'
                        '4. "Tai nghe khoảng 2 triệu" → {"method": "sql", "query": "tai nghe", "min_price": 1800000, "max_price": 2200000}\n'
                        '5. "Tìm sản phẩm rẻ" → {"method": "rag", "query": "tìm sản phẩm rẻ", "min_price": null, "max_price": null}\n\n'
                        f'Phân tích truy vấn: "{user_query}"'
                    )
                }
            ],
            functions=[
                {
                    "name": "search_params",
                    "description": "Xác định phương pháp tìm kiếm sản phẩm.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "enum": ["rag", "sql"],
                                "description": "Phương pháp tìm kiếm."
                            },
                            "query": {
                                "type": "string",
                                "description": "Từ khóa ngữ cảnh."
                            },
                            "min_price": {
                                "type": ["number", "null"],
                                "description": "Giá tối thiểu."
                            },
                            "max_price": {
                                "type": ["number", "null"],
                                "description": "Giá tối đa."
                            }
                        },
                        "required": ["method", "query"]
                    }
                }
            ],
            function_call={"name": "search_params"}
        )

        if response.choices[0].message.function_call:
            return json.loads(response.choices[0].message.function_call.arguments)
        return {
            "method": "rag",
            "query": user_query,
            "min_price": None,
            "max_price": None
        }
    except Exception:
        return {
            "method": "rag",
            "query": user_query,
            "min_price": None,
            "max_price": None
        }

def filter_by_price(products: list, min_price: float = None, max_price: float = None):
    """
    Lọc sản phẩm theo giá.
    """
    filtered_products = products
    if min_price is not None:
        filtered_products = [p for p in filtered_products if float(p["price"]) >= min_price]
    if max_price is not None:
        filtered_products = [p for p in filtered_products if float(p["price"]) <= max_price]
    return filtered_products

def search_by_sql(query: str, min_price: Optional[float], max_price: Optional[float], db: Session, top_k: int) -> dict:
    """
    Tìm kiếm sản phẩm bằng SQL theo từ khóa và khoảng giá.
    """
    products_query = db.query(Product)

    if query.strip():
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

    products = products_query.limit(top_k).all()
    return {
        "results": [
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
    }

def search_by_rag(search_query: str, top_k: int, db: Session) -> dict:
    """
    Tìm kiếm bằng RAG sử dụng vector store.
    """
    try:
        # Lấy các đoạn mô tả liên quan từ Pinecone
        retrieved_chunks = vector_store.similarity_search(search_query, k=top_k * 2)  # Lấy nhiều hơn để đảm bảo đủ kết quả
        
        # Nhóm kết quả theo product_id
        product_chunks = {}
        for chunk in retrieved_chunks:
            product_id = chunk.metadata["product_id"]
            if product_id not in product_chunks:
                product_chunks[product_id] = []
            product_chunks[product_id].append(chunk)

        # Lấy danh sách các sản phẩm duy nhất
        unique_product_ids = list(product_chunks.keys())[:top_k]  # Giới hạn top_k product_id

        # Truy vấn thông tin sản phẩm từ database
        products_data = _get_products_by_ids(unique_product_ids, db)

        return {"results": products_data[:top_k]}  # Đảm bảo trả về tối đa top_k sản phẩm
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tìm kiếm RAG: {str(e)}")
    
def _get_products_by_ids(product_ids: List[str], db: Session) -> List[dict]:
    """
    Truy vấn thông tin sản phẩm từ danh sách product_id.
    """
    if not product_ids:
        return []
    
    products = db.query(Product).filter(Product.id.in_(product_ids)).all()
    return [
        {
            "id": str(product.id),
            "name": product.name,
            "short_description": product.short_description,
            "price": str(product.price),
            "quantity_sold": str(product.quantity_sold),
            "images": product.images,
            "description": product.description,
            "source": "rag"
        }
        for product in products
    ]

@router.get("/chat/")
@traceable
def search_products(
    query: str = Query(..., description="Truy vấn tìm kiếm sản phẩm"),
    top_k: int = Query(5, description="Số lượng sản phẩm tối đa trả về"),
    user_id: int = Query(..., description="ID người dùng"),
    db: Session = Depends(get_db)
):
    """
    API tìm kiếm sản phẩm kết hợp RAG và SQL.
    Lưu lịch sử chat vào bảng chat_histories.
    """
    try:
        # 1️⃣ Kiểm tra thread_id
        last_chat = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.created_at.desc()).first()
        thread_id = last_chat.thread_id if last_chat and last_chat.thread_id else int(uuid.uuid4().int % (10**8))

        # 2️⃣ Phân tích truy vấn
        search_params = generate_search_params(query)
        method = search_params["method"]
        search_query = search_params["query"]
        min_price = search_params["min_price"]
        max_price = search_params["max_price"]

        # 3️⃣ Xử lý tìm kiếm
        results = {"results": []}
        if method == "rag":
            results = search_by_rag(search_query, top_k, db)
        elif method == "sql":
            results = search_by_sql(search_query, min_price, max_price, db, top_k)
        elif method == "combined":
            rag_results = search_by_rag(search_query, top_k * 2, db)
            filtered_results = filter_by_price(rag_results["results"], min_price, max_price)
            results = {"results": filtered_results[:top_k]}

        # 4️⃣ Lưu lịch sử chat
        response_text = json.dumps(results["results"])
        chat_history = ChatHistory(
            user_id=user_id,
            thread_id=thread_id,
            role="human",
            message=query,
            response=response_text
        )
        db.add(chat_history)
        db.commit()

        return {
            "thread_id": thread_id,
            "results": results["results"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tìm kiếm: {str(e)}")

# def save_chat_history(thread_id: str, question: str, answer: str, db: Session = Depends(get_db)) -> Dict:
#     chat_history = ChatHistory(
#         thread_id=thread_id,  # Lưu thread_id
#         question=question,
#         answer=answer
#     )
#     db.add(chat_history)
#     db.commit()
#     db.refresh(chat_history)
    
#     return {
#         "id": str(chat_history.id),
#         "thread_id": chat_history.thread_id,
#         "question": chat_history.question,
#         "answer": chat_history.answer,
#         "created_at": chat_history.created_at
#     }

# def get_recent_chat_history(thread_id: str, limit: int = 10, db: Session = Depends(get_db)) -> List[Dict]:
#     """
#     Lấy lịch sử chat theo thread_id
#     """
#     chat_history = (
#         db.query(ChatHistory)
#         .filter(ChatHistory.thread_id == thread_id)
#         .order_by(ChatHistory.created_at.desc())
#         .limit(limit)
#         .all()
#     )
    
#     return [
#         {
#             "id": str(msg.id),
#             "thread_id": msg.thread_id,
#             "question": msg.question,
#             "answer": msg.answer,
#             "created_at": msg.created_at
#         }
#         for msg in chat_history
#     ]

# async def get_answer_stream(question: str, thread_id: str, db: Session = Depends(get_db)) -> AsyncGenerator[Dict, None]:
#     """
#     Lấy câu trả lời dạng stream và sử dụng lịch sử chat của thread_id
#     """
#     # Khởi tạo agent
#     agent = get_llm_and_agent()
    
#     # Lấy lịch sử chat theo thread_id
#     history = get_recent_chat_history(thread_id, db=db)  
#     chat_history = format_chat_history(history)

#     final_answer = ""

#     async for event in agent.astream_events(
#         {
#             "input": question,
#             "chat_history": chat_history,  # Gửi history vào mô hình
#         },
#         version="v2"
#     ):       
#         kind = event["event"]
#         if kind == "on_chat_model_stream":
#             content = event['data']['chunk'].content
#             if content:
#                 final_answer += content
#                 yield content
    
#     if final_answer:
#         save_chat_history(thread_id, question, final_answer, db=db)  # Lưu lại lịch sử chat