"""
Risk Classifier Node
====================
Classifies the risk of the remediation plan and determines if approval is required.
Later this node will integrate with Slack.
"""

import sys
import os
import json
import logfire
from groq import Groq

# Add parent directory to path to allow importing state
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Add root directory for config import
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from state import AgentState
import config


def risk_classifier_node(state: AgentState) -> AgentState:
    """
    Risk Classifier node.
    """
    plan_raw = state.get("plan", "{}")
    
    with logfire.span("🛡️ risk_classifier_node", plan=plan_raw):
        logfire.info("🛡️ Classifying risk of the remediation plan...")
        print("🛡️ ---CLASSIFYING RISK---")

        try:
            plan_data = json.loads(plan_raw) if isinstance(plan_raw, str) else plan_raw
        except json.JSONDecodeError:
            plan_data = {"raw_plan": plan_raw}
            
        client = Groq(api_key=config.GROQ_API)

        prompt = f"""You are a senior security and DevOps engineer. Analyze the following remediation plan and classify its risk level.
If the plan involves data deletion, major infrastructure changes, or high risk of downtime, it should require approval.

Plan:
{json.dumps(plan_data, indent=2)}

Return ONLY valid JSON with this exact structure:
{{
  "risk": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "approval_required": <boolean>
}}"""

        try:
            response = client.chat.completions.create(
                model=config.MODEL_120B,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            risk_data = json.loads(content)
            state["risk_assessment"] = json.dumps(risk_data)
            
            logfire.info("🛡️ Risk classification complete", risk=risk_data.get("risk"), approval_required=risk_data.get("approval_required"))
            print(f"🛡️ Risk Level: {risk_data.get('risk', 'UNKNOWN')}")
            print(f"   Approval Required: {risk_data.get('approval_required', False)}\n")
            
        except Exception as exc:
            logfire.error("⚠️ Risk classification failed", error=str(exc))
            print(f"⚠️ Risk classification failed: {exc}")
            
            fallback_risk = {
                "risk": "CRITICAL",
                "approval_required": True
            }
            state["risk_assessment"] = json.dumps(fallback_risk)
            print("🛡️ Falling back to CRITICAL risk (Approval Required: True)\n")

    return state
