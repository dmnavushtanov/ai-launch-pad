# backend/workflows/sequential_workflow.py
# This file contains the sequential workflow implementation that executes agents one after another
# Purpose: Execute agents in a predefined sequential order with context passing, progress tracking, and failure recovery

from typing import Dict, Any, Optional, List

from .base_workflow import BaseWorkflow
from ..agents.base_agent import AgentState


class SequentialWorkflow(BaseWorkflow):
    """Execute agents in sequential order with failure recovery."""
    
    def __init__(self, *args, **kwargs):
        """Initialize sequential workflow with checkpoint support."""
        super().__init__(*args, **kwargs)
        self._checkpoints: List[Dict[str, Any]] = []
        self._failed_step: Optional[int] = None
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute agents sequentially with failure recovery.
        
        Args:
            task: Task to execute
            context: Optional context information
            
        Returns:
            Combined results from all agents
        """
        if not self.agents:
            raise ValueError("No agents configured for workflow")
        
        # Initialize context
        if context is None:
            context = {}
        
        # Check if recovering from failure
        start_step = 0
        if self._failed_step is not None and self._checkpoints:
            start_step = self._failed_step
            context = self._checkpoints[-1]["context"].copy()
            self.logger.info(f"🔄 Recovering from step {start_step}")
        
        # Track results
        results = []
        current_task = task
        
        # Load previous results if recovering
        if start_step > 0 and self._checkpoints:
            results = self._checkpoints[-1]["results"].copy()
            if results:
                current_task = results[-1]["output"]
        
        # Execute each agent
        for i in range(start_step, len(self.agents)):
            agent = self.agents[i]
            
            # Update step counter
            self._current_step = i + 1
            
            # Check step limit
            if self._current_step > self.max_steps:
                raise RuntimeError(f"Exceeded maximum steps: {self.max_steps}")
            
            # Log progress
            progress = (self._current_step / len(self.agents)) * 100
            self.logger.info(f"📊 Progress: {progress:.0f}% - Step {self._current_step}/{len(self.agents)}: {agent.name}")
            
            try:
                # Execute agent
                agent_result = agent._execute_with_error_handling(current_task, context)
                
                # Store result
                results.append({
                    "agent": agent.name,
                    "input": current_task,
                    "output": agent_result,
                    "step": self._current_step
                })
                
                # Update context
                context[f"{agent.name}_output"] = agent_result
                
                # Save checkpoint after successful execution
                self._save_checkpoint(results, context)
                
                # Use output as next input
                current_task = agent_result
                
            except Exception as e:
                self.logger.error(f"❌ Agent {agent.name} failed: {str(e)}")
                self._failed_step = i
                
                # Try recovery
                if self._attempt_recovery(agent, current_task, context):
                    # Retry the failed agent
                    agent_result = agent._execute_with_error_handling(current_task, context)
                    results.append({
                        "agent": agent.name,
                        "input": current_task,
                        "output": agent_result,
                        "step": self._current_step,
                        "recovered": True
                    })
                    context[f"{agent.name}_output"] = agent_result
                    current_task = agent_result
                    self._failed_step = None
                else:
                    # Recovery failed, propagate error
                    raise
        
        # Clear failure state on success
        self._failed_step = None
        self._checkpoints.clear()
        
        return {
            "workflow_type": "sequential",
            "total_steps": self._current_step,
            "agents_executed": len(results),
            "results": results,
            "final_output": results[-1]["output"] if results else None,
            "context": context
        }
    
    def _save_checkpoint(self, results: List[Dict[str, Any]], context: Dict[str, Any]) -> None:
        """Save execution checkpoint for recovery."""
        checkpoint = {
            "step": self._current_step,
            "results": results.copy(),
            "context": context.copy()
        }
        self._checkpoints.append(checkpoint)
        
        # Keep only last 3 checkpoints
        if len(self._checkpoints) > 3:
            self._checkpoints.pop(0)
    
    def _attempt_recovery(self, agent: Any, task: str, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from agent failure.
        
        Args:
            agent: Failed agent
            task: Current task
            context: Current context
            
        Returns:
            True if recovery successful
        """
        try:
            self.logger.info(f"🔧 Attempting recovery for {agent.name}")
            
            # Reset agent state
            agent._set_state(AgentState.IDLE)
            
            # Clear agent's last execution from history
            if agent._execution_history:
                agent._execution_history.pop()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Recovery failed: {str(e)}")
            return False
    
    def reset(self) -> None:
        """Reset workflow state and checkpoints."""
        self.clear_history()
        self._checkpoints.clear()
        self._failed_step = None
        self._set_state(self.state.IDLE)
        self.logger.info("🔄 Workflow reset complete") 