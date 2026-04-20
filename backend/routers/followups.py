from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Followup
from datetime import date

router = APIRouter(prefix="/api/followups", tags=["followups"])

@router.get("")
def list_followups(db: Session = Depends(get_db)):
    return db.query(Followup).filter(Followup.status == "pending", Followup.due_date >= date.today()).all()

@router.put("/{id}/complete")
def complete_followup(id: int, db: Session = Depends(get_db)):
    fup = db.query(Followup).filter(Followup.id == id).first()
    if not fup:
        raise HTTPException(status_code=404, detail="Followup not found")
    fup.status = "completed"
    db.commit()
    return {"message": "Followup marked as completed"}
