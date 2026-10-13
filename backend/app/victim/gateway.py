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
from app.security.leak_scanner import LeakScanner

class Gateway:
    """Central point for tool execution and policy enforcement."""
    
    def __init__(
        self,
        defenses: DefensePipeline,
        taint_tracker: TaintTracker | None = None,
        allowed_tools: list[str] | set[str] | None = None,
        caller_role: str = "employee",
    ) -> None:
        self.defenses = defenses
        self.taint_tracker = taint_tracker or TaintTracker()
        self.allowed_tools = set(allowed_tools) if allowed_tools is not None else None
        self.caller_role = caller_role
        self.recorded_events: list[dict[str, Any]] = []
        self.leak_scanner = LeakScanner()
        
    async def execute(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Validate, enforce policy, and execute a tool."""
        # Record proposed tool
        self.recorded_events.append({
            "type": "tool_proposed",
            "tool_name": tool_name,
            "args": args,
            "taint": self.taint_tracker.get_all_origins()
        })
        
        # 1. Validation & Allowlist Check
        if tool_name not in TOOL_REGISTRY:
            return {"error": f"Unknown tool: {tool_name}"}

        if self.allowed_tools is not None and tool_name not in self.allowed_tools:
            reason = f"Tool '{tool_name}' is not permitted in target manifest or caller role '{self.caller_role}'."
            self.recorded_events.append({
                "type": "policy_decision",
                "tool_name": tool_name,
                "allowed": False,
                "reason": reason,
            })
            return {"error": f"Authorization denied: {reason}"}
            
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
            
        # 3. Execution (Socket guard and actual run)
        from app.victim.tools import set_sandbox_tool_executing
        set_sandbox_tool_executing(True)
        try:
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
            
            # Apply taint tracking based on returned data classification
            from app.victim.taint import Taint
            def _track_taint(item: Any) -> None:
                if isinstance(item, dict) and "classification" in item:
                    domain = None
                    if item.get("is_external"):
                        domain = item.get("from_addr", "").split("@")[-1] if "from_addr" in item else "external"
                    
                    self.taint_tracker.add(Taint(
                        origin="untrusted_retrieval" if item.get("classification") == "public" else "trusted",
                        source_id=item.get("id"),
                        domain=domain
                    ))
            
            if isinstance(result, dict):
                _track_taint(result)
            elif isinstance(result, list):
                for item in result:
                    _track_taint(item)
            
            leak_report = self.leak_scanner.scan_data(result, channel=tool_name)
            if leak_report.leaked:
                self.recorded_events.append({
                    "type": "leak_detected",
                    "canary_id": leak_report.canary_id,
                    "channel": leak_report.channel,
                    "snippet": leak_report.snippet
                })
                # Redact or allow depending on mode, but for now we just record it.
                # Could replace result with {"error": "Data Exfiltration Blocked"} if policy dictates.
            
            return result
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
        finally:
            set_sandbox_tool_executing(False)

