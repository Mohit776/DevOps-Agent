"""
Log MCP Server
==============
Pipeline:
  Application → Docker Logs → Parse Logs → Extract Errors
            → Summarize → Return Structured JSON → LLM Diagnosis
"""

import re
import json
import subprocess
from datetime import datetime
from typing import Optional
from groq import Groq
from mcp.server.fastmcp import FastMCP
import sys
import os
import logfire

# ── path setup so config is importable when run standalone ──────────────────
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import config  # loads GROQ_API, MODEL_120B, etc.

# Configure logfire
logfire.configure(token=config.LOGFIRE_TOKEN)
logfire.info("🔥 Log MCP Server initializing...")

# ── MCP server ───────────────────────────────────────────────────────────────
mcp = FastMCP("Log MCP")


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns that signal problems in logs
ERROR_PATTERNS = [
    # Level tags (case-insensitive)
    r"\b(error|err)\b",
    r"\b(fatal|critical|crit)\b",
    r"\b(exception|traceback|panic)\b",
    r"\b(warn(?:ing)?)\b",
    r"\b(fail(?:ed|ure)?)\b",
    r"\b(crash(?:ed)?|abort(?:ed)?)\b",
    # HTTP errors
    r"\bHTTP [45]\d{2}\b",
    r"\b[45]\d{2} [A-Z]",
    # Connection / resource issues
    r"\b(connection refused|timeout|timed out|ECONNREFUSED|ECONNRESET)\b",
    r"\b(out of memory|OOM|killed|segfault)\b",
    r"\b(no space left|disk full)\b",
    r"\b(permission denied|access denied|unauthorized|forbidden)\b",
    # Stack traces
    r"^\s+at\s+\w",                    # JS/Java stack frames
    r"^\s+File \".*\", line \d+",      # Python tracebacks
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in ERROR_PATTERNS]

SEVERITY_MAP = {
    "fatal": "CRITICAL", "critical": "CRITICAL", "crit": "CRITICAL",
    "panic": "CRITICAL",
    "error": "ERROR", "err": "ERROR", "exception": "ERROR",
    "traceback": "ERROR", "crash": "ERROR",
    "warning": "WARNING", "warn": "WARNING", "fail": "WARNING",
    "failed": "WARNING", "failure": "WARNING",
}


def _fetch_docker_logs(container_id: str, tail: int) -> str:
    """Pull logs from a Docker container (stdout + stderr)."""
    with logfire.span("🐳 fetch_docker_logs", container_id=container_id, tail=tail):
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container_id],
            capture_output=True, text=True
        )
        logs = (result.stdout + result.stderr).strip()
        logfire.info("Logs fetched", size=len(logs))
        return logs


