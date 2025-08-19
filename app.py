import os
from functools import wraps
from typing import Dict

from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import select

from database import Base, engine, SessionLocal
from models import Product, Order, OrderItem


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
ADMIN_PASSWORD = os.environ.get("PHARMACY_ADMIN_PASSWORD", "admin123")


# Ensure tables exist
Base.metadata.create_all(bind=engine)


def get_cart() -> Dict[str, int]:
	cart = session.get("cart")
	if not cart:
		cart = {}
		session["cart"] = cart
	return cart


def cart_item_count() -> int:
	cart = get_cart()
	return sum(cart.values())


@app.context_processor
def inject_globals():
	return {"cart_count": cart_item_count()}


@app.route("/")
def index():
	query = request.args.get("q", "").strip()
	category = request.args.get("category", "").strip()

	db = SessionLocal()
	try:
		stmt = select(Product)
		if query:
			like_query = f"%{query}%"
			stmt = stmt.where(Product.name.ilike(like_query))
		if category:
			stmt = stmt.where(Product.category == category)
		products = db.execute(stmt).scalars().all()

		# Build category list
		categories = db.query(Product.category).distinct().all()
		categories = [c[0] for c in categories]
	finally:
		db.close()

	return render_template("index.html", products=products, query=query, category=category, categories=categories)


@app.route("/product/<int:product_id>")
def product_detail(product_id: int):
	db = SessionLocal()
	try:
		product = db.get(Product, product_id)
		if not product:
			flash("Product not found", "error")
			return redirect(url_for("index"))
	finally:
		db.close()
	return render_template("product_detail.html", product=product)


@app.post("/cart/add/<int:product_id>")
def add_to_cart(product_id: int):
	quantity = int(request.form.get("quantity", 1))
	if quantity <= 0:
		flash("Quantity must be positive", "error")
		return redirect(request.referrer or url_for("index"))

	db = SessionLocal()
	try:
		product = db.get(Product, product_id)
		if not product:
			flash("Product not found", "error")
			return redirect(url_for("index"))
		if product.stock <= 0:
			flash("Out of stock", "error")
			return redirect(url_for("product_detail", product_id=product_id))
	finally:
		db.close()

	cart = get_cart()
	cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
	session.modified = True
	flash("Added to cart", "success")
	return redirect(request.referrer or url_for("index"))


@app.get("/cart")
def view_cart():
	db = SessionLocal()
	try:
		cart = get_cart()
		product_ids = [int(pid) for pid in cart.keys()]
		products = []
		subtotal = 0.0
		if product_ids:
			stmt = select(Product).where(Product.id.in_(product_ids))
			products = db.execute(stmt).scalars().all()
			for product in products:
				qty = cart.get(str(product.id), 0)
				subtotal += product.price * qty
	finally:
		db.close()
	return render_template("cart.html", products=products, cart=cart, subtotal=subtotal)


@app.post("/cart/update")
def update_cart():
	cart = get_cart()
	updates = request.form
	changed = False
	for key, value in updates.items():
		if key.startswith("qty_"):
			pid = key.split("_", 1)[1]
			try:
				qty = int(value)
			except ValueError:
				qty = cart.get(pid, 0)
			if qty <= 0:
				if pid in cart:
					del cart[pid]
					changed = True
			else:
				if cart.get(pid) != qty:
					cart[pid] = qty
					changed = True
	if changed:
		session.modified = True
		flash("Cart updated", "success")
	return redirect(url_for("view_cart"))


@app.post("/cart/remove/<int:product_id>")
def remove_from_cart(product_id: int):
	cart = get_cart()
	pid = str(product_id)
	if pid in cart:
		del cart[pid]
		session.modified = True
		flash("Item removed", "success")
	return redirect(url_for("view_cart"))


@app.get("/checkout")
def checkout():
	cart = get_cart()
	if not cart:
		flash("Your cart is empty", "error")
		return redirect(url_for("index"))
	return render_template("checkout.html")


