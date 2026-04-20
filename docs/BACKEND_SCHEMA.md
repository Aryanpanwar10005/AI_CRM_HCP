# BACKEND_SCHEMA.md - Database Schema, API & LangGraph Agent
## Version 4 - Final - April 19 2026

---

## 1. SQLAlchemy ORM Models (backend/models.py)

ORM = same Python code works for MySQL + PostgreSQL + SQLite.
Only DATABASE_URL in .env needs to change. No raw SQL needed.

```python
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class HCP(Base):
    __tablename__ = "hcps"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(255), nullable=False)
    specialty     = Column(String(255))
    hospital      = Column(String(255))
    city          = Column(String(100))
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    notes         = Column(Text)
    created_at    = Column(DateTime, server_default=func.now())
    updated_at    = Column(DateTime, server_default=func.now(), onupdate=func.now())
    interactions  = relationship("Interaction", back_populates="hcp")

class Interaction(Base):
    __tablename__ = "interactions"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    hcp_id            = Column(Integer, ForeignKey("hcps.id", ondelete="CASCADE"))
    rep_name          = Column(String(255), default="Field Rep")
    interaction_date  = Column(Date, nullable=False)
    mode              = Column(String(50))        # visit|call|email|video
    product_discussed = Column(String(255))
    key_topics        = Column(Text)
    sentiment         = Column(String(50))        # Positive|Neutral|Negative
    materials_shared  = Column(String(255))       # Brochures|Samples|None
    outcome           = Column(String(100))       # interested|not_interested|samples_requested|follow_up_needed
    follow_up_date    = Column(Date)
    follow_up_notes   = Column(Text)
    raw_notes         = Column(Text)              # original NL message from chat
    ai_summary        = Column(Text)              # LLM-generated summary sentence
    entities_json     = Column(JSON)              # full extracted entities dict
    compliance_flag   = Column(String(50))        # compliant|warning|violation
    next_best_action  = Column(Text)              # AI recommendation text
    source            = Column(String(20), default="chat")
    status            = Column(String(50), default="completed")
    created_at        = Column(DateTime, server_default=func.now())
    updated_at        = Column(DateTime, server_default=func.now(), onupdate=func.now())
    hcp               = relationship("HCP", back_populates="interactions")

class Followup(Base):
    __tablename__ = "followups"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True)
    hcp_id         = Column(Integer, ForeignKey("hcps.id", ondelete="CASCADE"), nullable=False)
    due_date       = Column(Date, nullable=False)
    notes          = Column(Text)
    status         = Column(String(50), default="pending")   # pending|completed
    created_at     = Column(DateTime, server_default=func.now())
```

---

## 2. Seed Data (backend/seed.py)

```python
from database import engine, SessionLocal, Base
from models import HCP, Interaction, Followup
from datetime import date

def seed():
    Base.metadata.create_all(bind=engine)   # creates tables if they dont exist
    db = SessionLocal()

    # 3 Pharma HCPs
    hcps = [
        HCP(name="Dr. Meera Sharma",  specialty="Cardiologist",         hospital="Apollo Hospital",  city="New Delhi"),
        HCP(name="Dr. Rajesh Patel",  specialty="General Practitioner", hospital="City Clinic",      city="Mumbai"),
        HCP(name="Dr. Anita Verma",   specialty="Endocrinologist",      hospital="Max Hospital",     city="Bangalore"),
    ]
    db.add_all(hcps)
    db.commit()

    # 5 Realistic Pharma Interactions
    interactions = [
        Interaction(hcp_id=1, interaction_date=date(2026,4,15), mode="visit",
            product_discussed="Atorvastatin 10mg", sentiment="Positive",
            materials_shared="Brochures", key_topics="Cholesterol management, post-MI patients",
            outcome="interested",
            raw_notes="Met Dr. Sharma at Apollo. Discussed Atorvastatin 10mg for post-MI.",
            ai_summary="Dr. Sharma showed strong interest in Atorvastatin 10mg."),
        Interaction(hcp_id=1, interaction_date=date(2026,4,10), mode="call",
            product_discussed="Rosuvastatin 20mg", sentiment="Neutral",
            materials_shared="None", key_topics="Dosage comparison, side effects",
            outcome="follow_up_needed",
            raw_notes="Phone call about Rosuvastatin 20mg vs competitors.",
            ai_summary="Dr. Sharma requested comparative data before switching."),
        Interaction(hcp_id=2, interaction_date=date(2026,4,17), mode="visit",
            product_discussed="Metformin 500mg", sentiment="Positive",
            materials_shared="Samples", key_topics="Type 2 diabetes management",
            outcome="samples_requested",
            raw_notes="Dr. Patel enthusiastic about Metformin. Requested 20 samples.",
            ai_summary="Strong prescription potential. 20 samples given."),
        Interaction(hcp_id=2, interaction_date=date(2026,4,12), mode="email",
            product_discussed="Glipizide 5mg", sentiment="Neutral",
            materials_shared="Brochures", key_topics="HbA1c reduction, combination therapy",
            outcome="detailed_product",
            raw_notes="Email follow-up on Glipizide combination therapy.",
            ai_summary="Dr. Patel requested detailed clinical data for Glipizide."),
        Interaction(hcp_id=3, interaction_date=date(2026,4,18), mode="visit",
            product_discussed="Insulin Glargine", sentiment="Positive",
            materials_shared="Brochures, Samples", key_topics="Basal insulin initiation",
            outcome="interested",
            raw_notes="Dr. Verma very interested in Insulin Glargine for T1D patients.",
            ai_summary="Priority account. Excellent engagement. Schedule follow-up within 10 days."),
    ]
    db.add_all(interactions)
    db.commit()

    # 2 Pending Follow-ups
    followups = [
        Followup(interaction_id=2, hcp_id=1, due_date=date(2026,4,28),
                 notes="Share Rosuvastatin vs Atorvastatin comparative study"),
        Followup(interaction_id=4, hcp_id=2, due_date=date(2026,4,25),
                 notes="Send Glipizide 5mg combination therapy clinical trial PDF"),
    ]
    db.add_all(followups)
    db.commit()
    db.close()
    print("Database seeded: 3 HCPs, 5 interactions, 2 follow-ups")

if __name__ == "__main__":
    seed()
```

