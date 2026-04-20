import os
import json
from datetime import date, datetime
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from database import SessionLocal
from models import HCP, Interaction, Followup

def get_db_session():
    return SessionLocal()

@tool
def log_interaction(message: str):
    """
    Extracts interaction details from natural language and logs them in the database.
    Use this when the user describes a visit, call, or email with an HCP.
    """
    db = get_db_session()
    try:
        primary_model = os.getenv("GROQ_MODEL_PRIMARY", "llama-3.1-8b-instant")
        llm = ChatGroq(temperature=0, model_name=primary_model)
        
        prompt = f"""Extract structured data from this interaction description:
"{message}"

Return ONLY valid JSON with these fields:
- hcp_name: string
- date: YYYY-MM-DD
- time: HH:MM (24h)
- mode: "Meeting" | "Call" | "Email" | "Video"
- product_discussed: string
- sentiment: "Positive" | "Neutral" | "Negative"
- materials_shared: string
- key_topics: string
- outcome: string
- follow_up_notes: string

If a field is not found, use null."""

        response = llm.invoke(prompt)
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
        
        extracted_data = json.loads(content)
        hcp_name = extracted_data.get("hcp_name", "").replace("Dr.", "").strip()
        
        # Fuzzy match HCP - search for name without 'Dr.' prefix
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        hcp_id = hcp.id if hcp else None
        
        # Interaction mapping
        interaction_date_str = extracted_data.get("date")
        interaction_date = date.today()
        if interaction_date_str:
            try:
                interaction_date = datetime.strptime(interaction_date_str, "%Y-%m-%d").date()
            except: pass

        new_interaction = Interaction(
            hcp_id=hcp_id,
            interaction_date=interaction_date,
            mode=extracted_data.get("mode", "Meeting"),
            product_discussed=extracted_data.get("product_discussed", ""),
            sentiment=extracted_data.get("sentiment", "Neutral"),
            materials_shared=extracted_data.get("materials_shared", ""),
            key_topics=extracted_data.get("key_topics", ""),
            outcome=extracted_data.get("outcome", ""),
            follow_up_notes=extracted_data.get("follow_up_notes", ""),
            raw_notes=message,
            source="chat",
            status="completed"
        )
        db.add(new_interaction)
        db.commit()
        db.refresh(new_interaction)
        
        # Prepare form updates for frontend
        form_updates = {k: v for k, v in extracted_data.items() if v is not None}
        form_updates["interaction_id"] = new_interaction.id
        form_updates["hcp_id"] = hcp_id
        if hcp: form_updates["hcp_name"] = hcp.name
        
        return json.dumps({
            "status": "success",
            "message": f"Logged the interaction with {hcp.name if hcp else hcp_name} and updated the form.",
            "form_updates": form_updates,
            "action": "log_interaction"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def edit_interaction(instruction: str, interaction_id: int):
    """
    Updates an existing interaction based on instructions.
    Example: "change the date to tomorrow" or "set sentiment to Positive".
    """
    db = get_db_session()
    try:
        primary_model = os.getenv("GROQ_MODEL_PRIMARY", "llama-3.1-8b-instant")
        llm = ChatGroq(temperature=0, model_name=primary_model)
        
        prompt = f"""Identify the changes requested: "{instruction}"
Return ONLY a JSON object of the fields to change.
Allowed fields: hcp_name, date, time, mode, product_discussed, sentiment, materials_shared, key_topics, outcome, follow_up_notes.
For dates, use YYYY-MM-DD. (Today is {date.today().isoformat()})."""

        response = llm.invoke(prompt)
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        
        changes = json.loads(content)
        
        interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
        if not interaction:
            return json.dumps({"status": "error", "message": "Interaction not found."})
        
        # Update DB
        for key, value in changes.items():
            if key == "date":
                interaction.interaction_date = datetime.strptime(value, "%Y-%m-%d").date()
            elif hasattr(interaction, key):
                setattr(interaction, key, value)
        
        db.commit()
        
        return json.dumps({
            "status": "success",
            "message": "Updated the requested interaction details in the form.",
            "form_updates": changes,
            "action": "edit_interaction"
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
    finally:
        db.close()

@tool
def get_hcp_profile(hcp_name: str):
    """Retrieves HCP profile, specialty, hospital and last 5 interactions."""
    db = get_db_session()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return json.dumps({"status": "error", "message": f"HCP '{hcp_name}' not found."})
        
        interactions = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).order_by(Interaction.interaction_date.desc()).limit(5).all()
        hist = [{"date": str(i.interaction_date), "product": i.product_discussed, "sentiment": i.sentiment} for i in interactions]
        
        profile_msg = f"{hcp.name} is a {hcp.specialty} at {hcp.hospital}, {hcp.city}."
        if hist:
            profile_msg += "\nRecent interactions: " + ", ".join([f"{i['date']} ({i['product']})" for i in hist])
        
        return json.dumps({
            "status": "success",
            "message": profile_msg,
            "form_updates": {"hcp_id": hcp.id, "hcp_name": hcp.name},
            "action": "get_hcp_profile"
        })
    finally:
        db.close()

@tool
def compliance_check(hcp_name: str):
    """Verifies if the rep can visit the HCP again this month (Max 3 visits/month)."""
    db = get_db_session()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp: return json.dumps({"status": "error", "message": "HCP not found."})
        
        first_day = date.today().replace(day=1)
        count = db.query(Interaction).filter(
            Interaction.hcp_id == hcp.id,
            Interaction.interaction_date >= first_day,
            Interaction.mode == "Meeting"
        ).count()
        
        limit = 3
        compliant = count < limit
        if compliant:
            msg = f"{hcp.name} has {count} of {limit} in-person visits this month. Another visit is within the monthly limit."
        else:
            msg = f"{hcp.name} has reached the monthly limit of {limit} in-person visits. Do not schedule another in-person visit this month."
        
        return json.dumps({
            "status": "success",
            "message": msg,
            "action": "compliance_check"
        })
    finally:
        db.close()

@tool
def next_best_action(hcp_name: str):
    """Generates a strategic recommendation using the advanced 70B model."""
    db = get_db_session()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp: return json.dumps({"status": "error", "message": "HCP not found."})
        
        interactions = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).order_by(Interaction.interaction_date.desc()).limit(5).all()
        summary = "\n".join([f"- {i.interaction_date}: {i.product_discussed} ({i.sentiment}) -> {i.outcome}" for i in interactions])
        
        secondary_model = os.getenv("GROQ_MODEL_SECONDARY", "llama-3.3-70b-versatile")
        llm = ChatGroq(temperature=0.7, model_name=secondary_model)
        
        prompt = f"""Analyze interaction history for {hcp.name} ({hcp.specialty}):
{summary}

Suggest the SINGLE most impactful Next Best Action. Be concise (max 2 sentences)."""
        
        response = llm.invoke(prompt)
        return json.dumps({
            "status": "success",
            "message": f"Next best action: {response.content}",
            "action": "next_best_action"
        })
    finally:
        db.close()
