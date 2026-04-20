from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import HCP
from schemas import HCPResponse
from typing import List

router = APIRouter(prefix="/api/hcps", tags=["hcps"])

@router.get("", response_model=List[HCPResponse])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(HCP).all()

@router.get("/{id}", response_model=HCPResponse)
def get_hcp(id: int, db: Session = Depends(get_db)):
    hcp = db.query(HCP).filter(HCP.id == id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp
