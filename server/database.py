import os

from sqlalchemy import URL, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

pg_username = os.environ.get('POSTGRES_USER', 'postgres')
pg_password = os.environ.get('POSTGRES_PASS', None)
pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
pg_database = os.environ.get('POSTGRES_DB', 'restaurants')

url_object = URL.create(
    "postgresql+psycopg2",
    username=pg_username,
    password=pg_password,
    host=pg_host,
    database=pg_database,
)

engine = create_engine(
    url_object
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
