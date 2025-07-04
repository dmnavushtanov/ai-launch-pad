# backend/agents/task_agent_2.py
# This file contains TaskAgent2, a specialized agent template with tool integration
# Purpose: Demonstrate customized agent behavior, tool usage, and specialized prompt templates

from typing import Dict, Any, Optional, List
from langchain.tools import BaseTool

from .base_agent import BaseAgent
from ..llm_clients.base_llm_client import BaseClient
from ..utils.context_manager import ContextManager
from ..utils.prompt_loader import prompt_loader


class TaskAgent2(BaseAgent):
    """Specialized agent with custom behavior and tool integration."""
    
    def __init__(
        self,
        llm_client: BaseClient,
        domain: str = "data_analysis",
        tools: Optional[List[BaseTool]] = None,
        context_manager: Optional[ContextManager] = None
    ):
        super().__init__(
            name="TaskAgent2",
            description=f"Specialized {domain} agent with tool capabilities",
            llm_client=llm_client,
            tools=tools,
            context_manager=context_manager
        )
        self.domain = domain
        
        # Initialize agent executor if tools are provided
        if self.tools:
            try:
                self._setup_tool_agent()
            except Exception as e:
                self.logger.warning(f"Failed to setup tool agent: {str(e)}")
                self.logger.warning(f"Continuing without tool integration")
                self.tools = []  # Clear tools to prevent issues later
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute specialized task with optional tool usage.
        
        Args:
            task: Task description
            context: Context from previous agents
            
        Returns:
            Task execution result
        """
        # Determine if tools should be used
        if self.tools and self._should_use_tools(task):
            return self._execute_with_tools(task, context)
        else:
            return self._execute_without_tools(task, context)
    
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate task input with domain-specific checks.
        
        Args:
            task: Task to validate
            context: Optional context
            
        Returns:
            True if valid
        """
        # Basic validation - check if task is not empty
        if not task or not task.strip():
            self.logger.error("Empty task provided")
            return False
        
        # Domain-specific validation (just log warning, don't reject)
        if self.domain == "data_analysis" and "analyze" not in task.lower():
            self.logger.warning(f"Task may not be suitable for {self.domain} domain")
        
        # Context validation
        if context and "previous_agent" in context:
            if context["previous_agent"] == "incompatible_agent":
                self.logger.error("Incompatible previous agent")
                return False
        
        return True
    
    def format_output(self, raw_output: Any) -> str:
        """
        Format output with domain-specific structure.
        
        Args:
            raw_output: Raw output
            
        Returns:
            Formatted output
        """
        output = str(raw_output)
        
        # Domain-specific formatting
        if self.domain == "data_analysis":
            formatted = {
                "agent": self.name,
                "domain": self.domain,
                "analysis": {
                    "summary": self._extract_summary(output),
                    "details": output.strip(),
                    "recommendations": self._extract_recommendations(output)
                },
                "metadata": {
                    "tools_used": [tool.name for tool in self.tools] if self.tools else [],
                    "status": "completed"
                }
            }
        else:
            # Generic formatting for other domains
            formatted = {
                "agent": self.name,
                "domain": self.domain,
                "output": output.strip(),
                "status": "completed"
            }
        
        # Convert to structured string
        return self._dict_to_formatted_string(formatted)
    
    def _setup_tool_agent(self):
        """Setup LangChain agent with tools."""
        # Create prompt template with required placeholders for LangChain
        # Do NOT format {tools}, {tool_names}, {input}, or {agent_scratchpad}
        # LangChain will handle these placeholders
        prompt_template = f"""You are a specialized {self.domain} agent with access to tools.

Available tools:
{{tools}}

Tool Names: {{tool_names}}

Task: {{input}}

Use the available tools when needed to complete the task.
Follow this format:

Thought: Consider what needs to be done
Action: tool_name
Action Input: input for the tool
Observation: tool result
... (repeat as needed)
Thought: Final analysis
Final Answer: Complete response

{{agent_scratchpad}}"""
        
        self.create_langchain_agent(prompt_template)
    
    def _should_use_tools(self, task: str) -> bool:
        """Determine if tools should be used for the task."""
        tool_keywords = ["calculate", "search", "query", "fetch", "analyze with"]
        return any(keyword in task.lower() for keyword in tool_keywords)
    
    def _execute_with_tools(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute task using tools."""
        self.logger.info(f"Executing with tools: {[t.name for t in self.tools]}")
        
        # Prepare task with context
        if context:
            context_str = self._format_context(context)
            enhanced_task = f"{task}\n\nContext:\n{context_str}"
        else:
            enhanced_task = task
        
        # Run with tools
        return self.run_with_tools(enhanced_task)
    
    def _execute_without_tools(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute task without tools using specialized prompt."""
        # Build context string
        context_str = ""
        if context:
            context_str = self._format_context(context)
        
        # Use specialized prompt
        prompt_template = prompt_loader.get_prompt('task_agent', 'DATA_ANALYSIS_PROMPT')
        prompt = prompt_template.format(
            task=task,
            data_context=context_str or "No previous context",
            tools="None available"
        )
        
        self.logger.info(f"Executing {self.domain} task without tools")
        return self.llm_client.generate_response(prompt)
    
    def _get_domain_requirements(self) -> str:
        """Get domain-specific requirements."""
        requirements = {
            "data_analysis": "Provide statistical insights, identify patterns, and suggest actionable recommendations",
            "code_review": "Check for bugs, suggest improvements, and ensure best practices",
            "research": "Provide comprehensive analysis with sources and evidence",
            "planning": "Create structured plans with timelines and dependencies"
        }
        return requirements.get(self.domain, "Complete the task according to domain best practices")
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt inclusion."""
        parts = []
        for key, value in context.items():
            if isinstance(value, dict):
                parts.append(f"{key}: {self._dict_to_formatted_string(value)}")
            else:
                parts.append(f"{key}: {value}")
        return "\n".join(parts)
    
    def _dict_to_formatted_string(self, data: Dict[str, Any], indent: int = 0) -> str:
        """Convert dictionary to formatted string."""
        lines = []
        indent_str = "  " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}{key}:")
                lines.append(self._dict_to_formatted_string(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}{key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{indent_str}{key}: {value}")
        
        return "\n".join(lines)
    
    def _extract_summary(self, output: str) -> str:
        """Extract summary from output."""
        # Simple extraction - take first sentence or line
        lines = output.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            if len(first_line) > 10:
                return first_line
        return "Analysis completed"
    
    def _extract_recommendations(self, output: str) -> List[str]:
        """Extract recommendations from output."""
        recommendations = []
        lines = output.lower().split("\n")
        
        for i, line in enumerate(lines):
            if "recommend" in line or "suggest" in line:
                # Take this line and possibly the next
                recommendations.append(lines[i].strip())
                if i + 1 < len(lines):
                    recommendations.append(lines[i + 1].strip())
        
        return recommendations[:3]  # Limit to 3 recommendations 