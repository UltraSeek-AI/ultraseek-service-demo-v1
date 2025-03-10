import json
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import csv
from app.db.database import get_db
from app.models import Product, Category

router = APIRouter()


@router.post("/products/import/")
def import_products(
    category_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    # Kiểm tra xem category có tồn tại không
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    products = []
    with file.file as f:
        reader = csv.DictReader(f.read().decode("utf-8").splitlines())
        for row in reader:
            images_data = eval(row["product_images"])  # Chuyển chuỗi thành list (cẩn thận nếu dữ liệu không tin cậy)
            if images_data and isinstance(images_data, list):
                first_image_url = images_data[0].get("base_url", None)
            else:
                first_image_url = None
            
            product = Product(
                category_id=category_id,
                short_description=row["product_short_description"],
                description=row["product_description"],
                name=row["product_name"],
                price=float(row["product_price"]),
                quantity_sold=int(row["product_quantity_sold"]),
                images=first_image_url if first_image_url else None,
            )
            products.append(product)

    db.add_all(products)
    db.commit()
    return {"message": "Products imported successfully", "count": len(products)}


@router.delete("/products/category/{category_id}")
def delete_products_by_category(category_id: int, db: Session = Depends(get_db)):
    db.query(Product).filter(Product.category_id == category_id).delete()
    db.commit()
    return {"message": "Products deleted successfully"}
