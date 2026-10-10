"""
Tool execution gateway.
Provides a central choke-point for all tool execution, enabling
policy enforcement, taint tracking, and event recording.
"""
from __future__ import annotations
from typing import Any
import asyncio

from app.defenses import DefensePipeline
from app.victim.tools import TOOL_REGISTRY
from app.victim.taint import TaintTracker

class Gateway:
    """Central point for tool execution and policy enforcement."""
    
    def __init__(self, defenses: DefensePipeline, taint_tracker: TaintTracker | None = None) -> None:
        self.defenses = defenses
        self.taint_tracker = taint_tracker or TaintTracker()
        self.recorded_events: list[dict[str, Any]] = []
        
    async def execute(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Validate, enforce policy, and execute a tool."""
        # Record proposed tool
        self.recorded_events.append({
            "type": "tool_proposed",
            "tool_name": tool_name,
            "args": args,
            "taint": self.taint_tracker.get_all_origins()
        })
        
        # 1. Validation
        if tool_name not in TOOL_REGISTRY:
            return {"error": f"Unknown tool: {tool_name}"}
            
        tool_func = TOOL_REGISTRY[tool_name]
        
        # 2. Policy Pipeline (pre_tool)
        allowed, reason = self.defenses.apply_pre_tool(tool_name, args)
        
        self.recorded_events.append({
            "type": "policy_decision",
            "tool_name": tool_name,
            "allowed": allowed,
            "reason": reason
        })
        
        if not allowed:
            # Check if it's an approval gate
            if "approval" in reason.lower():
                return {"error": "Pending human approval. " + reason}
            return {"error": f"Policy denied: {reason}"}
            
        # 3. Execution (Simulation of socket guard and actual run)
        try:
            # Here we would enter a socket guard context
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**args)
            else:
                result = tool_func(**args)
                
            if isinstance(result, str):
                result = self.defenses.apply_post_retrieval(tool_name, result)
                
            self.recorded_events.append({
                "type": "tool_result",
                "tool_name": tool_name,
                "result": result
            })
            return result
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
