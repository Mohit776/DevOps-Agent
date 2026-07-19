"""
Human Approval Node
===================
If the risk classifier flags approval_required=True,
this node pauses and prompts the operator in the terminal.

A simple `y/n` prompt is shown. If the operator approves,
the flow continues to execute. Otherwise, it is aborted.
"""

import json
import logfire

from state import AgentState


def human_approval_node(state: AgentState) -> AgentState:
    """
    Human Approval node.

    Reads the plan from state and prompts the operator to approve or reject it.
    Sets state["human_approved"] = True/False.
    """
    plan_raw = state.get("plan", "{}")
    risk_raw = state.get("risk_assessment", "{}")

    try:
        plan_data = json.loads(plan_raw) if isinstance(plan_raw, str) else plan_raw
    except json.JSONDecodeError:
        plan_data = {}

    try:
        risk_data = json.loads(risk_raw) if isinstance(risk_raw, str) else risk_raw
    except json.JSONDecodeError:
        risk_data = {}

    risk_level = risk_data.get("risk", "UNKNOWN")
    steps = plan_data.get("steps", [])

    with logfire.span("🧑‍✈️ human_approval_node", risk=risk_level):
        print("\n" + "=" * 60)
        print("🚨  HUMAN APPROVAL REQUIRED")
        print(f"    Risk Level : {risk_level}")
        print("=" * 60)
        print("📋  Proposed Remediation Plan:")
        for i, step in enumerate(steps, 1):
            tool = step.get("tool", "unknown")
            args = step.get("arguments", {})
            print(f"    Step {i}: {tool}({', '.join(f'{k}={v}' for k, v in args.items())})")
        print("=" * 60)

        # Build a human-readable summary for the prompt
        if steps:
            first_step = steps[0]
            tool_name = first_step.get("tool", "operation")
            container_id = first_step.get("arguments", {}).get("container_id", "container")
            prompt_msg = f"Approve {tool_name} on '{container_id}'? (y/n): "
        else:
            prompt_msg = "Approve this remediation plan? (y/n): "

        try:
            answer = input(prompt_msg).strip().lower()
        except (EOFError, KeyboardInterrupt):
            # Non-interactive environment — default to rejected
            answer = "n"
            print("\n⚠️  Non-interactive environment — defaulting to REJECTED.")

        approved = answer in ("y", "yes")
        state["human_approved"] = approved

        if approved:
            print("✅  Plan APPROVED by operator. Proceeding with execution...\n")
            logfire.info("✅ Human approved the remediation plan", risk=risk_level)
        else:
            print("❌  Plan REJECTED by operator. Aborting execution.\n")
            logfire.warn("❌ Human rejected the remediation plan", risk=risk_level)
            state["execution"] = "Execution aborted: operator rejected the remediation plan."

    return state
