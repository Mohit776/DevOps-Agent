"""
kill_next.py
------------
Chaos script — stops the Next.js application Docker container.

Usage:
    python chaos/kill_next.py
    python chaos/kill_next.py --wait 10     # wait 10s then kill
"""

import subprocess
import sys
import argparse
import time


def kill_docker_next() -> bool:
    """Stop the Docker Compose service named 'app'."""
    killed_any = False

    result = subprocess.run(
        [
            "docker",
            "ps",
            "--format",
            '{{.ID}}\t{{.Names}}\t{{.Label "com.docker.compose.service"}}'
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"[!] Docker not available: {result.stderr.strip()}")
        return False

    for line in result.stdout.splitlines():
        parts = line.split("\t")

        if len(parts) != 3:
            continue

        container_id, container_name, service = parts

        if service == "app":
            stop = subprocess.run(
                ["docker", "stop", container_id],
                capture_output=True,
                text=True
            )

            if stop.returncode == 0:
                print(f"[✓] Stopped Docker service '{service}' ({container_name})")
                killed_any = True
            else:
                print(f"[!] Failed to stop '{container_name}': {stop.stderr.strip()}")

    if not killed_any:
        print("[i] No Docker Compose service 'app' is running.")

    return killed_any


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chaos script: stop the Next.js application container."
    )
    parser.add_argument("--wait", type=float, default=0, help="Seconds to wait before killing (default: 0)")
    args = parser.parse_args()

    if args.wait > 0:
        print(f"[~] Waiting {args.wait}s before triggering chaos...")
        time.sleep(args.wait)

    print("=== kill_next.py — Stopping Next.js ===\n")

    docker_killed = kill_docker_next()

    print()
    if docker_killed:
        print("[✓] Next.js has been stopped.")
        sys.exit(0)
    else:
        print("[i] Nothing was stopped — Next.js was not running.")
        sys.exit(0)
