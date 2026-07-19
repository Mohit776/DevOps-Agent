import sys
import os
import requests
import logfire
import time

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
    with logfire.span("🩺 verify_node", execution=state.get("execution", "")):
        print("🩺 ---VERIFYING REMEDIATION---")
        logfire.info("🔄 Calling health endpoint to verify recovery...")

        print("⏳ Waiting 5 seconds for container to start...")
        time.sleep(5)

        url = "http://localhost:3000/api/health"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                state["verified"] = True
                logfire.info("🎉 Service is healthy!", status_code=response.status_code)
                print("🎉 Verification successful: Service is healthy.")
            else:
                state["verified"] = False
                logfire.warn("⚠️ Service returned non-200 status", status_code=response.status_code)
                print(f"⚠️  Verification failed: Status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            state["verified"] = False
            logfire.error("❌ Verification failed — service unreachable", error=str(e))
            print(f"❌ Verification failed: {e}")

    return state
