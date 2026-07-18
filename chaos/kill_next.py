"""
kill_next.py
------------
Stops the Next.js application whether it is:
  1. Running as a local `npm run dev` / `node` process
  2. Running inside a Docker container (image or name contains "next")
"""

import subprocess
import sys

# ──────────────────────────────────────────────
# 2. Kill Next.js Docker container (if any)
# ──────────────────────────────────────────────

def kill_docker_next() -> bool:
    """Stop the Docker Compose service named 'app'."""
    killed_any = False

    result = subprocess.run(
        [
            "docker",
            "ps",
            "--format",
            "{{.ID}}\t{{.Names}}\t{{.Label \"com.docker.compose.service\"}}"
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

        # Change "app" if your compose service has a different name
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


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== kill_next.py — Stopping Next.js ===\n")

    docker_killed = kill_docker_next()

    print()
    if local_killed or docker_killed:
        print("[✓] Next.js has been stopped.")
        sys.exit(0)
    else:
        print("[i] Nothing was stopped — Next.js was not running.")
        sys.exit(0)
