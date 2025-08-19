from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Product(Base):
	__tablename__ = "products"

	id = Column(Integer, primary_key=True)
	name = Column(String(200), nullable=False)
	description = Column(Text, default="")
	category = Column(String(100), default="General")
	price = Column(Float, nullable=False)
	stock = Column(Integer, nullable=False, default=0)
	created_at = Column(DateTime, default=datetime.utcnow)

	def __repr__(self) -> str:
		return f"<Product id={self.id} name={self.name!r} stock={self.stock}>"


class Order(Base):
	__tablename__ = "orders"

	id = Column(Integer, primary_key=True)
	customer_name = Column(String(200), nullable=False)
	customer_phone = Column(String(50), nullable=False)
	customer_address = Column(Text, nullable=False)
	total_amount = Column(Float, nullable=False, default=0.0)
	created_at = Column(DateTime, default=datetime.utcnow)

	items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

	def __repr__(self) -> str:
		return f"<Order id={self.id} total={self.total_amount}>"


class OrderItem(Base):
	__tablename__ = "order_items"

	id = Column(Integer, primary_key=True)
	order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
	product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
	quantity = Column(Integer, nullable=False)
	unit_price = Column(Float, nullable=False)
	subtotal = Column(Float, nullable=False)

	order = relationship("Order", back_populates="items")
	product = relationship("Product")

	def __repr__(self) -> str:
		return f"<OrderItem order_id={self.order_id} product_id={self.product_id} qty={self.quantity}>"