# backend/workflows/base_workflow.py
# This file contains the abstract base workflow class for managing agent execution patterns
# Purpose: Provide a simple framework for orchestrating multi-agent workflows with state management and error handling

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

from ..agents.base_agent import BaseAgent
from ..utils.logger import get_logger


class WorkflowState(Enum):
    """Workflow execution states."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class BaseWorkflow(ABC):
    """Abstract base class for workflow execution patterns."""
    
    def __init__(
        self,
        name: str,
        description: str,
        agents: List[BaseAgent],
        max_steps: int = 20,
        timeout: int = 300
    ):
        """
        Initialize workflow.
        
        Args:
            name: Workflow name
            description: Workflow description
            agents: List of agents in workflow
            max_steps: Maximum execution steps
            timeout: Execution timeout in seconds
        """
        self.name = name
        self.description = description
        self.agents = agents
        self.max_steps = max_steps
        self.timeout = timeout
        self.logger = get_logger(f"workflow.{name}")
        
        # State management
        self._state = WorkflowState.IDLE
        self._current_step = 0
        self._execution_history: List[Dict[str, Any]] = []
        self._start_time: Optional[datetime] = None
        
        self.logger.info(f"📋 Initialized workflow: {name}")
    
    @property
    def state(self) -> WorkflowState:
        """Get current workflow state."""
        return self._state
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            task: Task to execute
            context: Optional context information
            
        Returns:
            Workflow execution result
        """
        pass
    
    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run workflow with error handling and state management.
        
        Args:
            task: Task to execute
            context: Optional context
            
        Returns:
            Execution result with status and output
        """
        try:
            # Set initial state
            self._set_state(WorkflowState.RUNNING)
            self._start_time = datetime.now()
            self._current_step = 0
            
            self.logger.info(f"▶️ Starting workflow execution: {task[:50]}...")
            
            # Execute workflow
            result = self.execute(task, context)
            
            # Record success
            self._record_execution(task, context, result, "completed")
            self._set_state(WorkflowState.COMPLETED)
            
            return {
                "status": "success",
                "result": result,
                "steps": self._current_step,
                "duration": self._get_duration()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {str(e)}")
            
            # Record failure
            self._record_execution(task, context, None, "failed", str(e))
            self._set_state(WorkflowState.FAILED)
            
            # Attempt rollback
            rollback_success = self._rollback()
            
            return {
                "status": "failed",
                "error": str(e),
                "steps": self._current_step,
                "duration": self._get_duration(),
                "rollback": rollback_success
            }
    
    def _set_state(self, state: WorkflowState) -> None:
        """Update workflow state."""
        self._state = state
        self.logger.debug(f"🔄 State changed to: {state.value}")
    
    def _record_execution(
        self,
        task: str,
        context: Optional[Dict[str, Any]],
        result: Any,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """Record execution in history."""
        self._execution_history.append({
            "task": task,
            "context": context,
            "result": result,
            "status": status,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "step": self._current_step
        })
    
    def _get_duration(self) -> float:
        """Get execution duration in seconds."""
        if self._start_time:
            return (datetime.now() - self._start_time).total_seconds()
        return 0.0
    
    def _rollback(self) -> bool:
        """
        Attempt to rollback workflow on failure.
        
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            self.logger.info("🔄 Attempting rollback...")
            
            # Default rollback: reset agent states
            for agent in self.agents:
                agent._set_state(agent.AgentState.IDLE)
            
            self._set_state(WorkflowState.ROLLED_BACK)
            self.logger.info("✅ Rollback completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Rollback failed: {str(e)}")
            return False
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        return self._execution_history.copy()
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()
        self._current_step = 0
        self.logger.debug("🧹 Cleared execution history")
    
    def __str__(self) -> str:
        return f"{self.name} ({self.state.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>" 