"""
kill_db.py
----------
Chaos script — kills the MongoDB database container.

It finds any running Docker container whose Compose service is named "db"
(or whose name / image contains "mongo") and forcefully stops it.

Usage:
    python chaos/kill_db.py
    python chaos/kill_db.py --service db          # target by compose service name
    python chaos/kill_db.py --name my_mongo       # target by exact container name
"""

import subprocess
import sys
import argparse
import time


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _list_running_containers() -> list[dict]:
    """Return a list of running containers as dicts with id / name / service / image."""
    result = subprocess.run(
        [
            "docker", "ps",
            "--format",
            "{{.ID}}\t{{.Names}}\t{{.Label \"com.docker.compose.service\"}}\t{{.Image}}"
        ],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"[!] Docker not available: {result.stderr.strip()}")
        return []

    containers = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            containers.append({
                "id":      parts[0],
                "name":    parts[1],
                "service": parts[2],
                "image":   parts[3],
            })
    return containers


def _stop_container(container: dict) -> bool:
    """Force-stop a single container. Returns True on success."""
    cid   = container["id"]
    cname = container["name"]

    stop = subprocess.run(
        ["docker", "stop", cid],
        capture_output=True,
        text=True
    )
    if stop.returncode == 0:
        print(f"[✓] Stopped container '{cname}' ({cid})")
        return True
    else:
        print(f"[!] Failed to stop '{cname}': {stop.stderr.strip()}")
        return False


# ─────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────

def kill_db(service_name: str = "mongo", container_name: str | None = None) -> bool:
    """
    Kill the database Docker container.

    Priority:
      1. Exact container name match (--name flag).
      2. Compose service name match   (--service flag, default "db").
      3. Fallback: any container whose name or image contains "mongo".
    """
    containers = _list_running_containers()
    if not containers:
        print("[i] No running containers found.")
        return False

    killed_any = False

    for c in containers:
        matched = False

        if container_name and c["name"] == container_name:
            matched = True
        elif not container_name and c["service"] == service_name:
            matched = True
        elif not container_name and ("mongo" in c["name"].lower() or "mongo" in c["image"].lower()):
            matched = True

        if matched:
            print(f"[~] Target found: {c['name']} (service={c['service'] or 'n/a'}, image={c['image']})")
            killed_any = _stop_container(c) or killed_any

    if not killed_any:
        identifier = container_name or f"service='{service_name}' / image~='mongo'"
        print(f"[i] No running DB container matched: {identifier}")

    return killed_any


# ─────────────────────────────────────────────────────────────────
# CLI entry-point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chaos script: kill the MongoDB / database container."
    )
    parser.add_argument(
        "--service", default="mongo",
        help="Docker Compose service name to kill (default: 'mongo')"
    )
    parser.add_argument(
        "--name", default=None,
        help="Exact container name to kill (overrides --service)"
    )
    parser.add_argument(
        "--wait", type=float, default=0,
        help="Seconds to wait before killing (for timed chaos, default: 0)"
    )
    args = parser.parse_args()

    if args.wait > 0:
        print(f"[~] Waiting {args.wait}s before triggering chaos...")
        time.sleep(args.wait)

    print("=== kill_db.py — Killing Database Container ===\n")

    success = kill_db(service_name=args.service, container_name=args.name)

    print()
    if success:
        print("[✓] Database container stopped. Agent should detect and recover it.")
        sys.exit(0)
    else:
        print("[i] Nothing was stopped — DB container was not running.")
        sys.exit(0)
