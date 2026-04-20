# 🛡️ AI-First CRM HCP Module

### PhRMA-Compliant Interaction Logging & Strategic AI Orchestration

[![React](https://img.shields.io/badge/React-18.3-blue?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-Inference-f5ba31)](https://groq.com/)

A premium, high-fidelity CRM module designed for pharmaceutical field representatives. This solution offers **Dual-Mode Parity**, allowing reps to log interactions via a pixel-perfect structured form or a conversational AI assistant powered by LangGraph.

---

## 🌟 Key Features

### 1. Dual-Mode Logging Parity

- **Total Flexibility**: Switch between manual form entry and AI-driven chat at any time.
- **Bi-directional Sync**: Changes made in chat reflect instantly on the form with a **1.5s blue-pulse animation** for visual confirmation.
- **Manual Override**: The form remains fully interactive; AI-suggested values can be manually corrected.

### 2. Agentic 5-Tool Architecture (LangGraph)

The AI Assistant operates on a **stateful state graph** where the state persists across the conversation loop, allowing contextual corrections.

#### 🧠 Tool 1: `log_interaction`

- **Role**: Captures a new HCP interaction from free-form rep input.
- **Logic**: Performs entity extraction using `llama-3.1-8b-instant` to fill 11 structured fields. Fuzzy-matches `hcp_name` to database records.
- **Trigger**: _"Visited Dr. Sharma…"_, _"Met with Dr. Patel today..."_

#### ✏️ Tool 2: `edit_interaction`

- **Role**: Contextual modification of already-logged data.
- **Logic**: Reads `current_interaction_id` from state. LLM returns **ONLY** explicitly changed fields to prevent accidental overwrites.
- **Trigger**: _"Actually it was a call, not a visit"_, _"Change sentiment to Positive."_

#### 👤 Tool 3: `get_hcp_profile`

- **Role**: Retrieves account history and profile.
- **Logic**: **Zero LLM (Pure SQL)**. Returns details, last 5 interactions, and pending follow-ups.
- **Trigger**: _"Show me Dr. Sharma's history"_, _"What's Dr. Patel's specialty?"_

#### ⚖️ Tool 4: `compliance_check`

- **Role**: Verifies PhRMA visit limits.
- **Logic**: **Zero LLM (Pure SQL)**. Counts visits in the current calendar month vs. the **limit of 3 visits/month**.
- **Trigger**: _"Can I visit Dr. Verma again this month?"_

#### 🎯 Tool 5: `next_best_action`

- **Role**: Strategic recommendation engine.
- **Logic**: Deep reasoning using **llama-3.3-70b-versatile**. Analyzes interaction history to generate specific product-based strategies.
- **Trigger**: _"What should I do next with Dr. Verma?"_

---

## 🛠️ Tech Stack & Architecture

| Layer             | Technology                                           |
| ----------------- | ---------------------------------------------------- |
| **Frontend**      | React 18, Redux Toolkit, Lucide Icons                |
| **Backend**       | Python 3.10+, FastAPI, SQLAlchemy                    |
| **Orchestration** | LangGraph (Stateful Agent Workflow)                  |
| **LLM Inference** | Groq (Llama 3.1 8B Primary, Llama 3.3 70B Secondary) |
| **Database**      | MySQL (Primary), SQLite (Auto-Fallback)              |

> [!IMPORTANT]
> **Model Substitution Note**: As of Oct 8, 2025, `gemma2-9b-it` has been substituted with `llama-3.1-8b-instant` for primary tasks, and `llama-3.3-70b-versatile` is utilized for high-reasoning strategy.

---

## 📡 API Endpoints

| Method | Endpoint                 | Description                             |
| ------ | ------------------------ | --------------------------------------- |
| `POST` | `/api/chat`              | Main AI endpoint — runs LangGraph agent |
| `GET`  | `/api/interactions`      | Interaction history (Newest first)      |
| `POST` | `/api/interactions`      | Direct form save                        |
| `GET`  | `/api/hcps`              | HCP directory lookup                    |
| `GET`  | `/api/compliance/{name}` | Direct compliance check endpoint        |

---

## 🚀 Setup & Running Locally

### 1. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL_PRIMARY=llama-3.1-8b-instant
GROQ_MODEL_SECONDARY=llama-3.3-70b-versatile
DATABASE_URL=mysql+mysqlconnector://root@localhost/crm_hcp
# Fallback: sqlite:///./crm.db
```

### 2. Installation & Seed

```bash
# Backend
cd backend
pip install -r requirements.txt
python seed.py  # Initializes Dr. Sharma, Dr. Patel, and Dr. Verma
uvicorn main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm run dev
```

---

## 📊 Sample Data (seed.py)

| HCP              | Specialty            | Hospital        | City      |
| ---------------- | -------------------- | --------------- | --------- |
| Dr. Meera Sharma | Cardiologist         | Apollo Hospital | New Delhi |
| Dr. Rajesh Patel | General Practitioner | City Clinic     | Mumbai    |
| Dr. Anita Verma  | Endocrinologist      | Max Hospital    | Bangalore |

---

## 🎬 Video Walkthrough & Submission

**Submission Link**: [https://forms.gle/NFXPou3mgrB4Px1u5](https://forms.gle/NFXPou3mgrB4Px1u5)

The 10–15 minute video covers:

1. Live demo of all **5 LangGraph tools** functioning via chat.
2. Architecture explanation — how chat input flows into Redux form updates.
3. Code walkthrough — `agent.py` (StateGraph) and `tools.py` (SQL vs LLM logic).
4. PhRMA compliance logic and strategic recommendation reasoning.
