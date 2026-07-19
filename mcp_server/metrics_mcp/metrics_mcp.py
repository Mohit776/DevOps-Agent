"""
Metrics MCP Server
==================
Pipeline:
  Docker Stats → Parse Metrics → Health Analysis → Resource Bottleneck Detection
              → Top Consumers → System Summary → LLM Diagnosis

Tools exposed:
  - analyze_container_health(container_id)
  - detect_resource_bottleneck()
  - top_resource_consumers()
  - system_summary()
"""

import re
import json
import subprocess
from datetime import datetime
from groq import Groq
from mcp.server.fastmcp import FastMCP
import sys
import os
import logfire

# ── path setup so config is importable when run standalone ──────────────────
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import config

# Configure logfire
logfire.configure(token=config.LOGFIRE_TOKEN)
logfire.info("📊 Metrics MCP Server initializing...")

# ── MCP server ───────────────────────────────────────────────────────────────
mcp = FastMCP("Metrics MCP")


# ═══════════════════════════════════════════════════════════════════════════════
# Thresholds
# ═══════════════════════════════════════════════════════════════════════════════

THRESHOLDS = {
    "cpu_warning":    60.0,   # %
    "cpu_critical":   85.0,
    "mem_warning":    70.0,   # %
    "mem_critical":   90.0,
    "net_rx_warning": 50,     # MB/s
    "net_rx_critical":100,
    "block_warning":  100,    # MB/s (combined I/O)
    "block_critical": 500,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_size_to_mb(value: str) -> float:
    """
    Convert Docker-style size string (e.g. '1.23MiB', '512kB', '2.1GB')
    to a float in MB.
    """
    value = value.strip()
    units = {
        "b":   1 / (1024 * 1024),
        "kb":  1 / 1024,
        "kib": 1 / 1024,
        "mb":  1.0,
        "mib": 1.0,
        "gb":  1024.0,
        "gib": 1024.0,
        "tb":  1024 * 1024.0,
        "tib": 1024 * 1024.0,
    }
    match = re.match(r"^([\d.]+)\s*([a-zA-Z]+)$", value)
    if not match:
        return 0.0
    num, unit = float(match.group(1)), match.group(2).lower()
    return num * units.get(unit, 1.0)


def _fetch_docker_stats(container_id: str | None = None) -> list[dict]:
    """
    Run `docker stats --no-stream` and return a list of metric dicts.
    If container_id is given, only stats for that container are returned.
    """
    with logfire.span("📡 fetch_docker_stats", container_id=container_id or "all"):
        cmd = ["docker", "stats", "--no-stream",
               "--format",
               "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t"
               "{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}"]

        if container_id:
            cmd.append(container_id)

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logfire.error("docker stats failed", stderr=result.stderr)
            return []

        rows = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue

            name, cpu_pct, mem_usage, mem_pct, net_io, block_io, pids = parts

            # Parse CPU %
            cpu = float(cpu_pct.replace("%", "").strip() or 0)

            # Parse memory  e.g. "123MiB / 1GiB"
            mem_parts = mem_usage.split("/")
            mem_used_mb = _parse_size_to_mb(mem_parts[0]) if len(mem_parts) > 0 else 0.0
            mem_limit_mb = _parse_size_to_mb(mem_parts[1]) if len(mem_parts) > 1 else 0.0
            mem_percent = float(mem_pct.replace("%", "").strip() or 0)

            # Parse net I/O  e.g. "1.5MB / 300kB"
            net_parts = net_io.split("/")
            net_rx_mb = _parse_size_to_mb(net_parts[0]) if len(net_parts) > 0 else 0.0
            net_tx_mb = _parse_size_to_mb(net_parts[1]) if len(net_parts) > 1 else 0.0

            # Parse block I/O  e.g. "8MB / 0B"
            blk_parts = block_io.split("/")
            blk_read_mb = _parse_size_to_mb(blk_parts[0]) if len(blk_parts) > 0 else 0.0
            blk_write_mb = _parse_size_to_mb(blk_parts[1]) if len(blk_parts) > 1 else 0.0

            rows.append({
                "container": name.strip(),
                "cpu_percent": cpu,
                "mem_used_mb": round(mem_used_mb, 2),
                "mem_limit_mb": round(mem_limit_mb, 2),
                "mem_percent": mem_percent,
                "net_rx_mb": round(net_rx_mb, 2),
                "net_tx_mb": round(net_tx_mb, 2),
                "block_read_mb": round(blk_read_mb, 2),
                "block_write_mb": round(blk_write_mb, 2),
                "pids": int(pids.strip() or 0),
            })

        logfire.info("Stats fetched", container_count=len(rows))
        return rows


def _health_status(metrics: dict) -> str:
    """Return HEALTHY | WARNING | CRITICAL based on thresholds."""
    if (metrics["cpu_percent"] >= THRESHOLDS["cpu_critical"] or
            metrics["mem_percent"] >= THRESHOLDS["mem_critical"]):
        return "CRITICAL"
    if (metrics["cpu_percent"] >= THRESHOLDS["cpu_warning"] or
            metrics["mem_percent"] >= THRESHOLDS["mem_warning"]):
        return "WARNING"
    return "HEALTHY"


def _analyze_container(metrics: dict) -> dict:
    """Build a detailed health report for a single container."""
    with logfire.span("🔬 analyze_container", container=metrics["container"]):
        status = _health_status(metrics)
        issues = []

        if metrics["cpu_percent"] >= THRESHOLDS["cpu_critical"]:
            issues.append(f"CPU critically high: {metrics['cpu_percent']:.1f}%")
        elif metrics["cpu_percent"] >= THRESHOLDS["cpu_warning"]:
            issues.append(f"CPU elevated: {metrics['cpu_percent']:.1f}%")

        if metrics["mem_percent"] >= THRESHOLDS["mem_critical"]:
            issues.append(f"Memory critically high: {metrics['mem_percent']:.1f}%")
        elif metrics["mem_percent"] >= THRESHOLDS["mem_warning"]:
            issues.append(f"Memory elevated: {metrics['mem_percent']:.1f}%")

        blk_total = metrics["block_read_mb"] + metrics["block_write_mb"]
        if blk_total >= THRESHOLDS["block_critical"]:
            issues.append(f"Block I/O critically high: {blk_total:.1f} MB")
        elif blk_total >= THRESHOLDS["block_warning"]:
            issues.append(f"Block I/O elevated: {blk_total:.1f} MB")

        report = {
            "container": metrics["container"],
            "status": status,
            "issues": issues,
            "metrics": metrics,
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        }

        logfire.info("Container health analyzed", container=metrics["container"], status=status)
        return report


def _detect_bottlenecks(all_metrics: list[dict]) -> list[dict]:
    """Scan all containers and flag those exceeding any threshold."""
    with logfire.span("🚨 detect_bottlenecks", container_count=len(all_metrics)):
        bottlenecks = []

        for m in all_metrics:
            triggered = []

            if m["cpu_percent"] >= THRESHOLDS["cpu_critical"]:
                triggered.append({"resource": "cpu", "severity": "CRITICAL",
                                   "value": m["cpu_percent"], "threshold": THRESHOLDS["cpu_critical"]})
            elif m["cpu_percent"] >= THRESHOLDS["cpu_warning"]:
                triggered.append({"resource": "cpu", "severity": "WARNING",
                                   "value": m["cpu_percent"], "threshold": THRESHOLDS["cpu_warning"]})

            if m["mem_percent"] >= THRESHOLDS["mem_critical"]:
                triggered.append({"resource": "memory", "severity": "CRITICAL",
                                   "value": m["mem_percent"], "threshold": THRESHOLDS["mem_critical"]})
            elif m["mem_percent"] >= THRESHOLDS["mem_warning"]:
                triggered.append({"resource": "memory", "severity": "WARNING",
                                   "value": m["mem_percent"], "threshold": THRESHOLDS["mem_warning"]})

            blk = m["block_read_mb"] + m["block_write_mb"]
            if blk >= THRESHOLDS["block_critical"]:
                triggered.append({"resource": "block_io", "severity": "CRITICAL",
                                   "value": blk, "threshold": THRESHOLDS["block_critical"]})
            elif blk >= THRESHOLDS["block_warning"]:
                triggered.append({"resource": "block_io", "severity": "WARNING",
                                   "value": blk, "threshold": THRESHOLDS["block_warning"]})

            if triggered:
                bottlenecks.append({"container": m["container"], "bottlenecks": triggered})

        logfire.info("Bottleneck detection complete",
                     bottleneck_count=len(bottlenecks),
                     containers_affected=[b["container"] for b in bottlenecks])
        return bottlenecks


def _top_consumers(all_metrics: list[dict], top_n: int = 5) -> dict:
    """Return top N containers by CPU, memory, and I/O usage."""
    with logfire.span("🏆 top_consumers", top_n=top_n):
        by_cpu = sorted(all_metrics, key=lambda x: x["cpu_percent"], reverse=True)[:top_n]
        by_mem = sorted(all_metrics, key=lambda x: x["mem_percent"], reverse=True)[:top_n]
        by_io  = sorted(all_metrics,
                        key=lambda x: x["block_read_mb"] + x["block_write_mb"],
                        reverse=True)[:top_n]

        result = {
            "top_cpu": [{"container": m["container"], "cpu_percent": m["cpu_percent"]} for m in by_cpu],
            "top_memory": [{"container": m["container"],
                            "mem_percent": m["mem_percent"],
                            "mem_used_mb": m["mem_used_mb"]} for m in by_mem],
            "top_block_io": [{"container": m["container"],
                               "block_total_mb": round(m["block_read_mb"] + m["block_write_mb"], 2)}
                              for m in by_io],
        }

        logfire.info("Top consumers identified",
                     top_cpu=result["top_cpu"][0]["container"] if result["top_cpu"] else "none",
                     top_mem=result["top_memory"][0]["container"] if result["top_memory"] else "none")
        return result


def _system_summary(all_metrics: list[dict]) -> dict:
    """Aggregate system-wide metrics across all containers."""
    with logfire.span("🌐 system_summary", container_count=len(all_metrics)):
        if not all_metrics:
            return {"error": "No running containers found"}

        total_cpu = sum(m["cpu_percent"] for m in all_metrics)
        avg_cpu   = total_cpu / len(all_metrics)
        total_mem = sum(m["mem_used_mb"] for m in all_metrics)
        avg_mem   = sum(m["mem_percent"] for m in all_metrics) / len(all_metrics)
        total_rx  = sum(m["net_rx_mb"] for m in all_metrics)
        total_tx  = sum(m["net_tx_mb"] for m in all_metrics)
        total_blk = sum(m["block_read_mb"] + m["block_write_mb"] for m in all_metrics)
        total_pids = sum(m["pids"] for m in all_metrics)

        critical = [m["container"] for m in all_metrics if _health_status(m) == "CRITICAL"]
        warnings = [m["container"] for m in all_metrics if _health_status(m) == "WARNING"]

        overall_health = "HEALTHY"
        if critical:
            overall_health = "CRITICAL"
        elif warnings:
            overall_health = "WARNING"

        summary = {
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_health": overall_health,
            "container_count": len(all_metrics),
            "critical_containers": critical,
            "warning_containers": warnings,
            "totals": {
                "cpu_percent_sum": round(total_cpu, 2),
                "avg_cpu_percent": round(avg_cpu, 2),
                "total_mem_used_mb": round(total_mem, 2),
                "avg_mem_percent": round(avg_mem, 2),
                "total_net_rx_mb": round(total_rx, 2),
                "total_net_tx_mb": round(total_tx, 2),
                "total_block_io_mb": round(total_blk, 2),
                "total_pids": total_pids,
            },
        }

        logfire.info("System summary generated",
                     overall_health=overall_health,
                     container_count=len(all_metrics),
                     critical_count=len(critical),
                     warning_count=len(warnings))
        return summary


def _llm_diagnose_metrics(summary: dict, bottlenecks: list[dict]) -> dict:
    """Send metrics summary + bottlenecks to an LLM for root-cause analysis."""
    with logfire.span("🤖 llm_diagnose_metrics", overall_health=summary.get("overall_health")):
        client = Groq(api_key=config.GROQ_API)

        prompt = f"""You are a senior DevOps SRE. Analyse the following Docker container metrics summary and return a structured JSON diagnosis.

Metrics Summary:
{json.dumps(summary, indent=2)}

Detected Bottlenecks:
{json.dumps(bottlenecks, indent=2)}

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
  "docker_tool_arguments": {{"container_id": "<name or empty if none>"}},
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
            logfire.info("LLM metrics diagnosis successful",
                         root_cause=diagnosis.get("root_cause"),
                         urgency=diagnosis.get("urgency"))
            return diagnosis
        except json.JSONDecodeError:
            logfire.error("LLM returned non-JSON", raw_output=raw)
            return {"raw_llm_output": raw, "parse_error": "LLM returned non-JSON"}


# ═══════════════════════════════════════════════════════════════════════════════
# Register MCP Tools (side-effect import)
# ═══════════════════════════════════════════════════════════════════════════════

import tools  # noqa: F401


# ═══════════════════════════════════════════════════════════════════════════════
# Entrypoint
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
