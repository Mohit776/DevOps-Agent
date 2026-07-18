from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import diagnose_node, planner_node, execute_node, verify_node

def build_graph():
    workflow = StateGraph(AgentState)
    
    # Add all our nodes
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("verify", verify_node)
    
    # Define the flow
    workflow.set_entry_point("diagnose")
    workflow.add_edge("diagnose", "planner")
    workflow.add_edge("planner", "execute")
    workflow.add_edge("execute", "verify")
    workflow.add_edge("verify", END)
    
    return workflow.compile()

agent_app = build_graph()

def run_agent(alert_data: dict):
    print("\n[!] Triggering autonomous agent...")
    initial_state = {
        "alert": alert_data,
        "diagnosis": "",
        "plan": "",
        "execution": "",
        "verified": False
    }
    
    # Invoke the langgraph state machine
    final_state = agent_app.invoke(initial_state)
    
    print(f"[✓] Agent completed. Final verification status: {final_state.get('verified')}\n")
    return final_state
