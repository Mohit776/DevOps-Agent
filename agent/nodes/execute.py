import sys
import os
import subprocess
import logfire
import json

# Add parent directory to path to allow importing state if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from state import AgentState


def _run_docker_tool(tool_name: str, arguments: dict) -> str:
    """
    Execute a Docker CLI command based on the tool name chosen by the LLM.

    This mirrors the exact tools exposed by mcp_server/docker.py but calls
    the Docker CLI directly, avoiding the MCP stdio‑subprocess issues on
    Windows.
    """
    container_id = arguments.get("container_id", "")

    if tool_name == "list_containers":
        cmd = ["docker", "ps"]
        if arguments.get("all"):
            cmd.append("-a")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    elif tool_name == "get_container_logs":
        tail = str(arguments.get("tail", 100))
        cmd = ["docker", "logs", "--tail", tail, container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr

    elif tool_name == "start_container":
        cmd = ["docker", "start", container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully started container {container_id}"
        return f"Failed to start container: {result.stderr}"

    elif tool_name == "stop_container":
        cmd = ["docker", "stop", container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully stopped container {container_id}"
        return f"Failed to stop container: {result.stderr}"

    elif tool_name == "restart_container":
        cmd = ["docker", "restart", container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully restarted container {container_id}"
        return f"Failed to restart container: {result.stderr}"

    elif tool_name == "remove_container":
        cmd = ["docker", "rm"]
        if arguments.get("force"):
            cmd.append("-f")
        cmd.append(container_id)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Successfully removed container {container_id}"
        return f"Failed to remove container: {result.stderr}"

    else:
        return f"Unknown tool: {tool_name}"


def execute_node(state: AgentState):
    """
    Execute node.
    Parses the LLM plan and runs the appropriate Docker command.
    """
    plan = state.get("plan", "{}")
    with logfire.span("⚙️ execute_node", plan=plan):
        print("⚙️  ---EXECUTING PLAN---")
        logfire.info("🚀 Executing remediation plan", plan=plan)

        # Parse plan JSON produced by planner_node
        if isinstance(plan, str):
            try:
                plan_data = json.loads(plan)
            except json.JSONDecodeError:
                plan_data = {"action": plan, "arguments": {"container_id": "devopsagent-app-1"}}
        else:
            plan_data = plan

        tool_name = plan_data.get("action", "restart_container")
        arguments = plan_data.get("arguments", {"container_id": "devopsagent-app-1"})

        # Provide a safe fallback container_id when LLM omits it
        if "container_id" not in arguments and tool_name != "list_containers":
            arguments["container_id"] = "devopsagent-app-1"

        try:
            print(f"🐳 Executing docker tool '{tool_name}' with {arguments}...")
            output = _run_docker_tool(tool_name, arguments)

            state["execution"] = f"Tool output: {output}"
            logfire.info("✅ Docker tool executed successfully", output=output)
            print(f"✅ Docker tool executed successfully:\n{output}")
        except Exception as e:
            error_msg = f"Failed to execute docker tool: {e}"
            state["execution"] = error_msg
            logfire.error("❌ Failed to execute docker tool", error=str(e))
            print(f"❌ Error executing plan: {e}")

    return state
