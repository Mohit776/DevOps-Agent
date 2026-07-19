"""
Metrics MCP Tools
=================
All @mcp.tool() handlers.  The shared `mcp` instance and pipeline helpers
are imported from metrics_mcp.py.
"""

import json
import logfire

# Import shared MCP instance and all pipeline helpers
from metrics_mcp import (
    mcp,
    _fetch_docker_stats,
    _analyze_container,
    _detect_bottlenecks,
    _top_consumers,
    _system_summary,
    _llm_diagnose_metrics,
)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool: analyze_container_health
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def analyze_container_health(container_id: str) -> str:
    """Analyse CPU, memory, network, and block I/O health of a single container.

    Args:
        container_id: The name or ID of the Docker container.

    Returns:
        JSON with health status (HEALTHY | WARNING | CRITICAL), detected issues,
        and full metric snapshot.
    """
    with logfire.span("🛠️ analyze_container_health_tool", container_id=container_id):
        stats = _fetch_docker_stats(container_id)

        if not stats:
            result = {
                "container": container_id,
                "status": "UNKNOWN",
                "issues": ["Container not found or not running"],
                "metrics": {},
            }
            logfire.error("Container not found", container_id=container_id)
            return json.dumps(result, indent=2)

        report = _analyze_container(stats[0])
        logfire.info("analyze_container_health complete",
                     container=container_id,
                     status=report["status"])
        return json.dumps(report, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool: detect_resource_bottleneck
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def detect_resource_bottleneck() -> str:
    """Scan all running containers and detect any that exceed CPU, memory, or I/O thresholds.

    Returns:
        JSON with a list of containers that have bottlenecks, the affected
        resource, severity (WARNING | CRITICAL), current value, and threshold.
    """
    with logfire.span("🛠️ detect_resource_bottleneck_tool"):
        all_stats = _fetch_docker_stats()

        if not all_stats:
            return json.dumps({"bottlenecks": [], "note": "No running containers found."}, indent=2)

        bottlenecks = _detect_bottlenecks(all_stats)

        result = {
            "total_containers_scanned": len(all_stats),
            "bottleneck_count": len(bottlenecks),
            "bottlenecks": bottlenecks,
        }

        logfire.info("detect_resource_bottleneck complete",
                     scanned=len(all_stats),
                     bottlenecks_found=len(bottlenecks))
        return json.dumps(result, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool: top_resource_consumers
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def top_resource_consumers(top_n: int = 5) -> str:
    """Return the top N containers ranked by CPU, memory, and block I/O usage.

    Args:
        top_n: How many containers to include in each ranked list (default: 5).

    Returns:
        JSON with three ranked lists: top_cpu, top_memory, top_block_io.
    """
    with logfire.span("🛠️ top_resource_consumers_tool", top_n=top_n):
        all_stats = _fetch_docker_stats()

        if not all_stats:
            return json.dumps({"top_cpu": [], "top_memory": [], "top_block_io": [],
                                "note": "No running containers found."}, indent=2)

        consumers = _top_consumers(all_stats, top_n)
        logfire.info("top_resource_consumers complete", top_n=top_n)
        return json.dumps(consumers, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool: system_summary
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def system_summary(diagnose: bool = False) -> str:
    """Generate a system-wide aggregated metrics summary across all running containers.

    Optionally triggers an LLM diagnosis of the metrics if bottlenecks are found.

    Args:
        diagnose: If True, pass the summary and bottlenecks to the LLM for root-cause analysis.

    Returns:
        JSON with overall health, container counts, aggregated totals, critical/warning
        container lists, and optionally an LLM diagnosis.
    """
    with logfire.span("🛠️ system_summary_tool", diagnose=diagnose):
        all_stats = _fetch_docker_stats()

        if not all_stats:
            return json.dumps({
                "overall_health": "UNKNOWN",
                "container_count": 0,
                "note": "No running containers found.",
            }, indent=2)

        summary = _system_summary(all_stats)
        bottlenecks = _detect_bottlenecks(all_stats)

        result = {
            "pipeline": "Docker Stats → Parse → Aggregate → System Summary",
            "summary": summary,
            "bottlenecks": bottlenecks,
        }

        if diagnose and (summary.get("critical_containers") or summary.get("warning_containers")):
            logfire.info("Triggering LLM diagnosis for system summary",
                         overall_health=summary.get("overall_health"))
            diagnosis = _llm_diagnose_metrics(summary, bottlenecks)
            result["diagnosis"] = diagnosis

        logfire.info("system_summary complete",
                     overall_health=summary.get("overall_health"),
                     container_count=summary.get("container_count"))
        return json.dumps(result, indent=2)
