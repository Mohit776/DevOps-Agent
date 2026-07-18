import asyncio
import subprocess
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Docker MCP")

@mcp.tool()
def list_containers(all: bool = False) -> str:
    """List Docker containers.
    
    Args:
        all: If True, list all containers (not just running ones).
    """
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
    cmd = ["docker", "logs", "--tail", str(tail), container_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout + result.stderr

@mcp.tool()
def start_container(container_id: str) -> str:
    """Start a Docker container.
    
    Args:
        container_id: The ID or name of the container.
    """
    cmd = ["docker", "start", container_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return f"Successfully started container {container_id}"
    return f"Failed to start container: {result.stderr}"

@mcp.tool()
def stop_container(container_id: str) -> str:
    """Stop a Docker container.
    
    Args:
        container_id: The ID or name of the container.
    """
    cmd = ["docker", "stop", container_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return f"Successfully stopped container {container_id}"
    return f"Failed to stop container: {result.stderr}"

@mcp.tool()
def restart_container(container_id: str) -> str:
    """Restart a Docker container.
    
    Args:
        container_id: The ID or name of the container.
    """
    cmd = ["docker", "restart", container_id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return f"Successfully restarted container {container_id}"
    return f"Failed to restart container: {result.stderr}"

@mcp.tool()
def remove_container(container_id: str, force: bool = False) -> str:
    """Remove a Docker container.
    
    Args:
        container_id: The ID or name of the container.
        force: If True, force the removal of a running container (uses -f).
    """
    cmd = ["docker", "rm"]
    if force:
        cmd.append("-f")
    cmd.append(container_id)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return f"Successfully removed container {container_id}"
    return f"Failed to remove container: {result.stderr}"

if __name__ == "__main__":
    # Run the server using stdin/stdout streams
    mcp.run()
