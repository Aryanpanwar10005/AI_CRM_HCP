# TECH_STACK.md - Exact Stack, Libraries & Versions
## Version 4 - Final - April 19 2026

---

## IMPORTANT: Model Substitution Note

PDF specifies: gemma2-9b-it
Groq shutdown date: October 8, 2025
Source: https://console.groq.com/docs/deprecations

Replacement used: llama-3.1-8b-instant

| Property       | gemma2-9b-it (DEAD)    | llama-3.1-8b-instant (ACTIVE) |
|----------------|------------------------|-------------------------------|
| Status         | SHUTDOWN Oct 8 2025    | Active                        |
| Speed          | ~500 tok/s             | ~560-1250 tok/s               |
| Context window | 8,192 tokens           | 131,072 tokens                |
| Tool calling   | Unreliable             | Confirmed working             |

This substitution is documented in README for evaluators.

---

## Frontend

| Package               | Version | Purpose                  |
|-----------------------|---------|--------------------------|
| react                 | 18.3.1  | UI framework             |
| react-dom             | 18.3.1  | DOM rendering            |
| react-router-dom      | 6.26.2  | SPA routing              |
| @reduxjs/toolkit      | 2.3.0   | State management (PDF required) |
| react-redux           | 9.1.2   | Redux bindings           |
| axios                 | 1.7.7   | HTTP client              |
| lucide-react          | 0.454.0 | Icons                    |
| vite                  | 5.4.8   | Dev server + build tool  |
| @vitejs/plugin-react  | 4.3.2   | Vite React plugin        |

### frontend/.env
```
VITE_API_BASE_URL=http://localhost:8000
```

### src/api/axios.js
```js
import axios from 'axios';
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 60000,   // 60s - LLM processing can be slow
});
export default api;
```

---

## Backend

| Package                  | Version    | Purpose                             |
|--------------------------|------------|-------------------------------------|
| fastapi                  | 0.115.0    | Web framework (PDF required)        |
| uvicorn[standard]        | 0.30.0     | ASGI server                         |
| sqlalchemy               | 2.0.36     | ORM - works MySQL + SQLite + PG     |
| mysql-connector-python   | 8.3.0      | MySQL driver (pure Python, no C)    |
| python-dotenv            | 1.0.1      | Load .env file                      |
| pydantic                 | 2.9.2      | Request/response validation         |
| langgraph                | 0.2.55     | Agent framework (PDF required)      |
| langchain-groq           | 0.3.6      | Groq LLM integration                |
| langchain-core           | >=0.3.68   | Required by langchain-groq 0.3.6    |
| groq                     | >=0.29.0   | Groq SDK                            |
| httpx                    | 0.27.2     | Async HTTP (used by groq)           |
| dateparser               | 1.2.0      | Parse "next Monday" -> actual date  |

### backend/requirements.txt
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
mysql-connector-python==8.3.0
python-dotenv==1.0.1
pydantic==2.9.2
langgraph==0.2.55
langchain-groq==0.3.6
langchain-core>=0.3.68
groq>=0.29.0
httpx==0.27.2
dateparser==1.2.0
# Optional - uncomment for PostgreSQL:
# psycopg2-binary==2.9.9
```

### backend/.env
```
# PRIMARY: MySQL local (matches PDF requirement)
DATABASE_URL=mysql+mysqlconnector://root:@localhost/crm_hcp

# FALLBACK: SQLite - zero install, change only this line
# DATABASE_URL=sqlite:///./crm_hcp.db

# OPTIONAL: PostgreSQL
# DATABASE_URL=postgresql+psycopg2://postgres:password@localhost/crm_hcp

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_PRIMARY=llama-3.1-8b-instant
GROQ_MODEL_SECONDARY=llama-3.3-70b-versatile
```

---

## AI / LLM Stack

| Layer            | Choice                    | Version  | Status |
|------------------|---------------------------|----------|--------|
| Agent Framework  | LangGraph                 | 0.2.55   | Active |
| LLM Provider     | Groq                      | -        | Active |
| LangChain-Groq   | langchain-groq            | 0.3.6    | Active |
| LangChain Core   | langchain-core            | >=0.3.68 | Active |
| Primary Model    | llama-3.1-8b-instant      | -        | Active |
| Secondary Model  | llama-3.3-70b-versatile   | -        | Active |

### Model Usage by Tool
| Tool                  | Model                   | Reason                        |
|-----------------------|-------------------------|-------------------------------|
| log_interaction       | llama-3.1-8b-instant    | Fast JSON extraction          |
| edit_interaction      | llama-3.1-8b-instant    | Fast field identification     |
| get_hcp_profile       | No LLM - DB only        | Pure SQL query                |
| compliance_check      | No LLM - DB only        | COUNT query + rule check      |
| next_best_action      | llama-3.3-70b-versatile | Deep reasoning over history   |

---

## Database

| Item        | Choice                | Notes                                      |
|-------------|-----------------------|--------------------------------------------|
| Primary DB  | MySQL 8.0             | Matches PDF spec                           |
| Fallback    | SQLite 3              | Zero install - change one .env line        |
| ORM         | SQLAlchemy 2.0        | Same ORM models for both - only URL changes|
| Setup       | python seed.py        | Auto-creates tables + inserts pharma data  |
| Driver      | mysql-connector-python| Pure Python - no C compilation issues      |

### database.py pattern
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm_hcp.db")

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Developer Experience - 3 Ways to Run

### Option 1: Docker Compose (Recommended - Zero Setup)
```bash
# Requires: Docker Desktop installed
cp .env.example .env
# Edit .env: add your GROQ_API_KEY (only thing needed)
docker-compose up
# Open: http://localhost:5173
```

### Option 2: Makefile (MySQL already installed)
```bash
cp .env.example .env    # fill DATABASE_URL + GROQ_API_KEY
make install            # pip install -r requirements.txt + npm install
make seed               # python seed.py (creates tables + data)
make dev                # starts uvicorn + vite simultaneously
```

### Option 3: Windows start.bat (Double-click)
```
1. Fill in .env with your GROQ_API_KEY
2. Double-click start.bat
3. Open http://localhost:5173
```

---

## Design Tokens (CSS Variables)

```css
:root {
  --color-primary:        #0D7E79;   /* Pharma Teal */
  --color-primary-hover:  #0A6560;
  --color-bg:             #F8FAFC;
  --color-surface:        #FFFFFF;
  --color-left-panel:     #F1F5F9;
  --color-text:           #1A1A2E;
  --color-text-muted:     #64748B;
  --color-border:         #E2E8F0;
  --color-field-highlight:#E0F2FE;   /* animates when AI fills field */
  --color-success:        #22C55E;
  --color-warning:        #F59E0B;
  --color-error:          #EF4444;
  --font-body:            'Inter', sans-serif;
}
```

Font load (in index.html):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```
