"""
Component inventory registry (GOV-02).
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass
class ComponentVersion:
    id: str
    type: str # model | tool | defense | dependency
    name: str
    version: str
    description: str

COMPONENT_INVENTORY: list[ComponentVersion] = [
    ComponentVersion("gemini-3.8-flash", "model", "Gemini 3.8 Flash", "latest", "Google DeepMind frontier model"),
    ComponentVersion("read_email", "tool", "Read Email", "1.0", "Reads simulated emails"),
    ComponentVersion("send_email", "tool", "Send Email", "1.0", "Sends simulated emails"),
    ComponentVersion("search_docs", "tool", "Search Documents", "1.0", "Queries RAG knowledge base"),
    ComponentVersion("policy_engine", "defense", "Deterministic Policy Engine", "1.0", "Blocks unapproved tool arguments"),
    ComponentVersion("injection_classifier", "defense", "LLM Injection Classifier", "1.0", "Detects malicious prompts"),
    ComponentVersion("fastapi", "dependency", "FastAPI", "0.111.0", "Web framework"),
    ComponentVersion("sqlalchemy", "dependency", "SQLAlchemy", "2.0.30", "ORM"),
]
