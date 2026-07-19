import sys
import os
import asyncio
import subprocess
import logfire
from mcp.server.fastmcp import FastMCP

# ── path setup so config is importable when run standalone ──────────────────
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

import config

# Configure logfire
logfire.configure(token=config.LOGFIRE_TOKEN)
logfire.info("🐳 Docker MCP Server initializing...")

# Initialize FastMCP server
mcp = FastMCP("Docker MCP")

@mcp.tool()
def list_containers(all: bool = False) -> str:
    """List Docker containers.
    
    Args:
        all: If True, list all containers (not just running ones).
    """
    with logfire.span("🐳 list_containers_tool", all=all):
        cmd = ["docker", "ps"]
        if all:
            cmd.append("-a")
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

@mcp.tool()
def get_container_logs(container_id: str, tail: int = 100) -> str:
    """Get logs for a specific Docker container.
    
    Args:
        container_id: The ID or name of the container.
        tail: Number of lines to show from the end of the logs.
    """
    with logfire.span("🐳 get_container_logs_tool", container_id=container_id, tail=tail):
        cmd = ["docker", "logs", "--tail", str(tail), container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr

@mcp.tool()
def start_container(container_id: str) -> str:
    """Start a Docker container.
    
    Args:
        container_id: The ID or name of the container.
    """
    with logfire.span("🐳 start_container_tool", container_id=container_id):
        cmd = ["docker", "start", container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logfire.info("Successfully started container", container_id=container_id)
            return f"Successfully started container {container_id}"
            
        logfire.error("Failed to start container", container_id=container_id, error=result.stderr)
        return f"Failed to start container: {result.stderr}"

@mcp.tool()
def stop_container(container_id: str) -> str:
    """Stop a Docker container.
    
    Args:
        container_id: The ID or name of the container.
    """
    with logfire.span("🐳 stop_container_tool", container_id=container_id):
        cmd = ["docker", "stop", container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logfire.info("Successfully stopped container", container_id=container_id)
            return f"Successfully stopped container {container_id}"
            
        logfire.error("Failed to stop container", container_id=container_id, error=result.stderr)
        return f"Failed to stop container: {result.stderr}"

@mcp.tool()
def restart_container(container_id: str) -> str:
    """Restart a Docker container.
    
    Args:
        container_id: The ID or name of the container.
    """
    with logfire.span("🐳 restart_container_tool", container_id=container_id):
        cmd = ["docker", "restart", container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logfire.info("Successfully restarted container", container_id=container_id)
            return f"Successfully restarted container {container_id}"
            
        logfire.error("Failed to restart container", container_id=container_id, error=result.stderr)
        return f"Failed to restart container: {result.stderr}"

@mcp.tool()
def docker_compose_up(service_name: str) -> str:
    """Run docker-compose up -d --force-recreate for a specific service.
    This is extremely useful to restore missing networks, missing volumes, or recover from fatal configuration issues.
    
    Args:
        service_name: The name of the docker-compose service (e.g. 'app', 'mongo').
    """
    with logfire.span("🐳 docker_compose_up_tool", service_name=service_name):
        # We assume docker-compose.yml is in root_dir or we can just use "docker compose" in root_dir
        cmd = ["docker", "compose", "up", "-d", "--force-recreate", service_name]
        result = subprocess.run(cmd, cwd=root_dir, capture_output=True, text=True)
        if result.returncode == 0:
            logfire.info("Successfully recreated service via compose", service_name=service_name)
            return f"Successfully recreated service {service_name}"
            
        logfire.error("Failed to recreate service", service_name=service_name, error=result.stderr)
        return f"Failed to recreate service {service_name}: {result.stderr}"

@mcp.tool()
def remove_container(container_id: str, force: bool = False) -> str:
    """Remove a Docker container.
    
    Args:
        container_id: The ID or name of the container.
        force: If True, force the removal of a running container (uses -f).
    """
    with logfire.span("🐳 remove_container_tool", container_id=container_id, force=force):
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container_id)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logfire.info("Successfully removed container", container_id=container_id)
            return f"Successfully removed container {container_id}"
            
        logfire.error("Failed to remove container", container_id=container_id, error=result.stderr)
        return f"Failed to remove container: {result.stderr}"

if __name__ == "__main__":
    # Run the server using stdin/stdout streams
    mcp.run()
