# src/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.config import get_database_url

engine = create_engine(get_database_url(), echo=False)
Session = sessionmaker(bind=engine)