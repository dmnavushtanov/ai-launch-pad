# AGENTS.md
# This file contains the guide for creating and implementing custom agents
# Purpose: Document agent interface, provide best practices, and show implementation examples

# 🤖 Agent Development Guide

This guide explains how to create custom agents for the AI Agentic Workflow Launchpad.

## 📚 Table of Contents

1. [Agent Interface](#agent-interface)
2. [Creating a New Agent](#creating-a-new-agent)
3. [Best Practices](#best-practices)
4. [Examples](#examples)
5. [Testing Your Agent](#testing-your-agent)

## 🔧 Agent Interface

All agents must inherit from `BaseAgent` and implement required methods.

### BaseAgent Class

```python
from backend.agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    """Your agent description."""
    
    def __init__(self, llm_client):
        super().__init__(
            name="my_custom_agent",
            llm_client=llm_client,
            description="What this agent does"
        )
    
    def _process_task(self, task: str, context: Dict[str, Any]) -> str:
        """Process the task and return result."""
        # Your implementation here
        pass
```

### Required Methods

#### `_process_task(task: str, context: Dict[str, Any]) -> str`

- **Purpose**: Core task processing logic
- **Parameters**:
  - `task`: The input task/question
  - `context`: Shared context from previous agents
- **Returns**: String result
- **Note**: Called automatically by base class

### Optional Methods

#### `_validate_task(task: str) -> bool`

- Validate if agent can handle the task
- Default returns `True`

#### `_prepare_context(context: Dict[str, Any]) -> Dict[str, Any]`

- Modify context before processing
- Default returns context unchanged

## 🚀 Creating a New Agent

### Step 1: Create Agent File

Create `backend/agents/my_agent.py`:

```python
# backend/agents/my_agent.py
# This file implements a custom agent for specific task handling
# Purpose: Process tasks related to [your domain] and provide structured responses

from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from .base_agent import BaseAgent
from ..utils.logger import get_logger


class MyAgent(BaseAgent):
    """Agent for handling [specific domain] tasks."""
    
    def __init__(self, llm_client):
        """Initialize with specific configuration."""
        super().__init__(
            name="my_agent",
            llm_client=llm_client,
            description="Handles [specific] tasks"
        )
        self.logger = get_logger(f"agent.{self.name}")
        
        # Define system prompt
        self.system_prompt = """
        You are a specialized agent for [domain].
        Your role is to [specific responsibilities].
        Always [specific guidelines].
        """
    
    def _process_task(self, task: str, context: Dict[str, Any]) -> str:
        """Process the task using LLM."""
        try:
            # Prepare messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=task)
            ]
            
            # Add context if relevant
            if context.get("previous_analysis"):
                messages.append(
                    SystemMessage(
                        content=f"Previous context: {context['previous_analysis']}"
                    )
                )
            
            # Call LLM
            response = self.llm_client.generate(messages)
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"Task processing failed: {str(e)}")
            raise
```

### Step 2: Register Agent

Add to `main.py` in `_register_agents()`:

```python
from backend.agents.my_agent import MyAgent

# In _register_agents method:
self.agent_registry.register(
    name="my_agent",
    agent_class=MyAgent,
    version="1.0.0",
    capabilities=["domain_specific", "analysis"],
    description="Handles domain-specific tasks"
)
```

### Step 3: Configure Agent

Add to `config.yml`:

```yaml
agents:
  my_agent:
    name: "My Custom Agent"
    description: "Specialized agent for domain tasks"
    llm_provider: "openai"
    system_prompt: "You are a specialized agent..."
    temperature: 0.7
    max_iterations: 10
    tools: ["domain_tool_1", "domain_tool_2"]
```

### Step 4: Add to Workflow

Update workflow configuration:

```yaml
workflows:
  my_workflow:
    name: "Custom Workflow"
    type: "sequential"
    agents: ["router", "my_agent", "task_agent_2"]
    max_steps: 20
```

## 📋 Best Practices

### 1. Single Responsibility

Each agent should have ONE clear purpose:

```python
# ✅ Good
class DataAnalysisAgent(BaseAgent):
    """Analyzes data and provides insights."""

# ❌ Bad
class DoEverythingAgent(BaseAgent):
    """Analyzes data, writes code, sends emails..."""
```

### 2. Clear Prompts

Use specific, focused system prompts:

```python
# ✅ Good
self.system_prompt = """
You are a data analysis agent.
Analyze the provided data and identify:
1. Key patterns
2. Anomalies
3. Trends
Provide clear, concise insights.
"""

# ❌ Bad
self.system_prompt = "You are an AI assistant."
```

### 3. Context Handling

Pass relevant information to next agents:

```python
def _process_task(self, task: str, context: Dict[str, Any]) -> str:
    result = self._analyze_data(task)
    
    # Add to context for next agents
    context["data_insights"] = {
        "patterns": result.patterns,
        "anomalies": result.anomalies
    }
    
    return result.summary
```

### 4. Error Handling

Always handle errors gracefully:

```python
def _process_task(self, task: str, context: Dict[str, Any]) -> str:
    try:
        return self._perform_analysis(task)
    except ValueError as e:
        self.logger.warning(f"Invalid input: {e}")
        return f"Unable to process: {str(e)}"
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}")
        raise
```

### 5. Logging

Use structured logging:

```python
self.logger.info(f"Starting analysis for task: {task[:50]}...")
self.logger.debug(f"Context keys: {list(context.keys())}")
self.logger.info(f"Analysis complete. Found {len(results)} insights")
```

## 💡 Examples

### Example 1: Research Agent

```python
class ResearchAgent(BaseAgent):
    """Agent for conducting research on topics."""
    
    def __init__(self, llm_client):
        super().__init__(
            name="research_agent",
            llm_client=llm_client,
            description="Conducts thorough research"
        )
        
        self.system_prompt = """
        You are a research specialist.
        For any topic, provide:
        1. Overview
        2. Key facts
        3. Recent developments
        4. Reliable sources
        Be accurate and cite sources when possible.
        """
    
    def _process_task(self, task: str, context: Dict[str, Any]) -> str:
        # Check if it's a research request
        if not self._is_research_task(task):
            return "This doesn't appear to be a research task."
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Research this topic: {task}")
        ]
        
        response = self.llm_client.generate(messages)
        
        # Extract key findings for context
        context["research_findings"] = self._extract_key_points(response.content)
        
        return response.content
    
    def _is_research_task(self, task: str) -> bool:
        research_keywords = ["research", "find out", "investigate", "explore", "what is"]
        return any(keyword in task.lower() for keyword in research_keywords)
```

### Example 2: Code Generation Agent

```python
class CodeGenerationAgent(BaseAgent):
    """Agent for generating code solutions."""
    
    def __init__(self, llm_client):
        super().__init__(
            name="code_gen_agent",
            llm_client=llm_client,
            description="Generates code solutions"
        )
        
        self.system_prompt = """
        You are an expert programmer.
        Generate clean, efficient code with:
        1. Clear comments
        2. Error handling
        3. Best practices
        4. Example usage
        """
    
    def _process_task(self, task: str, context: Dict[str, Any]) -> str:
        # Check previous context for requirements
        requirements = context.get("requirements", "")
        
        prompt = f"""
        Task: {task}
        Additional Requirements: {requirements}
        
        Generate a complete, working solution.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm_client.generate(messages)
        
        # Store code in context
        context["generated_code"] = self._extract_code_blocks(response.content)
        
        return response.content
```

## 🧪 Testing Your Agent

### Unit Test Example

```python
import pytest
from unittest.mock import Mock
from backend.agents.my_agent import MyAgent

def test_my_agent_process_task():
    # Mock LLM client
    mock_llm = Mock()
    mock_llm.generate.return_value.content = "Test response"
    
    # Create agent
    agent = MyAgent(mock_llm)
    
    # Test task processing
    result = agent._process_task("Test task", {})
    
    assert result == "Test response"
    assert mock_llm.generate.called
```

### Integration Test

```python
def test_agent_in_workflow():
    # Create real components
    llm_client = create_test_llm_client()
    agent = MyAgent(llm_client)
    
    # Test with workflow
    workflow = SequentialWorkflow(
        name="test_workflow",
        agents=[agent],
        max_steps=5
    )
    
    result = workflow.execute("Test task")
    assert result["final_output"] is not None
```

## 🔍 Debugging Tips

1. **Enable Debug Logging**:
   ```env
   DEBUG=true
   LOG_LEVEL=DEBUG
   ```

2. **Check Agent State**:
   ```python
   self.logger.debug(f"Current state: {self.get_state()}")
   ```

3. **Inspect Context**:
   ```python
   self.logger.debug(f"Context: {json.dumps(context, indent=2)}")
   ```

4. **Test in Isolation**:
   ```python
   # Test agent directly
   agent = MyAgent(llm_client)
   result = agent._execute_with_error_handling("test", {})
   ```

## 📝 Checklist for New Agents

- [ ] Inherit from `BaseAgent`
- [ ] Implement `_process_task` method
- [ ] Add clear system prompt
- [ ] Handle errors gracefully
- [ ] Add structured logging
- [ ] Update context for next agents
- [ ] Register in `main.py`
- [ ] Configure in `config.yml`
- [ ] Write unit tests
- [ ] Document capabilities

## 🚫 Common Pitfalls

1. **Too Broad Scope**: Keep agents focused
2. **Ignoring Context**: Use previous agent outputs
3. **No Error Handling**: Always catch exceptions
4. **Poor Prompts**: Be specific and clear
5. **Missing Logging**: Add helpful debug info

## 🎯 Summary

Creating effective agents requires:
- Clear, single purpose
- Well-defined prompts
- Proper error handling
- Context awareness
- Good logging

Follow these guidelines to build robust, reusable agents that work well in multi-agent workflows. 