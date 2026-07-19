"""
network.py
----------
Chaos script — simulates a network outage for a target Docker container.

Strategy:
  1. Finds the target container (by compose service, name, or image match).
  2. Inspects the container to find which Docker networks it is connected to.
  3. Disconnects the container from all its networks, causing an outage.

Usage:
    python chaos/network.py                             # isolate 'app' service
    python chaos/network.py --service mongo             # isolate mongo
    python chaos/network.py --name devopsagent-app-1    # isolate by exact name
    python chaos/network.py --wait 5                    # wait 5s then isolate
"""

import subprocess
import sys
import argparse
import time
import json


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


def _get_networks(container_id: str) -> dict:
    """Return a dictionary of network configurations for the container."""
    r = subprocess.run(
        ["docker", "inspect", "-f", "{{json .NetworkSettings.Networks}}", container_id],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        try:
            return json.loads(r.stdout.strip())
        except json.JSONDecodeError:
            pass
    return {}


# ─────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────

def network_outage(
    service_name: str = "app",
    container_name: str | None = None,
) -> bool:
    target = _find_target(service_name=service_name, container_name=container_name)

    if not target:
        identifier = container_name or f"service='{service_name}'"
        print(f"[!] No running container found matching: {identifier}")
        return False

    cid   = target["id"]
    cname = target["name"]
    print(f"[✓] Target : {cname} ({cid})  image={target['image']}")

    networks = _get_networks(cid)
    if not networks:
        print(f"[!] No networks found for container {cname}.")
        return False

    print(f"[~] Connected to {len(networks)} network(s): {', '.join(networks.keys())}")

    disconnected_networks = []

    # Disconnect from all networks
    for net, details in networks.items():
        print(f"[~] Disconnecting from '{net}'...")
        r = subprocess.run(["docker", "network", "disconnect", net, cid])
        if r.returncode == 0:
            disconnected_networks.append(net)
        else:
            print(f"[!] Failed to disconnect from '{net}'")

    if not disconnected_networks:
        print("[!] Could not disconnect from any networks. Aborting.")
        return False

    print(f"\n[✓] Container {cname} is now isolated from the network!")
    print(f"[✓] Agent must detect and recover the connection.")

    return True


# ─────────────────────────────────────────────────────────────────
# CLI entry-point
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chaos script: disconnects a Docker container from its networks."
    )
    parser.add_argument("--service",    default="app",             help="Compose service name (default: 'app')")
    parser.add_argument("--name",       default=None,              help="Exact container name (overrides --service)")
    parser.add_argument("--wait",       type=float, default=0,     help="Seconds to wait before starting (default: 0)")
    args = parser.parse_args()

    if args.wait > 0:
        print(f"[~] Waiting {args.wait}s before triggering chaos...")
        time.sleep(args.wait)

    print("=== network.py — Network Chaos ===\n")

    ok = network_outage(
        service_name=args.service,
        container_name=args.name,
    )

    sys.exit(0 if ok else 1)
