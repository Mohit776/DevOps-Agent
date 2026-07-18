import sys
import os
import logfire

# Add parent directory to path to allow importing state if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from state import AgentState

def diagnose_node(state: AgentState):
    """
    Diagnose node.
    For Version 1, this does not use an LLM and returns a hardcoded diagnosis.
    """
    with logfire.span("🔍 diagnose_node", alert=state.get("alert", {})):
        logfire.info("🚨 Alert received — starting diagnosis", alert=state.get("alert", {}))
        
        diagnosis = "Application container is unavailable."
        state["diagnosis"] = diagnosis
        
        logfire.info("✅ Diagnosis complete", diagnosis=diagnosis)
        print(f"🔍 ---DIAGNOSING ISSUE---")
        print(f"📋 Diagnosis: {diagnosis}")
    
    return state
