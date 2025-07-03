"""
Common prompts shared across different agents.
"""


class CommonPrompts:
    """Shared prompt templates for common scenarios."""
    
    ERROR_HANDLING_PROMPT = """An error occurred during task execution. Analyze and recover.

Error Type: {error_type}
Error Message: {error_message}
Task Context: {task_context}
Previous Attempts: {attempts}

Recovery Strategy:
1. Identify root cause
2. Determine if recoverable
3. Suggest alternative approach
4. Provide actionable next steps

Example:
Error: "DatabaseConnectionError"
Message: "Unable to connect to database on port 5432"
Context: "Retrieving customer data for analysis"
Recovery: "Connection failed. Alternative approaches:
- Check if database service is running
- Verify connection credentials
- Use cached data if available
- Try backup database server
- Suggest manual data upload"

Your error recovery plan:"""

    VALIDATION_PROMPT = """Validate the output against requirements.

Output to Validate: {output}
Requirements: {requirements}
Validation Criteria: {criteria}

Check for:
- Completeness
- Accuracy  
- Format compliance
- Business rules

Example:
Output: "Customer analysis: 1000 records processed, 15% churn rate"
Requirements: "Analyze all customers, identify churn rate and risk factors"
Validation: "✓ Record count matches expected
✓ Churn rate calculated
✗ Missing: Risk factors not identified
Status: Partially complete - need risk factor analysis"

Validation result:"""

    CLARIFICATION_PROMPT = """The user request needs clarification.

Original Request: {user_request}
Ambiguous Elements: {ambiguities}
Context: {context}

Generate clarifying questions that are:
- Specific and focused
- Easy to answer
- Relevant to task completion

Example:
Request: "Analyze the data"
Ambiguities: "Which data? What type of analysis? What's the goal?"
Questions:
1. Which dataset should I analyze? (sales, customer, inventory)
2. What type of analysis do you need? (statistical, trend, comparison)  
3. What's the intended use of the results? (report, decision-making, presentation)

Your clarifying questions:""" 