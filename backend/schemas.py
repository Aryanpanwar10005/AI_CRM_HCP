from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date as date_type

class InteractionFormState(BaseModel):
    interaction_id:    Optional[int] = None
    hcp_name:          Optional[str] = None
    hcp_id:            Optional[int] = None
    date:              Optional[str] = None
    mode:              Optional[str] = None
    product_discussed: Optional[str] = None
    sentiment:         Optional[str] = None
    materials_shared:  Optional[str] = None
    key_topics:        Optional[str] = None
    outcome:           Optional[str] = None
    follow_up_date:    Optional[str] = None
    follow_up_notes:   Optional[str] = None
    status:            Optional[str] = None

class ChatMessage(BaseModel):
    message:                str
    session_id:             Optional[str] = None
    current_form_state:     Optional[InteractionFormState] = None
    current_interaction_id: Optional[int] = None

class ChatResponse(BaseModel):
    reply:          str
    actions_taken:  Optional[List[str]] = []
    interaction_id: Optional[int] = None
    form_updates:   Optional[Dict[str, Any]] = {}

class HCPResponse(BaseModel):
    id: int
    name: str
    specialty: Optional[str]
    hospital: Optional[str]
    city: Optional[str]
    class Config:
        from_attributes = True

class InteractionResponse(BaseModel):
    id: int
    hcp_id: Optional[int] = None
    hcp_name: Optional[str] = None
    interaction_date: date_type
    mode: Optional[str] = None
    product_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    status: Optional[str] = None
    class Config:
        from_attributes = True
