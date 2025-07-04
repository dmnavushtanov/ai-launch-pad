# backend/agents/task_agent_1.py
# This file contains the CalculatorAgent that uses LangChain's ReAct pattern for mathematical calculations
# Purpose: Perform mathematical calculations with step-by-step reasoning and explanations. This IS for mathematical operations ONLY, NOT for general task execution.

import re
import math
from typing import Dict, Any, Optional, List
from langchain.tools import Tool, BaseTool
from langchain.memory import ConversationBufferWindowMemory

from .base_agent import BaseAgent
from ..llm_clients.base_llm_client import BaseClient
from ..utils.prompt_loader import prompt_loader


class CalculatorTool(BaseTool):
    """Tool for evaluating mathematical expressions."""
    
    name: str = "calculator"
    description: str = "Useful for evaluating mathematical expressions. Input should be a valid mathematical expression."
    
    def _run(self, expression: str) -> str:
        """Evaluate a mathematical expression."""
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Replace common mathematical terms
            expression = expression.replace('^', '**')
            expression = expression.replace('sqrt', 'math.sqrt')
            expression = expression.replace('sin', 'math.sin')
            expression = expression.replace('cos', 'math.cos')
            expression = expression.replace('tan', 'math.tan')
            expression = expression.replace('log', 'math.log')
            expression = expression.replace('pi', 'math.pi')
            expression = expression.replace('e', 'math.e')
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, {"math": math})
            
            return f"Result: {result}"
        except Exception as e:
            return f"Error evaluating expression '{expression}': {str(e)}"


class CalculatorAgent(BaseAgent):
    """Calculator agent using LangChain's ReAct pattern for step-by-step mathematical reasoning."""
    
    def __init__(self, llm_client: BaseClient):
        # Initialize calculator tool
        calculator_tool = CalculatorTool()
        
        super().__init__(
            name="CalculatorAgent",
            description="Mathematical calculator agent with step-by-step reasoning",
            llm_client=llm_client,
            tools=[calculator_tool]
        )
        
        # Initialize memory to track calculation history
        try:
            self.memory = ConversationBufferWindowMemory(
                memory_key="calculation_history",
                k=10,  # Keep last 10 calculations
                return_messages=False
            )
        except Exception as e:
            self.logger.warning(f"Failed to initialize memory: {str(e)}. Continuing without memory.")
            self.memory = None
        
        # Create LangChain agent
        try:
            self._create_calculator_agent()
        except Exception as e:
            self.logger.error(f"Failed to create LangChain agent: {str(e)}")
            self.logger.error(f"This might be due to missing LangChain dependencies.")
            self.logger.error(f"Please ensure you have installed: pip install langchain langchain-community")
            raise
    
    def _create_calculator_agent(self):
        """Create the LangChain agent executor."""
        # Get prompt template string from YAML
        prompt_template = prompt_loader.get_prompt('task_agent', 'CALCULATOR_AGENT_PROMPT')
        
        # The prompt template already has {tools}, {tool_names}, {input}, and {agent_scratchpad}
        # We should NOT format these - LangChain will handle them
        # Just pass the template string as-is
        self.create_langchain_agent(prompt_template)
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a mathematical calculation with step-by-step reasoning.
        
        Args:
            task: Mathematical problem to solve
            context: Optional context from previous steps
            
        Returns:
            Step-by-step solution with final answer
        """
        try:
            full_input = task
            if context and 'summary' in context:
                full_input = f"Context from previous steps:\n{context['summary']}\n\nYour task is: {task}"
                self.logger.info("Using context for task execution.")
            
            self.logger.info(f"Calculating: {full_input}")
            
            # Run the calculation using the agent
            result = self.run_with_tools(full_input)
            
            # Store in memory
            self.memory.save_context(
                {"input": full_input},
                {"output": result}
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error during calculation: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def validate_input(self, task: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate that the input is a mathematical question.
        
        Args:
            task: Task to validate
            context: Optional context
            
        Returns:
            True if valid mathematical input
        """
        if not task or not isinstance(task, str):
            self.logger.error("Invalid input: must be non-empty string")
            return False
        
        # Check for mathematical keywords or numbers
        math_patterns = [
            r'\d+',  # Contains numbers
            r'calculate|compute|solve|what is|find',  # Math verbs
            r'plus|minus|times|divided|add|subtract|multiply|divide',  # Operations
            r'percent|percentage|square root|power|squared',  # Math terms
            r'[\+\-\*\/\^\%]'  # Math symbols
        ]
        
        task_lower = task.lower()
        has_math_content = any(re.search(pattern, task_lower) for pattern in math_patterns)
        
        if not has_math_content:
            self.logger.warning(f"Input doesn't appear to be mathematical: {task}")
        
        return True
    
    def format_output(self, raw_output: Any) -> str:
        """
        Format the calculation output for clear presentation.
        
        Args:
            raw_output: Raw calculation output
            
        Returns:
            Formatted output with clear structure
        """
        output = str(raw_output)
        
        # Extract final answer if present
        final_answer_match = re.search(r'Final Answer:\s*(.+?)(?:\n|$)', output, re.IGNORECASE | re.DOTALL)
        
        if final_answer_match:
            # Format with emphasis on final answer
            return f"**Calculation Result**\n\n{output}\n\n**Summary**: {final_answer_match.group(1).strip()}"
        else:
            # Return as-is if no clear final answer
            return f"**Calculation Result**\n\n{output}"
    
    def get_calculation_history(self) -> List[Dict[str, str]]:
        """
        Get the history of calculations.
        
        Returns:
            List of calculation history entries
        """
        history = []
        if hasattr(self.memory, 'buffer'):
            # Parse the buffer to extract calculations
            buffer_content = self.memory.buffer
            if buffer_content:
                # Simple parsing - can be enhanced
                lines = buffer_content.split('\n')
                current_calc = {}
                for line in lines:
                    if line.startswith('Human:'):
                        current_calc['input'] = line.replace('Human:', '').strip()
                    elif line.startswith('AI:'):
                        current_calc['output'] = line.replace('AI:', '').strip()
                        if current_calc.get('input'):
                            history.append(current_calc.copy())
                            current_calc = {}
        
        return history
    
    def clear_calculation_history(self):
        """Clear the calculation history."""
        self.memory.clear()
        self.logger.info("Cleared calculation history") 