---

## 3. Pydantic Schemas (backend/schemas.py)

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class InteractionFormState(BaseModel):
    # Field names MUST match Redux formSlice keys exactly
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
    # form_updates keys MUST match InteractionFormState field names
```

---

## 4. API Endpoints

| Method | URL                           | Purpose                                  |
|--------|-------------------------------|------------------------------------------|
| POST   | /api/chat                     | CORE: NL -> LangGraph -> form_updates    |
| GET    | /api/hcps                     | List all HCPs                            |
| GET    | /api/hcps/{id}                | Single HCP + recent interactions         |
| POST   | /api/hcps                     | Create HCP                               |
| GET    | /api/interactions             | List all (newest first)                  |
| GET    | /api/interactions/{id}        | Single interaction                       |
| POST   | /api/interactions             | Save current form to DB                  |
| PUT    | /api/interactions/{id}        | Edit interaction                         |
| DELETE | /api/interactions/{id}        | Delete interaction                       |
| GET    | /api/followups                | Upcoming (due >= today, status=pending)  |
| POST   | /api/followups                | Create follow-up                         |
| PUT    | /api/followups/{id}/complete  | Mark follow-up as done                   |
| GET    | /                             | Health check: {"status": "ok"}           |

---

## 5. LangGraph Agent Architecture (backend/agent.py)

### AgentState
```python
from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages:               Annotated[list, add_messages]  # LangGraph manages history
    current_form_state:     dict          # current left-panel state (from frontend)
    current_interaction_id: Optional[int] # for edit_interaction tool
    form_updates:           dict          # tools write here, sent back to frontend
    actions_taken:          list          # ["log_interaction", ...] per turn
```

### StateGraph
```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode([
    log_interaction,
    edit_interaction,
    get_hcp_profile,
    compliance_check,
    next_best_action,
]))
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    lambda s: "tools" if s["messages"][-1].tool_calls else END,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent")   # loop back after tool execution
graph = workflow.compile()
```

### Flow Diagram
```
START
  -> agent node (LLM reads message, decides which tool)
    -> [has tool_calls?] -> YES -> tools node (executes tool, updates state)
                                     -> back to agent node (generates reply)
                         -> NO  -> END (returns response to API)
```

### System Prompt
```
You are an AI assistant for a Life Sciences CRM used by pharmaceutical field reps.
You help reps log and manage HCP (Healthcare Professional) interactions.

You have 5 tools:
1. log_interaction     - When rep describes a visit, call, or email with an HCP
2. edit_interaction    - When rep wants to correct fields ("change X to Y")
3. get_hcp_profile     - When rep asks about an HCP history or profile
4. compliance_check    - When rep asks if they can visit an HCP again this month
5. next_best_action    - When rep asks what to do next with an HCP

