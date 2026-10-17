# AI-First CRM: HCP Interaction Logging

Pharma field reps lose time after every doctor visit retyping notes into CRM forms. In this project a rep can log a healthcare professional (HCP) visit either by filling in a form or by describing it in a chat, and the two stay in sync. The chat fills in the form fields, and the form's current values go back to the assistant with every message, so a follow-up like "actually it was a call" can correct the record that was just logged.

Case study: [aryanpanwar.in/case-studies/ai-first-crm-hcp](https://aryanpanwar.in/case-studies/ai-first-crm-hcp)

---

## What it does

- **Form or chat, kept in sync.** Fields the assistant fills in are highlighted for 1.5 seconds so the rep can see what changed. The form stays editable, so any value the AI suggests can be corrected by hand before saving.
- **Five assistant actions**, built as LangGraph tools:

| Tool | What it does | Uses an LLM? |
| --- | --- | --- |
| `log_interaction` | Pulls 10 fields (HCP name, date, time, mode, product, sentiment, materials, topics, outcome, follow-up notes) out of a free-text note, matches the HCP name against the database and saves the interaction. Example: "Met Dr. Patel today…" | Yes, Llama 3.1 8B |
| `edit_interaction` | Changes only the fields the rep mentions, e.g. "Change sentiment to Positive". | Yes, Llama 3.1 8B |
| `get_hcp_profile` | Returns specialty, hospital, city and the last 5 interactions. | No, SQL only |
| `compliance_check` | Counts this calendar month's in-person meetings with the HCP against a limit of 3. | No, SQL only |
| `next_best_action` | Reads the last 5 interactions and suggests one next step in two sentences or fewer. | Yes, Llama 3.3 70B |

- **Compliance checks based on the PhRMA Code.** There are two simple checks: the monthly in-person visit limit above, and a checkbox ("I confirm compliance with PhRMA guidelines") that the rep has to tick before the form will save. The limit of 3 is a rule set in `backend/tools.py`, not a number taken from the Code. Questions like "Can I visit Dr. Verma again this month?" are answered straight from SQL when the message names a known HCP, without calling the LLM.
- **Plain-language replies.** The backend strips JSON, code blocks and internal field names from the assistant's replies before they reach the rep.
- **Dashboard.** A list of recent interactions, newest first.

## How it works

1. The React app keeps the form and the chat in one Redux store.
2. A chat message goes to `POST /api/chat` together with the current form values.
3. FastAPI runs a LangGraph graph with an agent node (Llama 3.1 8B with the five tools bound) and a tools node. The agent picks a tool, the tool runs, and the agent writes a short plain-text reply.
4. The response carries `form_updates`. Redux applies them to the form and highlights the changed fields.
5. Saving the form calls `POST /api/interactions`.

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, Redux Toolkit, React Router, Vite, Lucide icons |
| Backend | Python, FastAPI, SQLAlchemy |
| Agent | LangGraph, LangChain (Groq) |
| Models | Groq-hosted `llama-3.1-8b-instant` (extraction, tool routing) and `llama-3.3-70b-versatile` (next best action) |
| Database | MySQL, or SQLite when `DATABASE_URL` isn't set |

## API endpoints

| Endpoint | Description |
| --- | --- |
| `POST /api/chat` | Runs the LangGraph agent on a chat message |
| `GET /api/interactions` | Interaction history, newest first |
| `POST /api/interactions` | Saves the form |
| `PUT /api/interactions/{id}` | Updates an interaction |
| `DELETE /api/interactions/{id}` | Deletes an interaction |
| `GET /api/hcps`, `GET /api/hcps/{id}` | HCP directory |
| `GET /api/followups` | Pending follow-ups |
| `PUT /api/followups/{id}/complete` | Marks a follow-up done |

## Running it locally

### 1. Environment

Copy `backend/.env.example` to `backend/.env` and fill it in:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL_PRIMARY=llama-3.1-8b-instant
GROQ_MODEL_SECONDARY=llama-3.3-70b-versatile
DATABASE_URL=mysql+mysqlconnector://root@localhost/crm_hcp
# Or use SQLite: sqlite:///./crm_hcp.db
```

### 2. Install, seed and run

```bash
# Backend
cd backend
pip install -r requirements.txt
python seed.py  # adds 3 sample HCPs, 5 interactions and 2 follow-ups
uvicorn main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev
```

There's also a `docker-compose.yml` that runs MySQL, the backend and the frontend together (`docker compose up --build`). It still needs `backend/.env` to exist.

## Sample data

| HCP | Specialty | Hospital, city |
| --- | --- | --- |
| Dr. Meera Sharma | Cardiologist | City Hospital, New Delhi |
| Dr. Rajesh Patel | General Practitioner | City Clinic, Mumbai |
| Dr. Anita Verma | Endocrinologist | Lakeside Clinic, Bangalore |

All names here are fictional placeholders.

## Status

This is a working prototype. It runs locally against seeded sample data. It has no user authentication, and the only deployment setup in the repo is the local Docker Compose file.

---

Built by [Aryan Panwar](https://aryanpanwar.in).
