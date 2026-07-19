"""
Diagnose Node
=============
Uses the Log MCP pipeline to:
  Application → Docker Logs → Parse Logs → Extract Errors
            → Summarize → Structured JSON → LLM Diagnosis

The resulting diagnosis and log summary are stored in AgentState
so that the Planner and Execute nodes can act on real data.
"""

import sys
import os
import json
import logfire

# Add parent directory to path to allow importing state if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Add root directory for config / mcp_server imports
root_dir = os.path.dirname(parent_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from state import AgentState

# Import the Log MCP pipeline functions directly
# (avoids MCP stdio‑subprocess overhead on Windows)
sys.path.insert(0, os.path.join(root_dir, "mcp_server", "log_mcp"))
from logs_mcp import (
    _fetch_docker_logs,
    _parse_logs,
    _extract_errors,
    _summarize,
    _llm_diagnose,
)


def diagnose_node(state: AgentState) -> AgentState:
    """
    Diagnose node — runs the full Log MCP pipeline against the container
    specified in the incoming alert and stores the structured results in state.
    """
    alert = state.get("alert", {})
    container_id = alert.get("container_id", "devopsagent-app-1")
    tail = alert.get("log_tail", 200)

    with logfire.span("🔍 diagnose_node", alert=alert):
        logfire.info("🚨 Alert received — starting log-based diagnosis", alert=alert)
        print("🔍 ---DIAGNOSING ISSUE (Log MCP Pipeline)---")

        try:
            # ── Step 1: Fetch raw Docker logs ──────────────────────────────
            print(f"📥 Fetching last {tail} log lines from '{container_id}'...")
            raw_logs = _fetch_docker_logs(container_id, tail)

            if not raw_logs:
                logfire.warn("⚠️ No logs returned from container", container_id=container_id)
                print(f"⚠️  No logs returned from container '{container_id}'.")
                state["diagnosis"] = json.dumps({
                    "root_cause": f"Container '{container_id}' is not running or produces no logs.",
                    "confidence": "HIGH",
                    "impact": "Application is unreachable.",
                    "recommended_actions": ["start_container"],
                    "docker_tool_action": "start_container",
                    "docker_tool_arguments": {"container_id": container_id},
                    "urgency": "IMMEDIATE",
                })
                state["log_summary"] = {}
                return state

            # ── Step 2: Parse logs into structured entries ─────────────────
            print("🔎 Parsing log entries...")
            parsed = _parse_logs(raw_logs)

            # ── Step 3: Extract errors / anomalies ─────────────────────────
            print("🚨 Extracting error patterns...")
            errors = _extract_errors(parsed)

            # ── Step 4: Build structured summary ──────────────────────────
            print("📊 Summarising log data...")
            summary = _summarize(container_id, raw_logs, parsed, errors)

            # ── Step 5-7: LLM Diagnosis ────────────────────────────────────
            print("🤖 Sending summary to LLM for diagnosis...")
            diagnosis = _llm_diagnose(summary)

            # ── Persist results in state ───────────────────────────────────
            state["log_summary"] = summary
            state["diagnosis"] = json.dumps(diagnosis)

            logfire.info(
                "✅ Log MCP diagnosis complete",
                health=summary.get("health"),
                errors=summary["counts"]["errors"],
                diagnosis=diagnosis,
            )

            print(f"\n📋 Health:       {summary['health']}")
            print(f"   Critical:     {summary['counts']['critical']}")
            print(f"   Errors:       {summary['counts']['errors']}")
            print(f"   Warnings:     {summary['counts']['warnings']}")
            print(f"   Root Cause:   {diagnosis.get('root_cause', 'unknown')}")
            print(f"   Urgency:      {diagnosis.get('urgency', 'unknown')}")
            print(f"   Action:       {diagnosis.get('docker_tool_action', 'none')}\n")

        except Exception as exc:
            logfire.error("❌ diagnose_node error", error=str(exc))
            print(f"❌ diagnose_node encountered an error: {exc}")

            # Graceful fallback
            state["diagnosis"] = json.dumps({
                "root_cause": f"Log analysis failed: {exc}",
                "confidence": "LOW",
                "impact": "Unknown — log pipeline error.",
                "recommended_actions": ["Investigate manually", "Restart container"],
                "docker_tool_action": "restart_container",
                "docker_tool_arguments": {"container_id": container_id},
                "urgency": "SOON",
            })
            state["log_summary"] = {}

    return state
