from typing import TypedDict, Any

class AgentState(TypedDict):
    alert: dict           # incoming alert data (must include container_id)
    log_summary: dict     # structured log analysis from Log MCP
    metrics_summary: dict # structured metrics snapshot from Metrics MCP
    diagnosis: str        # JSON string from LLM diagnosis step
    plan: str             # JSON string from planner node
    risk_assessment: str  # JSON string from risk classifier node
    human_approved: bool  # True if a human approved a high-risk plan
    execution: str        # output from execute node
    verified: bool        # True if post-remediation health check passed