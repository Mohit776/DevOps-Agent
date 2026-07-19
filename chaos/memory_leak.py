"""
memory_leak.py
--------------
Chaos script — causes the Next.js container to become unhealthy via memory
pressure.

Strategy:
  Two modes available:
  1. (Default) Kill the main Node.js process inside the container using
     `kill 1`, which terminates server.js. Docker's restart policy will
     bring it back, but the agent should detect the outage first.
  2. (--flood) HTTP-flood the /api/health endpoint with concurrent requests
     to simulate heavy load and potential memory pressure.

Usage:
    python chaos/memory_leak.py                        # kill PID 1 in app container
    python chaos/memory_leak.py --service mongo        # target mongo container
    python chaos/memory_leak.py --name devopsagent-app-1
    python chaos/memory_leak.py --flood --duration 30  # HTTP flood for 30s
    python chaos/memory_leak.py --wait 5               # wait 5s then trigger
"""

import subprocess
import sys
import argparse
import time
import concurrent.futures
import urllib.request
import urllib.error


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _list_running_containers() -> list[dict]:
    result = subprocess.run(
        [
            "docker", "ps",
            "--format",
            '{{.ID}}\t{{.Names}}\t{{.Label "com.docker.compose.service"}}\t{{.Image}}'
        ],
        capture_output=True, text=True
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


def _find_target(
    service_name: str = "app",
    container_name: str | None = None,
) -> dict | None:
    for c in _list_running_containers():
        if container_name and c["name"] == container_name:
            return c
        if not container_name and c["service"] == service_name:
            return c
    return None


# ─────────────────────────────────────────────────────────────────
# Mode 1: Kill main process (PID 1)
# ─────────────────────────────────────────────────────────────────

def kill_main_process(
    service_name: str = "app",
    container_name: str | None = None,
) -> bool:
    """Kill the main process (PID 1) inside the target container.
    
    This causes the container to exit. If Docker's restart policy is
    'unless-stopped' or 'always', the container will restart automatically,
    but the agent should detect the brief downtime.
    """
    target = _find_target(service_name=service_name, container_name=container_name)

    if not target:
        identifier = container_name or f"service='{service_name}'"
        print(f"[!] No running container found matching: {identifier}")
        return False

    cid   = target["id"]
    cname = target["name"]
    print(f"[✓] Target : {cname} ({cid})  image={target['image']}")
    print(f"[~] Killing main process (PID 1) inside container...\n")

    # Send SIGKILL to PID 1 — this terminates the container immediately
    r = subprocess.run(
        ["docker", "kill", "--signal=SIGKILL", cid],
        capture_output=True, text=True
    )

    if r.returncode == 0:
        print(f"[✓] Container {cname} has been killed!")
        print(f"[~] Docker restart policy should bring it back up.")
        print(f"[~] The DevOps agent should detect the outage and respond.")
        return True
    else:
        print(f"[!] Failed to kill container: {r.stderr.strip()}")
        return False


# ─────────────────────────────────────────────────────────────────
# Mode 2: HTTP flood
# ─────────────────────────────────────────────────────────────────

def _send_request(url: str) -> tuple[int, str]:
    """Send a single HTTP request. Returns (status_code, error_or_empty)."""
    try:
        req = urllib.request.urlopen(url, timeout=3)
        return (req.status, "")
    except urllib.error.HTTPError as e:
        return (e.code, str(e))
    except Exception as e:
        return (0, str(e))


def http_flood(
    url: str = "http://localhost:3000/api/health",
    duration: float = 30.0,
    concurrency: int = 50,
) -> bool:
    """Flood the app with concurrent HTTP requests to stress it."""
    print(f"[✓] Target URL : {url}")
    print(f"[~] Flood plan : {concurrency} concurrent workers for {duration}s\n")

    total = 0
    errors = 0
    start = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        while (time.time() - start) < duration:
            futures = [pool.submit(_send_request, url) for _ in range(concurrency)]
            for f in concurrent.futures.as_completed(futures):
                status, err = f.result()
                total += 1
                if status != 200:
                    errors += 1

            elapsed = time.time() - start
            rps = total / elapsed if elapsed > 0 else 0
            print(f"[~] {total} requests ({errors} errors) — {rps:.0f} req/s — {elapsed:.1f}s elapsed")

    print(f"\n[✓] Flood complete: {total} total requests, {errors} errors")
    return True


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chaos script: cause memory pressure / crash in a Docker container."
    )
    parser.add_argument("--service",     default="app",             help="Compose service name (default: 'app')")
    parser.add_argument("--name",        default=None,              help="Exact container name (overrides --service)")
    parser.add_argument("--flood",       action="store_true",       help="Use HTTP flood mode instead of process kill")
    parser.add_argument("--duration",    type=float, default=30.0,  help="Flood duration in seconds (default: 30)")
    parser.add_argument("--concurrency", type=int,   default=50,    help="Concurrent flood workers (default: 50)")
    parser.add_argument("--url",         default="http://localhost:3000/api/health", help="URL to flood")
    parser.add_argument("--wait",        type=float, default=0,     help="Seconds to wait before starting (default: 0)")
    args = parser.parse_args()

    if args.wait > 0:
        print(f"[~] Waiting {args.wait}s before triggering chaos...")
        time.sleep(args.wait)

    print("=== memory_leak.py — Memory / Crash Chaos ===\n")

    if args.flood:
        ok = http_flood(
            url=args.url,
            duration=args.duration,
            concurrency=args.concurrency,
        )
    else:
        ok = kill_main_process(
            service_name=args.service,
            container_name=args.name,
        )

    sys.exit(0 if ok else 1)