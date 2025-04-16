
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Reemplaza con tu propia cadena de conexión
DATABASE_URL = "mysql+pymysql://admin:090731Nx@192.168.50.13/splynx"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