RULES:
- Always call a tool. Never respond without using a tool first.
- log_interaction: extract ALL possible fields from the message.
- edit_interaction: change ONLY the fields mentioned. Preserve everything else.
- compliance_check: PhRMA guideline = max 3 visits per HCP per month.
- next_best_action: analyze sentiment trends, outcomes, last 10 interactions.
- If HCP name is ambiguous, ask the rep to clarify before proceeding.
- Be concise, professional, and friendly.
```

---

## 6. Tool Specifications (backend/tools.py)

### Tool 1: log_interaction
```
Decorator: @tool
Input:  message (str) - rep's natural language description
LLM:    llama-3.1-8b-instant
Prompt: Extract JSON {hcp_name, date, mode, product_discussed, sentiment,
        materials_shared, key_topics, outcome} - use null for missing fields
Post-process:
  - Fuzzy match hcp_name against hcps table -> get hcp_id
  - Generate ai_summary sentence
  - Set raw_notes = original message
DB:     INSERT Interaction -> returns interaction_id
State:  form_updates = all extracted fields + interaction_id
        actions_taken.append("log_interaction")
Return: "Logged interaction with [HCP] (ID: [n])"
```

### Tool 2: edit_interaction
```
Decorator: @tool
Input:  instruction (str) - "change X to Y" or "the name was actually..."
Requires: state.current_interaction_id (error if None - ask to log first)
LLM:    llama-3.1-8b-instant
Prompt: "Return ONLY the fields that changed as JSON. Do NOT include
         fields that were not mentioned in the instruction."
DB:     UPDATE Interaction SET [only changed fields] WHERE id=current_id
State:  form_updates = changed fields only (NOT all fields)
        actions_taken.append("edit_interaction")
Return: "Updated [field_list] in interaction #[id]"
```

### Tool 3: get_hcp_profile
```
Decorator: @tool
Input:  hcp_name (str)
No LLM call
DB:     SELECT HCP WHERE name ILIKE '%hcp_name%'
        SELECT last 5 Interactions WHERE hcp_id=x ORDER BY date DESC
        SELECT Followups WHERE hcp_id=x AND status=pending
State:  no form_updates
Return: Formatted string:
        "[name] | [specialty] | [hospital], [city]
         Recent interactions:
         - [date]: [mode] - [product] ([sentiment])
         Pending follow-ups:
         - Due [date]: [notes]"
```

### Tool 4: compliance_check
```
Decorator: @tool
Input:  hcp_name (str)
No LLM call
DB:     SELECT HCP by fuzzy name match
        COUNT Interactions WHERE hcp_id=x
          AND interaction_date >= first_day_of_current_month
          AND mode = 'visit'
LIMIT:  PHARMA_MONTHLY_LIMIT = 3  (PhRMA guideline)
Logic:  remaining = PHARMA_MONTHLY_LIMIT - visit_count
Return: If visit_count < limit:
          "COMPLIANT: [name] has [n] visit(s) this month. [remaining] remaining."
        If visit_count >= limit:
          "WARNING: [name] has reached the monthly visit limit ([n]/3).
           Do not schedule another visit until next month."
```

### Tool 5: next_best_action
```
Decorator: @tool
Input:  hcp_name (str)
LLM:    llama-3.3-70b-versatile  (secondary - deeper reasoning)
DB:     SELECT HCP by fuzzy name match
        SELECT last 10 Interactions WHERE hcp_id=x ORDER BY date DESC
Prompt: "You are a pharmaceutical sales strategist.
         HCP: [name] ([specialty], [hospital])
         Interaction history:
         [last 10 interactions as bullet list]

         Recommend the single most impactful next action for the field rep.
         Be specific: mention the product, the action, and the reason.
         Keep it under 3 sentences."
Return: "Next Best Action for [name]:
         [LLM recommendation]"
```

---

## 7. Critical Field Name Alignment

These names MUST be identical across all 4 layers:
  models.py -> schemas.py -> Redux formSlice -> API form_updates keys

| Field Name        | DB (models.py)     | Pydantic | Redux | API Response |
|-------------------|--------------------|----------|-------|--------------|
| hcp_name          | via HCP join       | YES      | YES   | YES          |
| hcp_id            | hcp_id             | YES      | YES   | YES          |
| date              | interaction_date*  | YES      | YES   | YES          |
| mode              | mode               | YES      | YES   | YES          |
| product_discussed | product_discussed  | YES      | YES   | YES          |
| sentiment         | sentiment          | YES      | YES   | YES          |
| materials_shared  | materials_shared   | YES      | YES   | YES          |
| key_topics        | key_topics         | YES      | YES   | YES          |
| outcome           | outcome            | YES      | YES   | YES          |
| follow_up_date    | follow_up_date     | YES      | YES   | YES          |
| follow_up_notes   | follow_up_notes    | YES      | YES   | YES          |
| status            | status             | YES      | YES   | YES          |

* interaction_date in DB column, sent as "date" in API response
