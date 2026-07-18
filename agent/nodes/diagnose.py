import sys
import os

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
    print("---DIAGNOSING ISSUE---")
    
    # Update the state with the diagnosis
    state["diagnosis"] = "Application container is unavailable."
    
    return state
