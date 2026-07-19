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

        # docker_compose_up recreates the container from scratch — give it more time
        plan = state.get("plan", "{}")
        try:
            import json as _json
            plan_data = _json.loads(plan) if isinstance(plan, str) else plan
        except Exception:
            plan_data = {}
        uses_compose = any(
            s.get("tool") == "docker_compose_up"
            for s in plan_data.get("steps", [])
        )

        initial_wait = 12 if uses_compose else 5
        retry_wait   = 8  if uses_compose else 5

        print(f"Waiting {initial_wait}s for container to start...")
        time.sleep(initial_wait)

        url = "http://localhost:3000/api/health"
        max_retries = 4
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=8)
                if response.status_code == 200:
                    state["verified"] = True
                    logfire.info("Service is healthy!", status_code=response.status_code, attempt=attempt+1)
                    print("Verification successful: Service is healthy.")
                    return state
                else:
                    logfire.warn(f"Service returned {response.status_code}, retrying...", attempt=attempt+1)
                    print(f"Status code {response.status_code}. Retrying in {retry_wait}s... ({attempt+1}/{max_retries})")
            except requests.exceptions.RequestException as e:
                logfire.warn(f"Service unreachable, retrying...", error=str(e), attempt=attempt+1)
                print(f"Unreachable. Retrying in {retry_wait}s... ({attempt+1}/{max_retries})")
            
            if attempt < max_retries - 1:
                time.sleep(retry_wait)
                
        # If we exhausted all retries
        state["verified"] = False
        logfire.error("❌ Verification failed — exhausted all retries")
        print("❌ Verification failed: Service did not recover in time.")

    return state
