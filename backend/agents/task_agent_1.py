# backend/agents/task_agent_1.py
# This file contains TaskAgent1, a general-purpose agent template
# Purpose: Serve as a basic task execution agent that can receive context from previous agents and format output for next agent consumption

from typing import Dict, Any, Optional

from .base_agent import BaseAgent
from ..llm_clients.base_llm_client import BaseClient
from ..prompts.task_agent_prompts import TaskAgentPrompts


class TaskAgent1(BaseAgent):
    """General-purpose task execution agent."""
    
    def __init__(self, llm_client: BaseClient):
        super().__init__(
            name="TaskAgent1",
            description="General-purpose agent for executing various tasks",
            llm_client=llm_client
        )
        self.prompts = TaskAgentPrompts()
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a general task with optional context.
        
        Args:
            task: Task description
            context: Context from previous agents
            
        Returns:
            Task execution result
        """
        # Extract context information
        previous_context = ""
        if context:
            previous_context = self._format_context(context)
        
        # Build prompt
        prompt = self.prompts.GENERAL_TASK_PROMPT.format(
            task=task,
            context=previous_context or "No previous context",
            requirements="Execute the task accurately and provide clear output"
        )
        
        # Execute with LLM
        self.logger.info(f"Executing task: {task[:50]}...")
        response = self.llm_client.generate(prompt)
        
        return response
    
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate task input.
        
        Args:
            task: Task to validate
            context: Optional context
            
        Returns:
            True if valid
        """
        # Basic validation
        if not task or not isinstance(task, str):
            self.logger.error("Invalid task: must be non-empty string")
            return False
        
        if len(task.strip()) < 3:
            self.logger.error("Task too short")
            return False
        
        return True
    
    def format_output(self, raw_output: Any) -> str:
        """
        Format output for next agent consumption.
        
        Args:
            raw_output: Raw LLM output
            
        Returns:
            Formatted output
        """
        # Ensure string output
        output = str(raw_output)
        
        # Create structured output
        formatted = {
            "agent": self.name,
            "output": output.strip(),
            "status": "completed"
        }
        
        # Convert to string format
        return f"Agent: {formatted['agent']}\nOutput: {formatted['output']}\nStatus: {formatted['status']}"
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable string."""
        formatted_parts = []
        
        for key, value in context.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                nested = "\n  ".join([f"{k}: {v}" for k, v in value.items()])
                formatted_parts.append(f"{key}:\n  {nested}")
            else:
                formatted_parts.append(f"{key}: {value}")
        
        return "\n".join(formatted_parts) 