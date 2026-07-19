"""
Planner Node
============
Converts the structured LLM diagnosis (produced by diagnose_node via Log MCP)
into an actionable remediation plan.

The planner calls the Groq LLM with the full log summary context
and the diagnosis to determine the best remediation.
"""

import sys
import os
import json
import logfire
from groq import Groq

# Add parent directory to path to allow importing state
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Add root directory for config import
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from state import AgentState
import config


def _is_network_chaos(alert: dict, diagnosis: dict) -> bool:
    """
    Return True when the alert/diagnosis strongly indicates a network-level
    disconnect (docker network disconnect), where restart_container will NOT fix
    the issue because the container loses its port bindings.

    Symptoms: 'Connection refused', 'WinError 10061', 'Max retries exceeded',
    container logs healthy but host cannot reach port 3000.
    """
    incident = str(alert.get("incident", "")).lower()
    root_cause = str(diagnosis.get("root_cause", "")).lower()
    evidence = " ".join(str(e) for e in diagnosis.get("evidence", [])).lower()

    network_keywords = [
        "connection refused",
        "winerror 10061",
        "max retries exceeded",
        "failed to establish a new connection",
        "newconnectionerror",
        "no connection could be made",
    ]
    combined = incident + " " + root_cause + " " + evidence
    return any(kw in combined for kw in network_keywords)


def planner_node(state: AgentState) -> AgentState:
    """
    Planner node.

    First checks for well-known failure patterns (rule-based) and short-circuits
    with the correct tool immediately.  Falls back to LLM planning for everything
    else.
    """
    diagnosis_raw = state.get("diagnosis", "{}")
    log_summary = state.get("log_summary", {})
    alert = state.get("alert", {})

    with logfire.span("🧠 planner_node", diagnosis=diagnosis_raw):
        logfire.info("🤔 Planning remediation based on Log MCP diagnosis...")
        print("🧠 ---PLANNING REMEDIATION---")

        # ── Parse the LLM diagnosis produced by diagnose_node ───────────────
        try:
            diagnosis = json.loads(diagnosis_raw) if isinstance(diagnosis_raw, str) else diagnosis_raw
        except json.JSONDecodeError:
            diagnosis = {}

        # ── RULE-BASED SHORT-CIRCUIT ────────────────────────────────────────
        # For network-level chaos (docker network disconnect), restart_container
        # CANNOT fix the issue because the container loses its port bindings.
        # We must use docker_compose_up to recreate the container with proper
        # network attachments. Detect this pattern without asking the LLM.
        if _is_network_chaos(alert, diagnosis):
            container_id = alert.get("container_id", "devopsagent-app-1")
            # service_name is the compose service without the stack prefix/suffix
            # e.g. "devopsagent-app-1" -> "app"
            service_name = container_id.replace("devopsagent-", "").rstrip("-1").rstrip("-")
            # strip trailing digits+dash
            import re as _re
            service_name = _re.sub(r"-\d+$", "", service_name)

            plan_data = {
                "steps": [
                    {"tool": "docker_compose_up", "arguments": {"service_name": service_name}},
                    {"tool": "get_container_logs", "arguments": {"container_id": container_id, "tail": 30}},
                ]
            }
            state["plan"] = json.dumps(plan_data)
            logfire.info("Rule-based plan: network chaos detected, using docker_compose_up",
                         service_name=service_name)
            print(f"[RULE] Network chaos detected -> using docker_compose_up({service_name})")
            print(f"Plan:\n{json.dumps(plan_data, indent=2)}")
            return state

        logfire.info("🤔 Calling LLM for plan...")

        client = Groq(api_key=config.GROQ_FALLBACK_API)

        import subprocess
        
        # Fetch the actual list of containers so the LLM knows their exact names
        r = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}} ({{.Image}}) - {{.Status}}"], capture_output=True, text=True)
        containers_list = r.stdout.strip()

        context = {
            "alert": alert,
            "log_summary": log_summary,
            "diagnosis": diagnosis,
            "available_containers": containers_list,
        }

        prompt = f"""You are a senior DevOps engineer. Given the following Docker container alert, log analysis, and diagnosis, determine the best remediation strategy.
        
IMPORTANT: When specifying a container_id in your tool arguments, you MUST use the exact container name from the 'available_containers' list provided below.
If you use 'docker_compose_up', the 'service_name' is typically 'app' or 'mongo' (without the prefix/suffix).

Context:
{json.dumps(context, indent=2)}

Available Docker tools:
  - start_container (arguments: container_id)
  - stop_container (arguments: container_id)
  - restart_container (arguments: container_id)
  - docker_compose_up (arguments: service_name)  <-- USE THIS if network/volume is missing, container is fully dead, or Connection Refused
  - remove_container (arguments: container_id, force)
  - list_containers (arguments: all)
  - get_container_logs (arguments: container_id, tail)

Return ONLY valid JSON with this exact structure:
{{
  "steps": [
    {{
      "tool": "<tool_name>",
      "arguments": {{
        "<arg_name>": "<arg_value>"
      }}
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model=config.MODEL_120B,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        try:
            plan_data = json.loads(content)
            state["plan"] = json.dumps(plan_data)
            logfire.info("📝 Plan generated by LLM", plan=plan_data)
            print(f"📝 Generated Plan:\n{json.dumps(plan_data, indent=2)}")
        except json.JSONDecodeError:
            state["plan"] = content
            logfire.warn("⚠️ LLM returned non-JSON plan", raw_output=content)
            print(f"⚠️  Generated Plan (raw): {content}")

    return state


