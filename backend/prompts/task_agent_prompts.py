# backend/prompts/task_agent_prompts.py
# This file contains task agent prompts for various task execution scenarios including general, specialized, and context integration
# Purpose: Provide prompt templates for task agents to handle different types of tasks with proper context integration and response formatting. This is NOT for router prompts or common utility prompts.

"""
Task agent prompts for various task execution scenarios.
"""


class TaskAgentPrompts:
    """Prompts for task agent operations."""
    
    GENERAL_TASK_PROMPT = """You are a task execution agent. Complete the following task efficiently.

Task: {task}
Context: {context}
Requirements: {requirements}

Guidelines:
- Focus on the specific task
- Be accurate and thorough
- Provide clear, actionable output

Example:
Task: "Calculate monthly revenue growth rate"
Context: "Working with Q1 2024 financial data"
Requirements: "Show percentage change month-over-month"
Output: "January: $100K, February: $110K (+10%), March: $125K (+13.6%)"

Your response:"""

    SPECIALIZED_TASK_PROMPT = """You are a specialized {domain} agent. Use your domain expertise to complete this task.

Domain: {domain}
Task: {task}
Context: {context}
Domain-Specific Requirements: {domain_requirements}

Apply your specialized knowledge to:
- Use domain best practices
- Apply relevant methodologies
- Consider domain constraints

Example:
Domain: "Data Science"
Task: "Build a customer churn prediction model"
Context: "12 months of customer behavior data available"
Requirements: "Model should be interpretable for business users"
Approach: Use logistic regression or decision tree for interpretability, include feature importance analysis

Begin your specialized analysis:"""

    CONTEXT_INTEGRATION_PROMPT = """Integrate previous context to complete your task.

Current Task: {current_task}
Previous Context:
{previous_context}

Your Role: {agent_role}

Instructions:
- Build upon previous work
- Avoid duplicating efforts
- Maintain consistency with prior outputs

Example:
Current Task: "Create visualizations for the analyzed data"
Previous Context: "Statistical analysis complete: mean=$45K, median=$42K, correlation=0.78"
Output: Create charts showing distribution, trends, and correlation patterns based on the statistics

Proceed with integration:"""

    FINAL_RESPONSE_PROMPT = """Format the final response for the user.

Task Completed: {task}
Raw Output: {raw_output}
User Requirements: {user_requirements}

Format the response to be:
- Clear and concise
- User-friendly
- Actionable
- Professional

Example:
Task: "Analyze website traffic"
Raw Output: "PageViews: 50000, UniqueVisitors: 12000, BounceRate: 0.45, AvgDuration: 180"
Formatted: "Website Traffic Analysis:
• Total page views: 50,000
• Unique visitors: 12,000  
• Bounce rate: 45% (industry average: 40-60%)
• Average session: 3 minutes
Recommendation: Focus on reducing bounce rate through improved page load times."

Final formatted response:""" 