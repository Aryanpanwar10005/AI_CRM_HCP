from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import ChatMessage, ChatResponse
from agent import graph
from langchain_core.messages import HumanMessage
from models import HCP
from tools import compliance_check
import json
import re

router = APIRouter(prefix="/api/chat", tags=["chat"])

TECHNICAL_REPLY_MARKERS = (
    "```",
    "form_updates",
    "current_form_state",
    "current_interaction_id",
    "interaction_id",
    "tool_call",
    "tool_calls",
    "hcp_id",
    "raw_notes",
    "traceback",
    "log_interaction",
    "edit_interaction",
    "get_hcp_profile",
    "compliance_check",
    "next_best_action",
)

META_REPLY_PATTERN = re.compile(
    r"^(here (is|are)|below is|i found|the following).*?(code|json|technical|raw|payload|object|block|response)",
    re.IGNORECASE,
)

FIELD_LABELS = {
    "hcp_name": "HCP name",
    "product_discussed": "product discussed",
    "materials_shared": "materials shared",
    "key_topics": "key discussion topics",
    "follow_up_notes": "follow-up notes",
    "follow_up_date": "follow-up date",
}

COMPLIANCE_QUESTION_PATTERN = re.compile(
    r"\b(can|could|should|allowed|eligible|compliance|limit|again|monthly)\b",
    re.IGNORECASE,
)


def _looks_like_json_or_code(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return False

    try:
        json.loads(stripped)
        return True
    except json.JSONDecodeError:
        pass

    lowered = stripped.lower()
    if any(marker in lowered for marker in TECHNICAL_REPLY_MARKERS):
        return True

    return bool(
        re.search(r'["\']?[a-zA-Z_][\w]*["\']?\s*:', stripped)
        and any(char in stripped for char in "{}[]")
    )


def _strip_fenced_blocks(value: str) -> str:
    def replace_block(match: re.Match) -> str:
        body = match.group("body").strip()
        return "" if _looks_like_json_or_code(body) else body

    return re.sub(
        r"```(?P<language>[a-zA-Z0-9_-]+)?\s*(?P<body>.*?)```",
        replace_block,
        value,
        flags=re.DOTALL,
    )


def _strip_balanced_json(value: str) -> str:
    output = []
    index = 0

    while index < len(value):
        if value[index] != "{":
            output.append(value[index])
            index += 1
            continue

        depth = 0
        end_index = index
        while end_index < len(value):
            if value[end_index] == "{":
                depth += 1
            elif value[end_index] == "}":
                depth -= 1
                if depth == 0:
                    break
            end_index += 1

        if depth == 0:
            candidate = value[index : end_index + 1]
            if _looks_like_json_or_code(candidate):
                index = end_index + 1
                continue

        output.append(value[index])
        index += 1

    return "".join(output)


def _fallback_reply(actions_taken: list[str], form_updates: dict) -> str:
    actions = set(actions_taken or [])

    if "log_interaction" in actions:
        return "I logged the interaction and updated the form. Please review the highlighted fields before saving."
    if "edit_interaction" in actions:
        return "I updated the requested interaction details in the form. Please review the highlighted fields."
    if "get_hcp_profile" in actions:
        return "I found the HCP profile and updated the form."
    if "compliance_check" in actions:
        return "I checked visit compliance for this HCP. Please review the recommendation before scheduling."
    if "next_best_action" in actions:
        return "I prepared a next best action recommendation for this HCP."
    if form_updates:
        return "I updated the form with the details I found. Please review the highlighted fields."

    return "I reviewed your request and kept the response focused on the next step."


def _find_hcp_name(message: str, db: Session) -> str | None:
    normalized_message = re.sub(r"\bdr\.?\b", "", message.lower())
    normalized_message = re.sub(r"[^a-z0-9\s]", " ", normalized_message)

    for hcp in db.query(HCP).all():
        normalized_name = re.sub(r"\bdr\.?\b", "", hcp.name.lower())
        normalized_name = re.sub(r"[^a-z0-9\s]", " ", normalized_name).strip()
        name_parts = [part for part in normalized_name.split() if len(part) > 2]

        if normalized_name and normalized_name in normalized_message:
            return hcp.name
        if name_parts and any(part in normalized_message.split() for part in name_parts):
            return hcp.name

    return None


def _try_direct_compliance_response(request: ChatMessage, db: Session) -> ChatResponse | None:
    if not COMPLIANCE_QUESTION_PATTERN.search(request.message):
        return None

    hcp_name = _find_hcp_name(request.message, db)
    if not hcp_name:
        return None

    result = json.loads(compliance_check.invoke({"hcp_name": hcp_name}))
    reply = clean_ai_reply(result.get("message", ""), ["compliance_check"], {})

    return ChatResponse(
        reply=reply,
        actions_taken=["compliance_check"],
        interaction_id=request.current_interaction_id,
        form_updates={}
    )


def clean_ai_reply(reply: str, actions_taken: list[str], form_updates: dict) -> str:
    cleaned = _strip_fenced_blocks(reply or "")
    cleaned = _strip_balanced_json(cleaned)
    cleaned = cleaned.replace("`", "")

    for field_name, label in FIELD_LABELS.items():
        cleaned = re.sub(rf"\b{field_name}\b", label, cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\(ID:\s*\d+\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\binteraction\s*#\d+\b", "the interaction", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bStrategic NBA:\s*", "Next best action: ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bYou ARE compliant\b", "This is within the monthly limit", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bDO NOT VISIT again this month\b", "Do not schedule another in-person visit this month", cleaned, flags=re.IGNORECASE)

    lines = []
    for line in cleaned.splitlines():
        line = line.strip(" \t-")
        lowered = line.lower()
        if not line:
            continue
        if META_REPLY_PATTERN.search(line):
            continue
        if any(marker in lowered for marker in TECHNICAL_REPLY_MARKERS):
            continue
        if _looks_like_json_or_code(line):
            continue
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)

    if not cleaned or any(marker in cleaned.lower() for marker in TECHNICAL_REPLY_MARKERS):
        return _fallback_reply(actions_taken, form_updates)

    return cleaned


@router.post("", response_model=ChatResponse)
async def chat_with_agent(request: ChatMessage, db: Session = Depends(get_db)):
    try:
        direct_response = _try_direct_compliance_response(request, db)
        if direct_response:
            return direct_response

        # Prepare state for LangGraph
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "current_form_state": request.current_form_state.dict() if request.current_form_state else {},
            "current_interaction_id": request.current_interaction_id,
            "form_updates": {},
            "actions_taken": []
        }
        
        # Execute Graph
        result = await graph.ainvoke(initial_state)
        
        # Extract reply and updates
        last_message = result["messages"][-1]
        final_reply = last_message.content
        
        final_reply = clean_ai_reply(
            final_reply,
            result.get("actions_taken", []),
            result.get("form_updates", {})
        )
        
        return ChatResponse(
            reply=final_reply,
            actions_taken=result["actions_taken"],
            interaction_id=result.get("current_interaction_id"),
            form_updates=result["form_updates"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
