
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal
from .services import get_client_debt_by_rut

app = FastAPI()

class DeudaRequest(BaseModel):
    rut_cliente: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/consultar-deuda")
def consultar_deuda(request: DeudaRequest, db: Session = Depends(get_db)):
    data = get_client_debt_by_rut(db, request.rut_cliente)
    if not data:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return data
