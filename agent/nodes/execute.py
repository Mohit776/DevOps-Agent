import sys
import os
import json
import asyncio
import logfire

# Add parent directory to path to allow importing state if needed
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from state import AgentState

# Add mcp_server to import docker MCP
root_dir = os.path.dirname(parent_dir)
if os.path.join(root_dir, "mcp_server") not in sys.path:
    sys.path.insert(0, os.path.join(root_dir, "mcp_server"))

import docker as docker_mcp


def execute_node(state: AgentState):
    """
    Execute node.
    The executor does not know about Docker directly. It acts as an MCP client.
    It takes the structured tool calls from the plan and executes them.
    """
    plan = state.get("plan", "{}")
    
    with logfire.span("⚙️ execute_node", plan=plan):
        print("⚙️  ---EXECUTING PLAN---")
        logfire.info("🚀 Executing remediation plan via MCP")

        # Parse plan JSON produced by planner_node
        try:
            plan_data = json.loads(plan) if isinstance(plan, str) else plan
        except json.JSONDecodeError:
            plan_data = {"steps": []}
            
        steps = plan_data.get("steps", [])
        if not steps:
            state["execution"] = "No plan steps to execute."
            return state
        
        execution_results = []
        
        for step in steps:
            tool_name = step.get("tool")
            arguments = step.get("arguments", {})
            print(f"🔄 Executing step: {tool_name} with {arguments}")
            
            if not tool_name:
                execution_results.append("Step missing tool name.")
                continue
                
            try:
                # Call Docker MCP Tool asynchronously
                result = asyncio.run(docker_mcp.mcp.call_tool(tool_name, arguments))
                
                # Store Result
                execution_results.append(f"Executed '{tool_name}': {result}")
                logfire.info("✅ MCP tool executed successfully", tool=tool_name, result=result)
                
                # FastMCP returns a sequence of ContentBlocks, let's extract text if possible
                if isinstance(result, list):
                    result_text = "\n".join([r.text for r in result if hasattr(r, 'text')])
                    print(f"✅ MCP Tool result:\n{result_text}")
                else:
                    print(f"✅ MCP Tool result:\n{result}")
                    
            except Exception as e:
                error_msg = f"Failed to execute MCP tool {tool_name}: {e}"
                execution_results.append(f"ERROR executing '{tool_name}': {error_msg}")
                logfire.error("❌ Failed to execute MCP tool", error=str(e))
                print(f"❌ Error executing tool: {e}")
                
        state["execution"] = "\n".join(execution_results)

    return state
