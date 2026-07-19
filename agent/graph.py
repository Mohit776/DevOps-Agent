import sys
import os
import json
import logfire
from langgraph.graph import StateGraph, END

# Add root directory to path for config import
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from state import AgentState
import config
from nodes import diagnose_node, planner_node, risk_classifier_node, human_approval_node, execute_node, verify_node

# Configure Logfire once at startup
logfire.configure(token=config.LOGFIRE_TOKEN)
logfire.info("🚀 DevOps Agent initialized")


def _needs_approval(state: AgentState) -> str:
    """Conditional edge: route to human_approval if risk classifier requires it."""
    try:
        risk_data = json.loads(state.get("risk_assessment", "{}"))
    except Exception:
        risk_data = {}
    if risk_data.get("approval_required", False):
        return "human_approval"
    return "execute"


def _approval_gate(state: AgentState) -> str:
    """Conditional edge: proceed to execute only if human approved."""
    if state.get("human_approved", False):
        return "execute"
    return "end"


def build_graph():
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("risk_classifier", risk_classifier_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("verify", verify_node)

    # Linear flow up to risk classifier
    workflow.set_entry_point("diagnose")
    workflow.add_edge("diagnose", "planner")
    workflow.add_edge("planner", "risk_classifier")

    # Conditional: needs approval?
    workflow.add_conditional_edges(
        "risk_classifier",
        _needs_approval,
        {
            "human_approval": "human_approval",
            "execute": "execute",
        }
    )

    # Conditional: was the plan approved?
    workflow.add_conditional_edges(
        "human_approval",
        _approval_gate,
        {
            "execute": "execute",
            "end": END,
        }
    )

    # Execute → Verify → END
    workflow.add_edge("execute", "verify")
    workflow.add_edge("verify", END)

    return workflow.compile()

agent_app = build_graph()

def run_agent(alert_data: dict):
    print("\n⚡ [!] Triggering autonomous agent...")
    
    with logfire.span("🤖 agent_run", alert=alert_data):
        logfire.info("📥 Alert received — starting agent run", alert=alert_data)
        
        initial_state = {
            "alert": alert_data,
            "log_summary": {},        # populated by diagnose_node via Log MCP
            "metrics_summary": {},    # populated by diagnose_node via Metrics MCP
            "diagnosis": "",
            "plan": "",
            "risk_assessment": "",
            "human_approved": False,  # set by human_approval_node
            "execution": "",
            "verified": False
        }
        
        final_state = agent_app.invoke(initial_state)
        
        verified = final_state.get("verified")
        if verified:
            logfire.info("🎉 Agent completed — service recovered!", verified=verified)
        else:
            logfire.warn("⚠️ Agent completed — service may still be down", verified=verified)
        
        print(f"{'🎉' if verified else '⚠️ '} Agent completed. Final verification status: {verified}\n")
        return final_state

