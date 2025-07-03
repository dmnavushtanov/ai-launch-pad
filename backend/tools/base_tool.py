# backend/tools/base_tool.py
# This file contains the abstract BaseTool class for creating custom tools
# Purpose: Provide a standard interface for all tools with LangChain integration, error handling, validation, and metadata support

from abc import abstractmethod
from typing import Any, Optional, Type, Dict
from pydantic import BaseModel, Field
from langchain.tools import BaseTool as LangChainBaseTool

from ..utils.logger import get_logger


class ToolInputSchema(BaseModel):
    """Base schema for tool inputs."""
    query: str = Field(..., description="Input query or command")


class BaseTool(LangChainBaseTool):
    """Abstract base class for all tools with LangChain integration."""
    
    # Tool metadata
    name: str = "base_tool"
    description: str = "Base tool interface"
    args_schema: Type[BaseModel] = ToolInputSchema
    return_direct: bool = False
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(f"tool.{self.name}")
    
    @abstractmethod
    def _run(self, query: str, **kwargs) -> Any:
        """
        Execute the tool logic.
        
        Args:
            query: Input query
            **kwargs: Additional arguments
            
        Returns:
            Tool execution result
        """
        pass
    
    async def _arun(self, query: str, **kwargs) -> Any:
        """
        Async version of tool execution.
        
        Default implementation calls sync version.
        Override for true async behavior.
        """
        return self._run(query, **kwargs)
    
    def validate_input(self, query: str) -> bool:
        """
        Validate tool input.
        
        Args:
            query: Input to validate
            
        Returns:
            True if valid
        """
        if not query or not isinstance(query, str):
            return False
        return len(query.strip()) > 0
    
    def handle_error(self, error: Exception) -> str:
        """
        Handle tool execution errors.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Error message
        """
        self.logger.error(f"Tool error in {self.name}: {str(error)}")
        return f"Error: {str(error)}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata.
        
        Returns:
            Dictionary with tool information
        """
        return {
            "name": self.name,
            "description": self.description,
            "args_schema": self.args_schema.schema() if self.args_schema else None,
            "return_direct": self.return_direct
        }
    
    def run(self, query: str, **kwargs) -> Any:
        """
        Public method to run tool with error handling.
        
        Args:
            query: Input query
            **kwargs: Additional arguments
            
        Returns:
            Tool result or error message
        """
        try:
            # Validate input
            if not self.validate_input(query):
                raise ValueError("Invalid input")
            
            # Log execution
            self.logger.info(f"Running tool {self.name}: {query[:50]}...")
            
            # Execute tool
            result = self._run(query, **kwargs)
            
            # Log success
            self.logger.info(f"Tool {self.name} completed successfully")
            
            return result
            
        except Exception as e:
            return self.handle_error(e) 