def _parse_logs(raw: str) -> list[dict]:
    """
    Split raw log text into structured line-level entries.
    Each entry: {line_no, timestamp, level, message, raw}
    """
    with logfire.span("🔎 parse_logs", raw_size=len(raw)):
        entries = []
        ts_re = re.compile(
            r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
        )
        level_re = re.compile(
            r"\b(DEBUG|INFO|NOTICE|WARN(?:ING)?|ERROR|ERR|FATAL|CRITICAL|CRIT|PANIC)\b",
            re.IGNORECASE
        )

        for i, line in enumerate(raw.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # Try to extract timestamp
            ts_match = ts_re.search(stripped)
            timestamp = ts_match.group(1) if ts_match else None

            # Try to extract severity level
            lvl_match = level_re.search(stripped)
            level = lvl_match.group(1).upper() if lvl_match else "INFO"

            entries.append({
                "line_no": i,
                "timestamp": timestamp,
                "level": level,
                "message": stripped,
                "raw": line,
            })

        logfire.info("Parsed logs successfully", entry_count=len(entries))
        return entries


def _extract_errors(entries: list[dict]) -> list[dict]:
    """Filter entries that match any error pattern."""
    with logfire.span("🚨 extract_errors", entry_count=len(entries)):
        errors = []
        for entry in entries:
            msg = entry["message"]
            matched_patterns = []
            for pat in _COMPILED:
                if pat.search(msg):
                    matched_patterns.append(pat.pattern)

            if matched_patterns:
                # Determine severity from the message text
                severity = "WARNING"
                lower = msg.lower()
                for keyword, sev in SEVERITY_MAP.items():
                    if keyword in lower:
                        if sev == "CRITICAL":
                            severity = "CRITICAL"
                            break
                        elif sev == "ERROR" and severity != "CRITICAL":
                            severity = "ERROR"
                        elif sev == "WARNING" and severity == "WARNING":
                            severity = "WARNING"

                errors.append({
                    **entry,
                    "severity": severity,
                    "matched_patterns": matched_patterns,
                })

        logfire.info("Errors extracted", error_count=len(errors))
        return errors


def _summarize(
    container_id: str,
    raw_log: str,
    parsed: list[dict],
    errors: list[dict],
) -> dict:
    """Build a structured summary dict from parsed log data."""
    with logfire.span("📊 summarize_logs", container_id=container_id):
        total_lines = len(parsed)
        error_count = sum(1 for e in errors if e["severity"] == "ERROR")
        warning_count = sum(1 for e in errors if e["severity"] == "WARNING")
        critical_count = sum(1 for e in errors if e["severity"] == "CRITICAL")

        # Frequency analysis — top recurring error messages (normalised)
        freq: dict[str, int] = {}
        for e in errors:
            # strip timestamps and hex addresses for grouping
            key = re.sub(r"0x[0-9a-fA-F]+|\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*", "", e["message"])
            key = key.strip()[:120]
            freq[key] = freq.get(key, 0) + 1

        top_errors = sorted(freq.items(), key=lambda x: -x[1])[:5]

        # Timestamps range
        timestamps = [e["timestamp"] for e in parsed if e["timestamp"]]
        first_ts = timestamps[0] if timestamps else None
        last_ts = timestamps[-1] if timestamps else None

        # Overall health signal
        if critical_count > 0:
            health = "CRITICAL"
        elif error_count > 5:
            health = "DEGRADED"
        elif error_count > 0 or warning_count > 10:
            health = "WARNING"
        else:
            health = "HEALTHY"

        result = {
            "container_id": container_id,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "log_window": {
                "first_entry": first_ts,
                "last_entry": last_ts,
                "total_lines": total_lines,
            },
            "health": health,
            "counts": {
                "total": total_lines,
                "critical": critical_count,
                "errors": error_count,
                "warnings": warning_count,
                "anomalies": len(errors),
            },
            "top_recurring_errors": [
                {"message": msg, "occurrences": cnt} for msg, cnt in top_errors
            ],
            "raw_errors": errors[:30],  # cap payload size
        }
        logfire.info("Summary generated", health=health)
        return result


def _llm_diagnose(summary: dict) -> dict:
    """Send the structured summary to an LLM and get a diagnosis + remediation."""
    with logfire.span("🤖 llm_diagnose_logs", health=summary.get("health")):
        client = Groq(api_key=config.GROQ_API)

        prompt = f"""You are a senior DevOps SRE. Analyse the following Docker container log summary and return a structured JSON diagnosis.

Log Summary:
{json.dumps(summary, indent=2)}

Return ONLY valid JSON with this exact structure:
{{
  "root_cause": "<one-line root cause>",
  "confidence": "<HIGH|MEDIUM|LOW>",
  "impact": "<brief impact description>",
  "recommended_actions": [
    "<action 1>",
    "<action 2>"
  ],
  "docker_tool_action": "<one of: restart_container | stop_container | start_container | remove_container | get_container_logs | none>",
  "docker_tool_arguments": {{"container_id": "<name>"}},
  "urgency": "<IMMEDIATE|SOON|MONITOR>"
}}"""

        resp = client.chat.completions.create(
            model=config.MODEL_120B,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        raw = resp.choices[0].message.content
        try:
            diagnosis = json.loads(raw)
            logfire.info("LLM diagnosis successful", root_cause=diagnosis.get("root_cause"))
            return diagnosis
        except json.JSONDecodeError:
            logfire.error("LLM returned non-JSON", raw_output=raw)
            return {"raw_llm_output": raw, "parse_error": "LLM returned non-JSON"}



# ═══════════════════════════════════════════════════════════════════════════════
# Register MCP Tools
# All @mcp.tool() handlers are defined in tools.py.
# Importing it here registers them against the shared `mcp` instance.
# ═══════════════════════════════════════════════════════════════════════════════

import tools  # noqa: F401 — side-effect import; registers all @mcp.tool() decorators


# ═══════════════════════════════════════════════════════════════════════════════
# Entrypoint
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
