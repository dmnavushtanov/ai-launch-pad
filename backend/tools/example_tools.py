# backend/tools/example_tools.py
# This file contains example tools demonstrating BaseTool usage
# Purpose: Show how to create tools for calculation, web search, and JIRA API integration with proper error handling

import json
import requests
from typing import Any, Type
from pydantic import BaseModel, Field

from .base_tool import BaseTool


class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    query: str = Field(..., description="Mathematical expression to evaluate (e.g., '2 + 2 * 3')")


class CalculatorTool(BaseTool):
    """Simple calculator tool for mathematical operations."""
    
    name: str = "calculator"
    description: str = "Perform mathematical calculations. Input should be a valid math expression."
    args_schema: Type[BaseModel] = CalculatorInput
    
    def _run(self, query: str) -> str:
        """
        Evaluate mathematical expression.
        
        Args:
            query: Math expression
            
        Returns:
            Calculation result
        """
        try:
            # Remove any dangerous operations
            if any(op in query for op in ["import", "__", "exec", "eval"]):
                return "Error: Invalid expression"
            
            # Only allow basic math operations
            allowed_chars = "0123456789+-*/()., "
            if not all(c in allowed_chars for c in query):
                return "Error: Only numbers and basic operators allowed"
            
            # Evaluate the expression
            result = eval(query)
            return f"Result: {result}"
            
        except Exception as e:
            return self.handle_error(e)
    
    def validate_input(self, query: str) -> bool:
        """Validate calculator input."""
        if not super().validate_input(query):
            return False
        
        # Check for balanced parentheses
        if query.count("(") != query.count(")"):
            return False
        
        return True


class WebSearchInput(BaseModel):
    """Input schema for web search tool."""
    query: str = Field(..., description="Search query")


class WebSearchTool(BaseTool):
    """Web search tool (simulated for example)."""
    
    name: str = "web_search"
    description: str = "Search the web for information. Returns simulated results."
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str) -> str:
        """
        Simulate web search.
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        try:
            # In real implementation, this would call a search API
            # For now, return simulated results
            results = {
                "query": query,
                "results": [
                    {
                        "title": f"Result 1 for '{query}'",
                        "url": "https://example.com/1",
                        "snippet": f"This is a relevant result about {query}..."
                    },
                    {
                        "title": f"Result 2 for '{query}'",
                        "url": "https://example.com/2",
                        "snippet": f"Another useful resource about {query}..."
                    }
                ],
                "total_results": 2
            }
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            return self.handle_error(e)


class JiraApiInput(BaseModel):
    """Input schema for JIRA API tool."""
    query: str = Field(..., description="JIRA API action (e.g., 'get issue PROJECT-123' or 'list issues in PROJECT')")


class JiraApiTool(BaseTool):
    """JIRA API integration tool."""
    
    name: str = "jira_api"
    description: str = "Interact with JIRA API. Supports getting issues and listing project issues."
    args_schema: Type[BaseModel] = JiraApiInput
    
    def __init__(self, base_url: str = "", api_token: str = "", email: str = ""):
        super().__init__()
        self.base_url = base_url
        self.api_token = api_token
        self.email = email
    
    def _run(self, query: str) -> str:
        """
        Execute JIRA API request.
        
        Args:
            query: JIRA command
            
        Returns:
            API response
        """
        try:
            # Parse the query
            parts = query.lower().split()
            
            if len(parts) < 2:
                return "Error: Invalid command. Use 'get issue KEY' or 'list issues in PROJECT'"
            
            action = parts[0]
            
            if action == "get" and parts[1] == "issue" and len(parts) > 2:
                issue_key = parts[2].upper()
                return self._get_issue(issue_key)
            
            elif action == "list" and "issues" in query and "in" in query:
                project_key = parts[-1].upper()
                return self._list_issues(project_key)
            
            else:
                return "Error: Unsupported command. Use 'get issue KEY' or 'list issues in PROJECT'"
                
        except Exception as e:
            return self.handle_error(e)
    
    def _get_issue(self, issue_key: str) -> str:
        """Get single JIRA issue."""
        if not self.base_url:
            # Return simulated response
            return json.dumps({
                "key": issue_key,
                "fields": {
                    "summary": f"Sample issue {issue_key}",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "John Doe"}
                }
            }, indent=2)
        
        # Real API call would go here
        url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
        # headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
        # response = requests.get(url, headers=headers)
        return f"Would fetch issue {issue_key} from {url}"
    
    def _list_issues(self, project_key: str) -> str:
        """List issues in project."""
        if not self.base_url:
            # Return simulated response
            return json.dumps({
                "project": project_key,
                "issues": [
                    {
                        "key": f"{project_key}-1",
                        "summary": "First issue",
                        "status": "Open"
                    },
                    {
                        "key": f"{project_key}-2",
                        "summary": "Second issue",
                        "status": "In Progress"
                    }
                ],
                "total": 2
            }, indent=2)
        
        # Real API call would go here
        jql = f"project={project_key}"
        url = f"{self.base_url}/rest/api/2/search?jql={jql}"
        return f"Would search issues with JQL: {jql}"
    
    def validate_input(self, query: str) -> bool:
        """Validate JIRA command."""
        if not super().validate_input(query):
            return False
        
        # Check for minimum command structure
        parts = query.split()
        if len(parts) < 2:
            return False
        
        return True 