from database import engine, SessionLocal, Base
from models import Product


def seed_products():
	session = SessionLocal()
	try:
		if session.query(Product).count() == 0:
			products = [
				Product(name="Paracetamol 500mg", description="Pain reliever and fever reducer.", category="Analgesic", price=3.99, stock=100),
				Product(name="Ibuprofen 200mg", description="Nonsteroidal anti-inflammatory drug (NSAID).", category="Analgesic", price=5.49, stock=80),
				Product(name="Vitamin C 1000mg", description="Immune support supplement.", category="Vitamins", price=12.99, stock=50),
				Product(name="Cough Syrup", description="Relieves cough and cold symptoms.", category="Cough & Cold", price=8.49, stock=40),
				Product(name="Antacid Tablets", description="Relieves heartburn and indigestion.", category="Digestive", price=6.99, stock=60),
				Product(name="Allergy Relief", description="Antihistamine for allergy symptoms.", category="Allergy", price=7.99, stock=70),
			]
			session.add_all(products)
			session.commit()
			print(f"Seeded {len(products)} products.")
		else:
			print("Products already seeded; skipping.")
	finally:
		session.close()


def main():
	Base.metadata.create_all(bind=engine)
	seed_products()


if __name__ == "__main__":
	main()