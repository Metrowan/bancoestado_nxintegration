# app/local_database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ajusta tus credenciales y nombre de base de datos local
LOCAL_DATABASE_URL = "mysql+mysqlconnector://root:SebeL2024*@localhost/bancoestado_test"

LocalEngine = create_engine(LOCAL_DATABASE_URL)
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=LocalEngine)

LocalBase = declarative_base()
