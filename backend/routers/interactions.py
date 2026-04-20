from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import Interaction, HCP
from schemas import InteractionResponse, InteractionFormState
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/interactions", tags=["interactions"])

@router.get("", response_model=List[InteractionResponse])
def list_interactions(db: Session = Depends(get_db)):
    results = (
        db.query(Interaction, HCP.name.label("hcp_name"))
        .join(HCP, Interaction.hcp_id == HCP.id, isouter=True)
        .order_by(desc(Interaction.interaction_date))
        .all()
    )
    
    interactions = []
    for interaction_obj, hcp_name in results:
        # Use model_validate for Pydantic v2
        resp = InteractionResponse.model_validate(interaction_obj)
        resp.hcp_name = hcp_name
        interactions.append(resp)
    return interactions

@router.post("")
def save_interaction(data: InteractionFormState, db: Session = Depends(get_db)):
    # If interaction_id exists, we might want to update, but PDF says POST to interactions saves current form
    # Usually this is for final confirmation or manual logging
    try:
        interaction_date = datetime.strptime(data.date, "%Y-%m-%d").date() if data.date else datetime.now().date()
        
        interaction = Interaction(
            hcp_id=data.hcp_id,
            interaction_date=interaction_date,
            mode=data.mode,
            product_discussed=data.product_discussed,
            sentiment=data.sentiment,
            materials_shared=data.materials_shared,
            key_topics=data.key_topics,
            outcome=data.outcome,
            follow_up_date=datetime.strptime(data.follow_up_date, "%Y-%m-%d").date() if data.follow_up_date else None,
            follow_up_notes=data.follow_up_notes,
            status=data.status or "completed"
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return {"id": interaction.id, "message": "Interaction saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{interaction_id}")
def update_interaction(interaction_id: int, data: InteractionFormState, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    try:
        interaction.mode = data.mode
        interaction.product_discussed = data.product_discussed
        interaction.sentiment = data.sentiment
        interaction.materials_shared = data.materials_shared
        interaction.key_topics = data.key_topics
        interaction.outcome = data.outcome
        interaction.follow_up_notes = data.follow_up_notes
        if data.date:
            interaction.interaction_date = datetime.strptime(data.date, "%Y-%m-%d").date()
        
        db.commit()
        return {"message": "Updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    db.delete(interaction)
    db.commit()
    return {"message": "Deleted successfully"}
