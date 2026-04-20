# PRD.md - Product Requirements Document
## AI-First CRM HCP Module - LogInteractionScreen
### Version 4 - Final - April 19 2026

---

## 1. Problem Statement

Pharmaceutical field reps visit 8-12 HCPs per day. After every visit they must
log: who they met, what product, doctor sentiment, materials shared, next steps.
Today done manually - rep types from memory, misses fields, makes errors.

Solution: Rep describes visit in plain English. AI extracts every field, fills
the form, saves to DB, suggests next best action. All in one message.

---

## 2. PDF Requirements Checklist

| # | PDF Requirement | Our Implementation | Status |
|---|----------------|-------------------|--------|
| 1 | React UI + Redux state management | React 18.3.1 + Redux Toolkit 2.3.0 | PASS |
| 2 | Python + FastAPI | Python 3.11 + FastAPI 0.115.0 | PASS |
| 3 | LangGraph (mandatory - app rejected without it) | langgraph 0.2.55 - StateGraph ReAct pattern | PASS |
| 4 | Groq model: gemma2-9b-it | llama-3.1-8b-instant - Groq official replacement (gemma2 SHUTDOWN Oct 8 2025) | PASS substituted |
| 5 | llama-3.3-70b-versatile for context | Used in Tool 5 (next_best_action) for deep reasoning | PASS |
| 6 | Database: MySQL or PostgreSQL | MySQL 8.0 primary + SQLite fallback via SQLAlchemy ORM | PASS |
| 7 | Font: Google Inter | Inter 400,500,600,700 via Google Fonts CDN | PASS |
| 8 | Log Interaction Screen: structured form OR chat | Split screen: LEFT=read-only form + RIGHT=AI chat (both visible) | PASS |
| 9 | Minimum 5 LangGraph tools | log_interaction, edit_interaction, get_hcp_profile, compliance_check, next_best_action | PASS |
| 10 | Tool: Log Interaction (MANDATORY) | Tool 1 - NL -> JSON extraction -> DB INSERT -> form populated | PASS |
| 11 | Tool: Edit Interaction (MANDATORY) | Tool 2 - NL -> ONLY changed fields -> DB UPDATE | PASS |
| 12 | Single GitHub repo + README.md | One repo: frontend/ + backend/ + README | PASS |
| 13 | Video: frontend URL walkthrough | localhost:5173 screen recording | PASS |
| 14 | Video: all 5 tools demonstrated | Each tool has scripted demo scenario in VIDEO_SCRIPT.md | PASS |
| 15 | Video: code flow + architecture explanation | LangGraph graph, Redux flow, API contract explained | PASS |
| 16 | Video: personal understanding summary | Life sciences CRM context, AI value in pharma | PASS |

---

## 3. Core Screen Layout - Log Interaction (Split Screen)

```
+----------------------------------------------------------+
| CRM HCP Module                    [light/dark toggle]    |
| Dashboard | Log Interaction | HCP Profiles               |
+---------------------------+------------------------------+
| LEFT PANEL (40%)          | RIGHT PANEL (60%)            |
| Interaction Details       | AI Chat Assistant            |
| [READ-ONLY - AI fills it] |                              |
|                           | Bot: Hi! Describe your visit |
| HCP Name    [__________]  | and I will fill the form.    |
| Date        [__________]  |                              |
| Mode        [__________]  | User: Met Dr. Sharma...      |
| Product     [__________]  |                              |
| Sentiment   [__________]  | Bot: Logged! Form populated. |
| Materials   [__________]  |                              |
| Key Topics  [__________]  | [... typing indicator ...]   |
| Outcome     [__________]  |                              |
| Follow-up   [__________]  | [Type message]     [Send]    |
|                           |                              |
| [Save Interaction]        |                              |
| disabled until AI fills   |                              |
| hcp_name + date           |                              |
+---------------------------+------------------------------+
```

CRITICAL RULE: Form fields are readOnly. ONLY the LangGraph agent writes to
them via form_updates in API response -> Redux dispatch -> CSS animation.

---

## 4. The 5 LangGraph Tools

### Tool 1: log_interaction (MANDATORY)
- Trigger: Rep describes a visit/call/email in natural language
- LLM: llama-3.1-8b-instant - structured JSON entity extraction
- Extracts: hcp_name, date, mode, product_discussed, sentiment,
            materials_shared, key_topics, outcome, raw_notes
- DB: INSERT into interactions table, returns interaction_id
- Frontend: ALL extracted fields animate into left panel (blue highlight)

### Tool 2: edit_interaction (MANDATORY)
- Trigger: Rep says "change X to Y" or corrects a mistake
- LLM: llama-3.1-8b-instant - identifies ONLY the changed fields
- CRITICAL: Unchanged fields are NEVER touched or re-sent
- DB: UPDATE interactions SET [changed_fields_only] WHERE id=current_id
- Frontend: ONLY changed fields highlight/update

### Tool 3: get_hcp_profile
- Trigger: "Show me Dr. Sharma's history" / "Who is Dr. Patel?"
- DB: SELECT hcp + last 5 interactions + pending followups
- Output: Rich text in chat panel, no form update

### Tool 4: compliance_check (DIFFERENTIATOR - real Veeva CRM feature)
- Trigger: "Can I visit Dr. Sharma again?" / "Is it okay to go back?"
- Logic: COUNT(visits this month for HCP) vs PhRMA limit (3/month)
- Output: "COMPLIANT: 1 visit this month, 2 remaining"
       OR "WARNING: 3 visits this month - monthly limit reached"
- Domain value: Real pharma compliance requirement, shows industry knowledge

### Tool 5: next_best_action (DIFFERENTIATOR - real Veeva AI / Salesforce LSC)
- Trigger: "What should I do next with Dr. Sharma?"
- LLM: llama-3.3-70b-versatile - deep reasoning over full interaction history
- Output: Specific recommendation: product + action + timing + reason
- Domain value: AI-powered sales intelligence, shows advanced AI reasoning

---

## 5. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| LLM response time | < 10s (Groq ~500-1250 tok/s) |
| Axios timeout | 60s (covers worst-case cold start) |
| DB setup time for evaluator | < 3 min via Docker OR seed.py |
| Form field animation | 300ms ease-in blue highlight on AI update |
| Chat typing indicator | Animated 3-dot bounce while agent processing |
| Mobile responsive | Not required (desktop B2B CRM tool) |
| Auth / login | Not required (out of scope per PDF) |
| Cloud deployment | Not required (localhost:5173 for video) |

---

## 6. Out of Scope
- User authentication / login
- Multi-user / multi-rep support
- Cloud deployment
- Email notifications
- PDF/CSV export
- Real-time collaboration
