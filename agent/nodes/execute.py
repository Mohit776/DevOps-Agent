import sys
import os
import subprocess

# Add parent directory to path to allow importing state if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from state import AgentState

def execute_node(state: AgentState):
    """
    Execute node.
    Restarts the docker container and updates the state.
    """
    print("---EXECUTING PLAN---")
    
    try:
        # Call docker start as requested
        print("Starting container: devopsagent-app-1...")
        subprocess.run(["docker", "start", "devopsagent-app-1"], check=True)
        state["execution"] = "Container restarted"
        print("Container started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing plan: {e}")
        state["execution"] = f"Failed to restart container: {e}"
        
    return state
