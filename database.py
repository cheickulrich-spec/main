import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

DB_URL = os.environ.get("PHARMACY_DB_URL", "sqlite:///pharmacy.db")

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = scoped_session(
	sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
)
Base = declarative_base()


def get_db_session():
	"""Return a new SQLAlchemy session; caller is responsible for closing it."""
	return SessionLocal()