import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

role = os.environ.get("DATABASE_ROLE")
password = os.environ.get("DATABASE_PASSWORD")
host = os.environ.get("DATABASE_HOST")
name = os.environ.get("DATABASE_NAME")
if host is None or password is None or role is None or name is None:
    SQLALCHEMY_DATABASE_URL = "postgresql://root@127.0.0.1/womenProtection"
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{role}:{password}@{host}/{name}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
