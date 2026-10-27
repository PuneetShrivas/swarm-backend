from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Swarm Backend", version="1.0.0")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Agent(BaseModel):
    id: str
    name: str
    role: str
    status: str

# In-memory storage for demo purposes
agents_db: List[Agent] = []

@app.get("/")
def read_root():
    return {"message": "Welcome to Swarm Backend API"}

@app.get("/api/agents", response_model=List[Agent])
def get_agents():
    """Returns a list of all agents in the swarm."""
    return agents_db

@app.post("/api/agents", response_model=Agent)
def create_agent(agent: Agent):
    """Creates a new agent in the swarm."""
    agents_db.append(agent)
    return agent

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
