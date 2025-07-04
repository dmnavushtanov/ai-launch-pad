# backend/agents/router_agent.py
# This file contains the RouterAgent for task decomposition and orchestration between multiple agents
# Purpose: Decompose complex tasks into subtasks, select appropriate agents for each subtask, and aggregate results. This is NOT for individual task execution or agent creation.

"""
Router agent for task decomposition and orchestration.
"""
from typing import Dict, Any, List, Optional
import json
import re

from .base_agent import BaseAgent, AgentState
from ..llm_clients.base_llm_client import BaseClient
from ..utils.prompt_loader import prompt_loader
from ..utils.context_manager import ContextManager


class RouterAgent(BaseAgent):
    """Router agent that decomposes tasks and orchestrates other agents."""
    
    def __init__(
        self,
        llm_client: BaseClient,
        available_agents: Dict[str, BaseAgent],
        context_manager: Optional[ContextManager] = None,
        max_retries: int = 3
    ):
        super().__init__(
            name="RouterAgent",
            description="Decomposes tasks and routes them to appropriate agents",
            llm_client=llm_client,
            tools=[],  # Router doesn't use tools directly
            context_manager=context_manager
        )
        
        self.available_agents = available_agents
        self.max_retries = max_retries
        
        # Validate available agents
        if not self.available_agents:
            self.logger.warning("⚠️ RouterAgent initialized with no available agents!")
            self.logger.warning("   This means the router cannot delegate any tasks.")
        else:
            self.logger.info(f"✅ RouterAgent initialized with {len(self.available_agents)} available agents:")
            for name, agent in self.available_agents.items():
                self.logger.info(f"   - {name}: {agent.description}")
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute router workflow: decompose, select agents, execute, aggregate.
        
        Args:
            task: User task/request
            context: Optional initial context
            
        Returns:
            Aggregated results
        """
        try:
            # Decompose task
            subtasks = self.decompose_task(task)
            self.logger.info(f"📋 Decomposed into {len(subtasks)} subtasks")
            
            # Log the actual subtasks for debugging
            for i, subtask in enumerate(subtasks, 1):
                self.logger.debug(f"   Subtask {i}: {subtask}")
            
            # Execute tasks sequentially
            results = []
            current_context = context or {}
            
            for i, subtask in enumerate(subtasks):
                self.logger.info(f"🔄 Processing subtask {i+1}/{len(subtasks)}: {subtask[:50]}...")

                # Substitute placeholders before selecting agent
                current_task = self._substitute_placeholders(subtask, results)
                
                # Select agent
                selected_agent = self.select_agent(current_task)
                
                # If no agent is selected, it means the workflow is complete.
                if not selected_agent:
                    self.logger.info(f"✅ No suitable agent found for task, assuming workflow is complete.")
                    break
                
                self.logger.debug(f"   Selected agent: {selected_agent.name} for subtask: {current_task[:50]}...")
                
                # Pass context between agents
                if i > 0 and results:
                    previous_steps_summary = "\n".join(
                        [f"- Step {j+1} (executed by {res['agent']}):\n  Task: {res['task']}\n  Result: {res['result']}" for j, res in enumerate(results)]
                    )
                    current_context['summary'] = (
                        "You are part of a multi-step workflow. Here is a summary of the previous steps:\n"
                        f"{previous_steps_summary}"
                    )
                    self.logger.info("Created context summary for the next agent.")
                else:
                    # For the first step, context might be passed from outside, but we should clear summary if it exists from a previous run.
                    current_context.pop('summary', None)
                
                # Execute with retry
                result = self.execute_with_retry(
                    agent=selected_agent,
                    task=current_task,
                    context=current_context
                )
                
                results.append({
                    'task': current_task,
                    'agent': selected_agent.name,
                    'result': result
                })
            
            # Aggregate results
            return self.aggregate_results(results)
            
        except Exception as e:
            self.logger.error(f"Router execution failed: {str(e)}")
            raise
    
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate router input."""
        if not task or not task.strip():
            self.logger.error("Empty task provided")
            return False
        
        if not self.available_agents:
            self.logger.error("No agents available")
            return False
        
        return True
    
    def format_output(self, raw_output: Any) -> str:
        """Format router output."""
        if isinstance(raw_output, list):
            # Format list of results
            formatted = "Task Execution Results:\n\n"
            for i, item in enumerate(raw_output):
                formatted += f"{i+1}. {item.get('task', 'Unknown task')}\n"
                formatted += f"   Agent: {item.get('agent', 'Unknown')}\n"
                formatted += f"   Result: {item.get('result', 'No result')}\n\n"
            return formatted
        
        return str(raw_output)
    
    def _substitute_placeholders(self, task: str, results: List[Dict[str, Any]]) -> str:
        """Substitutes placeholders like {step_1_output} with actual results."""
        placeholders = re.findall(r'\{step_(\d+)_output\}', task)
        if not placeholders:
            return task

        for step_num_str in placeholders:
            step_num = int(step_num_str)
            if 1 <= step_num <= len(results):
                previous_result = results[step_num - 1]['result']
                placeholder_str = f"{{step_{step_num}_output}}"
                task = task.replace(placeholder_str, str(previous_result))
                self.logger.debug(f"Replaced {placeholder_str} with result from step {step_num}")
            else:
                self.logger.warning(f"Invalid step number {step_num} in placeholder for task: {task}")
        return task

    def decompose_task(self, user_request: str) -> List[str]:
        """
        Decompose user request into subtasks.
        
        Args:
            user_request: Original user request
            
        Returns:
            List of subtasks
        """
        # Prepare agent descriptions
        agent_descriptions = [
            f"{name}: {agent.description}"
            for name, agent in self.available_agents.items()
        ]
        
        # Format prompt
        prompt_template = prompt_loader.get_prompt('router', 'TASK_DECOMPOSITION_PROMPT')
        prompt = prompt_template.format(
            user_request=user_request,
            available_agents=", ".join(agent_descriptions)
        )
        
        # Get decomposition
        response = self.llm_client.generate_response(prompt)
        
        # Log the raw response for debugging
        self.logger.debug(f"Task decomposition raw response:\n{response.content}")
        
        # Parse numbered list
        tasks = []
        lines = response.content.split('\n')
        for line in lines:
            # Match numbered items (1. task, 2. task, etc.)
            match = re.match(r'^\d+\.\s+(.+)$', line.strip())
            if match:
                tasks.append(match.group(1))
        
        return tasks
    
    def select_agent(self, task: str) -> Optional[BaseAgent]:
        """
        Select appropriate agent for a task.
        
        Args:
            task: Task to assign
            
        Returns:
            Selected agent or None
        """
        # Prepare agent descriptions
        agent_descriptions = "\n".join([
            f"- {name}: {agent.description}"
            for name, agent in self.available_agents.items()
        ])
        
        # Format prompt
        prompt_template = prompt_loader.get_prompt('router', 'AGENT_SELECTION_PROMPT')
        prompt = prompt_template.format(
            task=task,
            agents_description=agent_descriptions
        )
        
        # Get selection
        response = self.llm_client.generate_response(prompt)
        
        # Log the raw response for debugging
        self.logger.debug(f"Agent selection raw response for task '{task[:50]}...':\n{response.content}")
        
        # Simple approach: check which agent name appears in the response
        content = response.content.lower()

        # Handle the case where no agent is needed
        if 'agent: none' in content:
            self.logger.debug("Agent selection returned 'None'. No further action needed.")
            return None
        
        for agent_name, agent in self.available_agents.items():
            if agent_name.lower() in content:
                self.logger.debug(f"Found agent name '{agent_name}' in response")
                return agent
        
        self.logger.warning(f"No agent name found in response: {response.content}")
        return None
    
    def execute_with_retry(
        self,
        agent: BaseAgent,
        task: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Execute task with retry logic.
        
        Args:
            agent: Agent to execute
            task: Task to execute
            context: Execution context
            
        Returns:
            Execution result
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Use agent's error handling
                result = agent._execute_with_error_handling(task, context)
                
                # Check if it's an error
                if not result.startswith("Error:"):
                    return result
                
                last_error = result
                self.logger.warning(f"Attempt {attempt + 1} failed: {result}")
                
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1} exception: {str(e)}")
            
            if attempt < self.max_retries - 1:
                self.logger.info(f"🔄 Retrying... ({attempt + 2}/{self.max_retries})")
        
        return f"Failed after {self.max_retries} attempts. Last error: {last_error}"
    
    def aggregate_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Aggregate results from multiple agents.
        
        Args:
            results: List of agent results
            
        Returns:
            Aggregated summary
        """
        if not results:
            return "No results to aggregate"
        
        # Simple aggregation - join all results
        aggregated = "## Task Execution Summary\n\n"
        
        for i, result in enumerate(results, 1):
            aggregated += f"### Step {i}: {result['task']}\n"
            aggregated += f"**Agent**: {result['agent']}\n"
            aggregated += f"**Result**: {result['result']}\n\n"
        
        aggregated += f"**Total Steps Completed**: {len(results)}"
        
        return aggregated 