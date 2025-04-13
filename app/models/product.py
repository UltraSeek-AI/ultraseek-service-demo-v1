from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String, index=True)
    short_description = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    quantity_sold = Column(Integer, default=0)
    images = Column(JSON, nullable=True, default=[])

    category = relationship("Category")
