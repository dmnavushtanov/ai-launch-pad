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
from ..prompts.router_prompts import RouterPrompts
from ..utils.prompt_loader import PromptLoader
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
        self.prompt_loader = PromptLoader()
        
        # Load prompts
        self.prompts = self.prompt_loader.load_from_class(
            'backend.prompts.router_prompts',
            'RouterPrompts'
        )
    
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
            
            # Execute tasks sequentially
            results = []
            current_context = context or {}
            
            for i, subtask in enumerate(subtasks):
                self.logger.info(f"🔄 Processing subtask {i+1}/{len(subtasks)}: {subtask[:50]}...")
                
                # Select agent
                selected_agent = self.select_agent(subtask)
                if not selected_agent:
                    self.logger.warning(f"⚠️ No suitable agent for: {subtask}")
                    continue
                
                # Pass context between agents
                if i > 0 and results:
                    current_context = self.create_context_summary(
                        previous_agent=results[-1]['agent'],
                        previous_output=results[-1]['result'],
                        next_agent=selected_agent.name,
                        next_task=subtask
                    )
                
                # Execute with retry
                result = self.execute_with_retry(
                    agent=selected_agent,
                    task=subtask,
                    context=current_context
                )
                
                results.append({
                    'task': subtask,
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
        prompt = self.prompt_loader.format_prompt(
            self.prompts['TASK_DECOMPOSITION_PROMPT'],
            user_request=user_request,
            available_agents=", ".join(agent_descriptions)
        )
        
        # Get decomposition
        response = self.llm_client.generate_response(prompt)
        
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
        prompt = self.prompt_loader.format_prompt(
            self.prompts['AGENT_SELECTION_PROMPT'],
            task=task,
            agents_description=agent_descriptions
        )
        
        # Get selection
        response = self.llm_client.generate_response(prompt)
        
        # Parse agent name
        content = response.content
        agent_match = re.search(r'Agent:\s*(\w+)', content)
        
        if agent_match:
            agent_name = agent_match.group(1)
            return self.available_agents.get(agent_name)
        
        return None
    
    def create_context_summary(
        self,
        previous_agent: str,
        previous_output: str,
        next_agent: str,
        next_task: str
    ) -> Dict[str, Any]:
        """
        Create context summary for next agent.
        
        Args:
            previous_agent: Previous agent name
            previous_output: Previous agent's output
            next_agent: Next agent name
            next_task: Next task
            
        Returns:
            Context dictionary
        """
        # Format prompt
        prompt = self.prompt_loader.format_prompt(
            self.prompts['CONTEXT_SUMMARY_PROMPT'],
            previous_agent=previous_agent,
            previous_output=previous_output,
            next_agent=next_agent,
            next_task=next_task
        )
        
        # Get summary
        response = self.llm_client.generate_response(prompt)
        
        return {
            'summary': response.content,
            'previous_agent': previous_agent,
            'previous_output': previous_output
        }
    
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