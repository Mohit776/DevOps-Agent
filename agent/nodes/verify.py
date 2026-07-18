import sys
import os
import requests

# Add parent directory to path to allow importing state if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from state import AgentState

def verify_node(state: AgentState):
    """
    Verify node.
    Calls GET /api/health to verify if the service is up.
    """
    print("---VERIFYING REMEDIATION---")
    
    url = "http://localhost:3000/api/health"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            state["verified"] = True
            print("Verification successful: Service is healthy.")
        else:
            state["verified"] = False
            print(f"Verification failed: Status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        state["verified"] = False
        print(f"Verification failed: {e}")
        
    return state
