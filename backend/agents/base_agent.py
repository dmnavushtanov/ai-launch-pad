# backend/agents/base_agent.py
# This file contains the abstract base agent class with LangChain integration and state management
# Purpose: Provide the foundational agent interface with execution, validation, and error handling capabilities. This is NOT for specific agent implementations or workflow orchestration.

"""
Abstract base agent with LangChain integration.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain_core.prompts import PromptTemplate

from ..llm_clients.base_llm_client import BaseClient
from ..utils.logger import get_logger
from ..utils.context_manager import ContextManager


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(
        self,
        name: str,
        description: str,
        llm_client: BaseClient,
        tools: Optional[List[BaseTool]] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.name = name
        self.description = description
        self.llm_client = llm_client
        self.tools = tools or []
        self.context_manager = context_manager or ContextManager()
        self.logger = get_logger(f"agent.{name}")
        
        # State management
        self._state = AgentState.IDLE
        self._execution_history: List[Dict[str, Any]] = []
        
        # LangChain agent executor
        self._agent_executor: Optional[AgentExecutor] = None
        
        self.logger.info(f"🤖 Initialized agent: {name}")
    
    @property
    def state(self) -> AgentState:
        """Get current agent state."""
        return self._state
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a task.
        
        Args:
            task: Task to execute
            context: Optional context information
            
        Returns:
            Execution result
        """
        pass
    
    @abstractmethod
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate input before execution.
        
        Args:
            task: Task to validate
            context: Optional context
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def format_output(self, raw_output: Any) -> str:
        """
        Format raw output for presentation.
        
        Args:
            raw_output: Raw execution output
            
        Returns:
            Formatted output string
        """
        pass
    
    def _set_state(self, state: AgentState) -> None:
        """Update agent state."""
        self._state = state
        self.logger.debug(f"🔄 State changed to: {state.value}")
    
    def _execute_with_error_handling(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute task with error handling and logging.
        
        Args:
            task: Task to execute
            context: Optional context
            
        Returns:
            Execution result or error message
        """
        try:
            # Set running state
            self._set_state(AgentState.RUNNING)
            
            # Validate input
            if not self.validate_input(task, context):
                raise ValueError("Invalid input")
            
            # Log execution start
            self.logger.info(f"▶️ Starting task: {task[:50]}...")
            
            # Execute task
            result = self.execute(task, context)
            
            # Format output
            formatted_result = self.format_output(result)
            
            # Store in context
            self.context_manager.store_context(
                context_type="agent",
                human_input=task,
                ai_output=formatted_result
            )
            
            # Record execution
            self._execution_history.append({
                "task": task,
                "context": context,
                "result": formatted_result,
                "state": "completed"
            })
            
            # Set completed state
            self._set_state(AgentState.COMPLETED)
            self.logger.info(f"✅ Task completed successfully")
            
            return formatted_result
            
        except Exception as e:
            # Log error
            import traceback
            self.logger.error(f"❌ Task failed: {str(e)}\n{traceback.format_exc()}")
            
            # Record failure
            self._execution_history.append({
                "task": task,
                "context": context,
                "error": str(e),
                "state": "failed"
            })
            
            # Set failed state
            self._set_state(AgentState.FAILED)
            
            # Re-raise the exception to be handled by the workflow
            raise
    
    def create_langchain_agent(self, prompt_template: str) -> AgentExecutor:
        """
        Create a LangChain agent executor.
        
        Args:
            prompt_template: ReAct prompt template
            
        Returns:
            AgentExecutor instance
        """
        if not self.tools:
            raise ValueError("No tools available for agent")
        
        try:
            # Create prompt
            prompt = PromptTemplate.from_template(prompt_template)
        except Exception as e:
            self.logger.error(f"Failed to create prompt template: {str(e)}")
            raise ValueError(f"Invalid prompt template: {str(e)}")
        
        try:
            # Create ReAct agent
            agent = create_react_agent(
                llm=self.llm_client.client,
                tools=self.tools,
                prompt=prompt
            )
        except AttributeError as e:
            self.logger.error(f"LLM client doesn't have required 'client' attribute: {str(e)}")
            self.logger.error(f"LLM client type: {type(self.llm_client)}")
            raise ValueError(f"Invalid LLM client configuration: {str(e)}")
        except Exception as e:
            self.logger.error(f"Failed to create ReAct agent: {str(e)}")
            raise
        
        try:
            # Create executor
            self._agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True
            )
        except Exception as e:
            self.logger.error(f"Failed to create agent executor: {str(e)}")
            raise
        
        return self._agent_executor
    
    def run_with_tools(self, task: str) -> str:
        """
        Run task using LangChain agent with tools.
        
        Args:
            task: Task to execute
            
        Returns:
            Agent response
        """
        if not self._agent_executor:
            raise ValueError("Agent executor not initialized")
        
        try:
            # Use invoke instead of run (run is deprecated)
            result = self._agent_executor.invoke({"input": task})
            # Extract the output from the result dictionary
            if isinstance(result, dict) and "output" in result:
                return result["output"]
            else:
                return str(result)
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            raise
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get agent execution history."""
        return self._execution_history.copy()
    
    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()
        self.logger.debug("🧹 Cleared execution history")
    
    def __str__(self) -> str:
        return f"{self.name} ({self.state.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>" 