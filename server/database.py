from sqlalchemy import URL, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

url_object = URL.create(
    "postgresql+psycopg2",
    username="rahul",
    password="Welcome!",
    host="localhost",
    database="restaurants",
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
