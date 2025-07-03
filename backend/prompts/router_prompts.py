# backend/prompts/router_prompts.py
# This file contains router agent prompts for task decomposition, agent selection, and context summarization
# Purpose: Provide prompt templates for the router agent to decompose complex tasks, select appropriate agents, and manage context flow between agents. This is NOT for task execution or general utility prompts.

"""
Router agent prompts for task decomposition and agent selection.
"""


class RouterPrompts:
    """Prompts for router agent operations."""
    
    TASK_DECOMPOSITION_PROMPT = """You are a task decomposition expert. Break down the user's request into smaller, manageable tasks.

User Request: {user_request}
Available Agents: {available_agents}

Analyze the request and decompose it into tasks. Each task should be:
- Clear and specific
- Assignable to one agent
- Independent or properly sequenced

Example:
User Request: "Analyze sales data and create a report with visualizations"
Tasks:
1. Load and validate sales data
2. Perform statistical analysis 
3. Create data visualizations
4. Generate report document

Output your tasks as a numbered list."""

    AGENT_SELECTION_PROMPT = """Select the most appropriate agent for the given task.

Task: {task}
Available Agents:
{agents_description}

Consider:
- Agent capabilities
- Task requirements
- Agent current load (if available)

Example:
Task: "Analyze customer sentiment from reviews"
Agents: [DataAgent: handles data processing, NLPAgent: handles text analysis]
Selected: NLPAgent
Reason: Task requires natural language processing capabilities

Output:
Agent: [agent_name]
Reason: [brief explanation]"""

    CONTEXT_SUMMARY_PROMPT = """Summarize the relevant context for the next agent.

Previous Agent: {previous_agent}
Previous Output: {previous_output}
Next Agent: {next_agent}
Next Task: {next_task}

Create a concise summary that includes:
- Key results from previous agent
- Relevant data or insights
- Any constraints or requirements

Example:
Previous Agent: DataAgent
Previous Output: "Loaded 10,000 customer records, 15% missing emails"
Next Agent: ValidationAgent
Next Task: "Clean and validate customer data"
Summary: "Customer dataset has 10,000 records with 15% missing email addresses. Needs cleaning and validation before analysis."

Summary:"""

    REACT_PROMPT = """Use the ReAct pattern to solve this task step by step.

Task: {task}
Context: {context}
Available Tools: {available_tools}

Follow this pattern:
Thought: Analyze what needs to be done
Action: Choose an action/tool
Observation: Note the result
... (repeat as needed)
Final Answer: Provide the solution

Example:
Task: Find the total revenue for Q4 2023
Thought: I need to query sales data for Q4 2023
Action: query_database("SELECT SUM(revenue) FROM sales WHERE quarter='Q4' AND year=2023")
Observation: Query returned 1,250,000
Thought: I have the total revenue
Final Answer: The total revenue for Q4 2023 is $1,250,000

Begin:""" 