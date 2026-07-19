"""
Diagnose Node
=============
Runs two parallel pipelines to build a complete picture before planning:

  1. Log MCP Pipeline:
       Application → Docker Logs → Parse → Extract Errors → Summarize → LLM Diagnosis

  2. Metrics MCP Pipeline:
       docker stats → Parse Metrics → Container Health → Bottleneck Detection → System Summary

Both summaries are stored in AgentState and forwarded to the Planner.
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

# ── Log MCP pipeline ─────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(root_dir, "mcp_server", "log_mcp"))
from logs_mcp import (
    _fetch_docker_logs,
    _parse_logs,
    _extract_errors,
    _summarize,
    _llm_diagnose,
)

# ── Metrics MCP pipeline ─────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(root_dir, "mcp_server", "metrics_mcp"))
from metrics_mcp import (
    _fetch_docker_stats,
    _analyze_container,
    _detect_bottlenecks,
    _system_summary,
)


def diagnose_node(state: AgentState) -> AgentState:
    """
    Diagnose node — runs the full Log MCP + Metrics MCP pipelines against the
    container specified in the incoming alert and stores structured results in state.
    """
    alert = state.get("alert", {})
    container_id = alert.get("container_id", "devopsagent-app-1")
    tail = alert.get("log_tail", 200)

    with logfire.span("🔍 diagnose_node", alert=alert):
        logfire.info("🚨 Alert received — starting diagnosis", alert=alert)
        print("🔍 ---DIAGNOSING ISSUE (Log MCP + Metrics MCP)---")

        # ════════════════════════════════════════════════════════════════════
        # STEP A: Log MCP Pipeline
        # ════════════════════════════════════════════════════════════════════
        try:
            print(f"\n📥 [Log MCP] Fetching last {tail} log lines from '{container_id}'...")
            with logfire.span("📋 log_mcp_pipeline", container_id=container_id):
                raw_logs = _fetch_docker_logs(container_id, tail)

                if not raw_logs:
                    logfire.warn("⚠️ No logs returned from container", container_id=container_id)
                    print(f"⚠️  No logs returned from container '{container_id}'.")
                    state["diagnosis"] = json.dumps({
                        "root_cause": f"Container '{container_id}' is not running or produces no logs.",
                        "confidence": 1.0,
                        "evidence": [f"Container '{container_id}' produced no logs"]
                    })
                    state["log_summary"] = {}
                    state["metrics_summary"] = {}
                    return state

                parsed  = _parse_logs(raw_logs)
                errors  = _extract_errors(parsed)
                summary = _summarize(container_id, raw_logs, parsed, errors)
                state["log_summary"] = summary

                logfire.info(
                    "✅ Log MCP pipeline complete",
                    health=summary.get("health"),
                    errors=summary["counts"]["errors"],
                    warnings=summary["counts"]["warnings"],
                )
                print(f"   Log Health:   {summary['health']}")
                print(f"   Errors:       {summary['counts']['errors']}")
                print(f"   Warnings:     {summary['counts']['warnings']}")

        except Exception as exc:
            logfire.error("❌ Log MCP pipeline failed", error=str(exc))
            print(f"❌ Log MCP error: {exc}")
            state["log_summary"] = {}
            summary = {}

        # ════════════════════════════════════════════════════════════════════
        # STEP B: Metrics MCP Pipeline
        # ════════════════════════════════════════════════════════════════════
        try:
            print(f"\n📊 [Metrics MCP] Collecting resource metrics for '{container_id}'...")
            with logfire.span("📊 metrics_mcp_pipeline", container_id=container_id):
                all_stats = _fetch_docker_stats()

                if all_stats:
                    # Filter from the already-fetched batch — no second subprocess call
                    container_stats = [m for m in all_stats if m["container"] == container_id]
                    container_health = _analyze_container(container_stats[0]) if container_stats else {}

                    # System-wide view
                    bottlenecks  = _detect_bottlenecks(all_stats)
                    sys_summary  = _system_summary(all_stats)

                    metrics_summary = {
                        "container_health": container_health,
                        "system": sys_summary,
                        "bottlenecks": bottlenecks,
                    }
                    state["metrics_summary"] = metrics_summary

                    logfire.info(
                        "✅ Metrics MCP pipeline complete",
                        container_status=container_health.get("status", "UNKNOWN"),
                        overall_health=sys_summary.get("overall_health"),
                        bottleneck_count=len(bottlenecks),
                    )
                    print(f"   Container Status:  {container_health.get('status', 'UNKNOWN')}")
                    print(f"   CPU:               {container_health.get('metrics', {}).get('cpu_percent', 'N/A')}%")
                    print(f"   Memory:            {container_health.get('metrics', {}).get('mem_percent', 'N/A')}%")
                    print(f"   Bottlenecks:       {len(bottlenecks)}")
                else:
                    logfire.warn("⚠️ No container stats available")
                    state["metrics_summary"] = {}
                    metrics_summary = {}

        except Exception as exc:
            logfire.error("❌ Metrics MCP pipeline failed", error=str(exc))
            print(f"❌ Metrics MCP error: {exc}")
            state["metrics_summary"] = {}
            metrics_summary = {}

        # ════════════════════════════════════════════════════════════════════
        # STEP C: LLM Diagnosis (uses both log + metrics context)
        # ════════════════════════════════════════════════════════════════════
        try:
            print("\n🤖 Sending combined log + metrics summary to LLM for diagnosis...")
            with logfire.span("🤖 llm_diagnosis_combined", container_id=container_id):
                # Enrich the log summary with metrics and the original alert before sending to LLM
                combined = dict(summary) if summary else {}
                combined["metrics_snapshot"] = state.get("metrics_summary", {})
                combined["alert"] = alert

                diagnosis = _llm_diagnose(combined)
                state["diagnosis"] = json.dumps(diagnosis)

                logfire.info(
                    "✅ LLM diagnosis complete",
                    root_cause=diagnosis.get("root_cause"),
                    confidence=diagnosis.get("confidence"),
                )
                print(f"\n📋 Root Cause: {diagnosis.get('root_cause', 'unknown')}")
                print(f"   Confidence: {diagnosis.get('confidence', 'unknown')}")
                print(f"   Evidence:   {diagnosis.get('evidence', [])}\n")

        except Exception as exc:
            logfire.error("❌ LLM diagnosis failed", error=str(exc))
            print(f"❌ LLM diagnosis error: {exc}")
            state["diagnosis"] = json.dumps({
                "root_cause": f"Diagnosis failed: {exc}",
                "confidence": 0.0,
                "evidence": ["Diagnosis pipeline error"]
            })

    return state
