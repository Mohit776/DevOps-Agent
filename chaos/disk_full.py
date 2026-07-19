"""
disk_full.py
------------
Chaos script — fills up disk space inside a target Docker container.

Strategy:
  1. Finds the target container (by compose service, name, or image match).
  2. Uses `docker exec` to run `dd` inside the container, writing large
     files to /tmp (writable by non-root users like `nextjs`).
  3. Optionally cleans up the files afterwards.

The agent's Metrics MCP should detect low disk space and trigger remediation.

Usage:
    python chaos/disk_full.py                            # fill 1024 MB in 'app' service
    python chaos/disk_full.py --service mongo --mb 512
    python chaos/disk_full.py --name devopsagent-app-1 --mb 2048
    python chaos/disk_full.py --mb 512 --wait 5
    python chaos/disk_full.py --no-cleanup               # leave the files to keep disk full
"""

import subprocess
import sys
import argparse
import time


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


def _exec(container_id: str, cmd: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", container_id, "sh", "-c", cmd],
        capture_output=True, text=True, check=check
    )


def _disk_free_mb(container_id: str, path: str) -> int | None:
    """Return free disk space (MB) at `path` inside the container."""
    r = _exec(container_id, f"df -m {path} | tail -1 | awk '{{print $4}}'")
    if r.returncode == 0:
        try:
            return int(r.stdout.strip())
        except ValueError:
            pass
    return None


# ─────────────────────────────────────────────────────────────────
# Core
# ─────────────────────────────────────────────────────────────────

def fill_disk(
    service_name: str = "app",
    container_name: str | None = None,
    mb: int = 1024,
    chunk_mb: int = 64,
    fill_path: str = "/tmp/chaos_disk_fill",
    hold_seconds: float = 60.0,
    no_cleanup: bool = False,
) -> bool:
    target = _find_target(service_name=service_name, container_name=container_name)

    if not target:
        identifier = container_name or f"service='{service_name}'"
        print(f"[!] No running container found matching: {identifier}")
        return False

    cid   = target["id"]
    cname = target["name"]
    print(f"[✓] Target : {cname} ({cid})  image={target['image']}")

    # Report current free space
    free = _disk_free_mb(cid, "/tmp")
    if free is not None:
        print(f"[~] Disk free before chaos : {free} MB")
        actual_mb = min(mb, max(0, free - 50))   # leave 50 MB headroom
        if actual_mb <= 0:
            print("[i] Disk is already nearly full — nothing to do.")
            return True
        if actual_mb < mb:
            print(f"[~] Capping fill at {actual_mb} MB (only {free} MB free, keeping 50 MB headroom)")
    else:
        actual_mb = mb

    print(f"[~] Plan : write {actual_mb} MB in {chunk_mb}-MB chunks → {fill_path}_*\n")

    # Write chunks
    written = 0
    chunk = 0
    try:
        while written < actual_mb:
            this_chunk = min(chunk_mb, actual_mb - written)
            chunk_path = f"{fill_path}_{chunk}"
            cmd = f"dd if=/dev/urandom of={chunk_path} bs=1M count={this_chunk} 2>&1"
            r = _exec(cid, cmd)

            if r.returncode != 0:
                # dd often exits non-zero when disk is actually full — that is intentional
                if "No space left on device" in r.stdout + r.stderr:
                    print(f"[✓] Disk is now full! (wrote ~{written} MB before device reported full)")
                    break
                print(f"[!] dd error at chunk {chunk}: {(r.stdout + r.stderr).strip()}")
                break

            written += this_chunk
            chunk   += 1
            free_now = _disk_free_mb(cid, "/tmp")
            free_str = f"{free_now} MB free" if free_now is not None else "unknown free"
            print(f"[~] Written {written} / {actual_mb} MB  ({free_str})")

    except KeyboardInterrupt:
        print("\n[!] Interrupted.")

    print(f"\n[✓] Disk filled with ~{written} MB.")
    print(f"[~] Holding for {hold_seconds}s so agent metrics can detect the condition...")
    try:
        time.sleep(hold_seconds)
    except KeyboardInterrupt:
        print("[!] Hold interrupted.")

    # Cleanup
    if not no_cleanup:
        print(f"\n[~] Cleaning up {fill_path}_* inside {cname}...")
        _exec(cid, f"rm -f {fill_path}_*")
        free_after = _disk_free_mb(cid, "/tmp")
        print(f"[✓] Cleanup done. Disk free now: {free_after} MB")
    else:
        print(f"[i] --no-cleanup set — leaving fill files at {fill_path}_* inside {cname}")

    return True


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Chaos script: fill disk space inside a Docker container."
    )
    parser.add_argument("--service",    default="app",              help="Compose service name (default: 'app')")
    parser.add_argument("--name",       default=None,              help="Exact container name (overrides --service)")
    parser.add_argument("--mb",         type=int,   default=1024,  help="MB of disk to fill (default: 1024)")
    parser.add_argument("--chunk",      type=int,   default=64,    help="MB per write chunk (default: 64)")
    parser.add_argument("--path",       default="/tmp/chaos_disk_fill", help="Prefix for fill files inside the container")
    parser.add_argument("--hold",       type=float, default=60.0,  help="Seconds to hold disk full state (default: 60)")
    parser.add_argument("--wait",       type=float, default=0,     help="Seconds to wait before starting (default: 0)")
    parser.add_argument("--no-cleanup", action="store_true",       help="Leave fill files (keep disk full)")
    args = parser.parse_args()

    if args.wait > 0:
        print(f"[~] Waiting {args.wait}s before triggering chaos...")
        time.sleep(args.wait)

    print("=== disk_full.py — Disk Chaos ===\n")

    ok = fill_disk(
        service_name=args.service,
        container_name=args.name,
        mb=args.mb,
        chunk_mb=args.chunk,
        fill_path=args.path,
        hold_seconds=args.hold,
        no_cleanup=args.no_cleanup,
    )

    sys.exit(0 if ok else 1)
