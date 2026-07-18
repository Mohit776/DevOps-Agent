from typing import TypedDict

class AgentState(TypedDict):
    alert: dict
    diagnosis: str
    plan: str
    execution: str
    verified: bool