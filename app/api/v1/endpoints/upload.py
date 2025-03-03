import getpass
from uuid import uuid4
from fastapi import APIRouter, Depends, Query, HTTPException
from langchain_core.documents import Document
from sqlalchemy.orm import Session
from app.services.extract import extract_price_nlp
from app.models import Product
from app.db.database import get_db
from app.config import vector_store  # Import cấu hình từ config.py

# load_dotenv()
# # Lấy đường dẫn token từ biến môi trường
# TOKEN_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "token.json")

# # Đặt biến GOOGLE_APPLICATION_CREDENTIALS
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = TOKEN_PATH
# pinecone_api_key = os.environ.get("PINECONE_API_KEY")
# if not os.environ.get("OPENAI_API_KEY"):
#   os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")
# pc = Pinecone(api_key=pinecone_api_key)

# index_name = "ultraseekdemov1"
# index = pc.Index(index_name)
# embeddings=GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# vector_store = PineconeVectorStore(index=index, embedding=embeddings)

router = APIRouter()


@router.get("/search/")
def search_products(
    query: str = Query(..., description="Truy vấn tìm kiếm sản phẩm"), top_k: int = 2
):
    """
    API tìm kiếm sản phẩm dựa trên mô hình vector embeddings và lọc theo giá nếu có.
    """
    try:
        min_price, max_price = extract_price_nlp(query)

        # Tạo bộ lọc dựa trên giá
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price

        # Tạo filter cho Pinecone
        filter_conditions = {"price": price_filter} if price_filter else None
        print(filter_conditions)

        results = vector_store.similarity_search(
            query, k=top_k, filter=filter_conditions
        )

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tìm kiếm: {str(e)}")


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

    for product in products:
        product_id = str(product.id)

        # Bỏ qua sản phẩm không có mô tả
        if not product.description:
            continue

        documents.append(
            Document(
                page_content=f"{product.description}",
                metadata={
                    "name": product.name,
                    "short_description": product.short_description,
                    "price": str(product.price),
                    "quantity_sold": str(product.quantity_sold),
                },
            )
        )
        uuids.append(product_id)

    # Nhúng dữ liệu vào Pinecone
    if documents:
        vector_store.add_documents(documents=documents, ids=uuids)

    return {
        "message": "Nhúng dữ liệu sản phẩm thành công!",
        "total_embedded": len(documents),
    }
