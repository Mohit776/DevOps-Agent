import sys
import os
import json
import logfire
from groq import Groq

# Add parent directory to path to allow importing state
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Add root directory to path to allow importing config
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from state import AgentState
import config

def planner_node(state: AgentState):
    """
    Planner node.
    Uses Groq LLM to reason about the alert and determine a plan.
    """
    with logfire.span("🧠 planner_node", diagnosis=state.get("diagnosis", "")):
        logfire.info("🤔 Sending alert to LLM for remediation planning...")
        print("🧠 ---PLANNING REMEDIATION (LLM)---")

        client = Groq(api_key=config.GROQ_API)
        alert_json = json.dumps(state.get("alert", {}), indent=2)

        prompt = f"""Input:
{alert_json}

The application is unavailable.
Decide the best remediation.
Return JSON only.

Example output:
{{
  "root_cause": "Application container stopped",
  "action": "restart_container",
  "risk": "LOW"
}}
"""

        response = client.chat.completions.create(
            model=config.MODEL_120B,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content

        try:
            plan_data = json.loads(content)
            state["plan"] = plan_data.get("action", content)
            logfire.info("📝 Plan generated", plan=plan_data)
            print(f"📝 Generated Plan: {plan_data}")
        except json.JSONDecodeError:
            state["plan"] = content
            logfire.warn("⚠️ LLM returned non-JSON plan", raw_output=content)
            print(f"⚠️  Generated Plan (raw): {content}")

    return state
