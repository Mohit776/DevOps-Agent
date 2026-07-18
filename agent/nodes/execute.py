import sys
import os
import subprocess
import logfire

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
    plan = state.get("plan", "restart_container")
    with logfire.span("⚙️ execute_node", plan=plan):
        print(f"⚙️  ---EXECUTING PLAN: {plan}---")
        logfire.info("🚀 Executing remediation plan", plan=plan)

        try:
            print("🐳 Starting container: devopsagent-app-1...")
            subprocess.run(["docker", "start", "devopsagent-app-1"], check=True)
            state["execution"] = "Container restarted"
            logfire.info("✅ Container started successfully")
            print("✅ Container started successfully.")
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to restart container: {e}"
            state["execution"] = error_msg
            logfire.error("❌ Failed to start container", error=str(e))
            print(f"❌ Error executing plan: {e}")

    return state
