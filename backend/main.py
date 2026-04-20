from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import chat, hcps, interactions, followups
import uvicorn
import os

app = FastAPI(title="CRM HCP Module API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

from database import engine, Base
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(chat.router)
app.include_router(hcps.router)
app.include_router(interactions.router)
app.include_router(followups.router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "CRM HCP API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
