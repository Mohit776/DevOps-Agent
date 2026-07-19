"""
MCP Tool Definitions — Log MCP
================================
All @mcp.tool() handlers live here.
Pipeline helpers and the shared `mcp` instance are imported from logs_mcp.py.
"""

import json

# Import shared MCP instance and all pipeline helpers from the sibling module
from logs_mcp import (
    mcp,
    _fetch_docker_logs,
    _parse_logs,
    _extract_errors,
    _summarize,
    _llm_diagnose,
)
import logfire


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tools  (exposed to the LangGraph agent via MCP protocol)
# ═══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def fetch_and_parse_logs(container_id: str, tail: int = 200) -> str:
    """
    Step 1-2 of the pipeline: fetch Docker logs and parse them into structured entries.

    Args:
        container_id: Docker container name or ID.
        tail: Number of log lines to retrieve (default 200).

    Returns:
        JSON string with keys: container_id, total_lines, entries (list of parsed log objects).
    """
    with logfire.span("🛠️ fetch_and_parse_logs_tool", container_id=container_id, tail=tail):
        raw = _fetch_docker_logs(container_id, tail)
        if not raw:
            return json.dumps({
                "container_id": container_id,
                "total_lines": 0,
                "entries": [],
                "note": "No logs returned — container may not exist or produce no output."
            }, indent=2)

        parsed = _parse_logs(raw)
        return json.dumps({
            "container_id": container_id,
            "total_lines": len(parsed),
            "entries": parsed[:50],   # first 50 for brevity
        }, indent=2)


@mcp.tool()
def extract_errors_from_logs(container_id: str, tail: int = 200) -> str:
    """
    Step 3 of the pipeline: fetch logs and extract only anomalous / error lines.

    Args:
        container_id: Docker container name or ID.
        tail: Number of log lines to retrieve.

    Returns:
        JSON string with keys: container_id, total_errors, errors (list of error objects with severity).
    """
    with logfire.span("🛠️ extract_errors_from_logs_tool", container_id=container_id, tail=tail):
        raw = _fetch_docker_logs(container_id, tail)
        parsed = _parse_logs(raw)
        errors = _extract_errors(parsed)

        return json.dumps({
            "container_id": container_id,
            "total_lines_scanned": len(parsed),
            "total_errors": len(errors),
            "errors": errors[:50],
        }, indent=2)


@mcp.tool()
def summarize_logs(container_id: str, tail: int = 200) -> str:
    """
    Step 4 of the pipeline: full log fetch → parse → error extraction → structured summary.

    Args:
        container_id: Docker container name or ID.
        tail: Number of log lines to retrieve.

    Returns:
        JSON string with health signal, error counts, top recurring errors, and log window metadata.
    """
    with logfire.span("🛠️ summarize_logs_tool", container_id=container_id, tail=tail):
        raw = _fetch_docker_logs(container_id, tail)
        parsed = _parse_logs(raw)
        errors = _extract_errors(parsed)
        summary = _summarize(container_id, raw, parsed, errors)
        return json.dumps(summary, indent=2)


@mcp.tool()
def diagnose_container_logs(container_id: str, tail: int = 200) -> str:
    """
    Full pipeline (Steps 1-7): Docker Logs → Parse → Extract Errors → Summarize
    → Structured JSON → LLM Diagnosis.

    This is the primary tool for autonomous log analysis.

    Args:
        container_id: Docker container name or ID.
        tail: Number of log lines to retrieve (default 200).

    Returns:
        JSON string with 'summary' (structured log data) and 'diagnosis' (LLM analysis).
    """
    with logfire.span("🛠️ diagnose_container_logs_tool", container_id=container_id, tail=tail):
        # Steps 1-4: ingest & structure
        raw = _fetch_docker_logs(container_id, tail)
        parsed = _parse_logs(raw)
        errors = _extract_errors(parsed)
        summary = _summarize(container_id, raw, parsed, errors)

        # Step 5-7: LLM diagnosis
        diagnosis = _llm_diagnose(summary)

        result = {
            "pipeline": "Application → Docker Logs → Parse Logs → Extract Errors → Summarize → LLM Diagnosis",
            "summary": summary,
            "diagnosis": diagnosis,
        }

        return json.dumps(result, indent=2)


@mcp.tool()
def get_raw_logs(container_id: str, tail: int = 100) -> str:
    """
    Utility: retrieve raw Docker log text for a container.

    Args:
        container_id: Docker container name or ID.
        tail: Number of lines from the end (default 100).

    Returns:
        Raw log text as a string.
    """
    with logfire.span("🛠️ get_raw_logs_tool", container_id=container_id, tail=tail):
        return _fetch_docker_logs(container_id, tail)


@mcp.tool()
def health_check_container(container_id: str, tail: int = 50) -> str:
    """
    Quick health check for a container based on its recent logs.

    Args:
        container_id: Docker container name or ID.
        tail: Number of recent lines to analyse (default 50).

    Returns:
        JSON with health status (HEALTHY | WARNING | DEGRADED | CRITICAL) and a brief summary.
    """
    with logfire.span("🛠️ health_check_container_tool", container_id=container_id, tail=tail):
        raw = _fetch_docker_logs(container_id, tail)
        parsed = _parse_logs(raw)
        errors = _extract_errors(parsed)
        summary = _summarize(container_id, raw, parsed, errors)

        return json.dumps({
            "container_id": container_id,
            "health": summary["health"],
            "counts": summary["counts"],
            "top_issues": summary["top_recurring_errors"],
        }, indent=2)