@app.post("/checkout")
def place_order():
	cart = get_cart()
	if not cart:
		flash("Your cart is empty", "error")
		return redirect(url_for("index"))

	name = request.form.get("name", "").strip()
	phone = request.form.get("phone", "").strip()
	address = request.form.get("address", "").strip()

	if not name or not phone or not address:
		flash("All fields are required", "error")
		return redirect(url_for("checkout"))

	db = SessionLocal()
	try:
		product_ids = [int(pid) for pid in cart.keys()]
		stmt = select(Product).where(Product.id.in_(product_ids))
		products = {p.id: p for p in db.execute(stmt).scalars().all()}

		# Validate stock
		for pid_str, qty in cart.items():
			pid = int(pid_str)
			product = products.get(pid)
			if not product or product.stock < qty:
				flash(f"Insufficient stock for {product.name if product else 'unknown product'}", "error")
				return redirect(url_for("view_cart"))

		# Create order
		order = Order(customer_name=name, customer_phone=phone, customer_address=address, total_amount=0.0)
		db.add(order)
		db.flush()

		total = 0.0
		for pid_str, qty in cart.items():
			pid = int(pid_str)
			product = products[pid]
			line_total = product.price * qty
			total += line_total
			item = OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=product.price, subtotal=line_total)
			db.add(item)
			product.stock -= qty

		order.total_amount = total
		db.commit()

		session["cart"] = {}
		session.modified = True
		return redirect(url_for("order_success", order_id=order.id))
	except Exception:
		db.rollback()
		flash("Failed to place order", "error")
		raise
	finally:
		db.close()


@app.get("/order/success/<int:order_id>")
def order_success(order_id: int):
	return render_template("order_success.html", order_id=order_id)


# -------------------- Admin --------------------

def require_admin(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		if not session.get("admin_authenticated"):
			flash("Admin login required", "error")
			return redirect(url_for("admin_login"))
		return f(*args, **kwargs)

	return wrapper


@app.get("/admin/login")
def admin_login():
	return render_template("admin/login.html")


@app.post("/admin/login")
def admin_login_post():
	password = request.form.get("password", "")
	if password == ADMIN_PASSWORD:
		session["admin_authenticated"] = True
		flash("Logged in as admin", "success")
		return redirect(url_for("admin_products"))
	flash("Invalid password", "error")
	return redirect(url_for("admin_login"))


@app.post("/admin/logout")
@require_admin
def admin_logout():
	session.pop("admin_authenticated", None)
	flash("Logged out", "success")
	return redirect(url_for("index"))


@app.get("/admin/products")
@require_admin
def admin_products():
	db = SessionLocal()
	try:
		products = db.execute(select(Product)).scalars().all()
	finally:
		db.close()
	return render_template("admin/products.html", products=products)


@app.get("/admin/products/new")
@require_admin
def admin_product_new():
	return render_template("admin/product_form.html", product=None)


@app.post("/admin/products/new")
@require_admin
def admin_product_new_post():
	name = request.form.get("name", "").strip()
	description = request.form.get("description", "").strip()
	category = request.form.get("category", "General").strip() or "General"
	price = float(request.form.get("price", 0) or 0)
	stock = int(request.form.get("stock", 0) or 0)

	if not name or price < 0 or stock < 0:
		flash("Invalid product data", "error")
		return redirect(url_for("admin_product_new"))

	db = SessionLocal()
	try:
		product = Product(name=name, description=description, category=category, price=price, stock=stock)
		db.add(product)
		db.commit()
		flash("Product created", "success")
	finally:
		db.close()
	return redirect(url_for("admin_products"))


@app.get("/admin/products/<int:product_id>/edit")
@require_admin
def admin_product_edit(product_id: int):
	db = SessionLocal()
	try:
		product = db.get(Product, product_id)
		if not product:
			flash("Product not found", "error")
			return redirect(url_for("admin_products"))
	finally:
		db.close()
	return render_template("admin/product_form.html", product=product)


@app.post("/admin/products/<int:product_id>/edit")
@require_admin
def admin_product_edit_post(product_id: int):
	name = request.form.get("name", "").strip()
	description = request.form.get("description", "").strip()
	category = request.form.get("category", "General").strip() or "General"
	price = float(request.form.get("price", 0) or 0)
	stock = int(request.form.get("stock", 0) or 0)

	db = SessionLocal()
	try:
		product = db.get(Product, product_id)
		if not product:
			flash("Product not found", "error")
			return redirect(url_for("admin_products"))
		if not name or price < 0 or stock < 0:
			flash("Invalid product data", "error")
			return redirect(url_for("admin_product_edit", product_id=product_id))
		product.name = name
		product.description = description
		product.category = category
		product.price = price
		product.stock = stock
		db.commit()
		flash("Product updated", "success")
	finally:
		db.close()
	return redirect(url_for("admin_products"))


@app.post("/admin/products/<int:product_id>/delete")
@require_admin
def admin_product_delete(product_id: int):
	db = SessionLocal()
	try:
		product = db.get(Product, product_id)
		if product:
			db.delete(product)
			db.commit()
			flash("Product deleted", "success")
	finally:
		db.close()
	return redirect(url_for("admin_products"))


if __name__ == "__main__":
	host = os.environ.get("HOST", "0.0.0.0")
	port = int(os.environ.get("PORT", "5000"))
	app.run(host=host, port=port, debug=True)