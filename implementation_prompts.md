# Implementation Prompts for AI Agentic Launch Pad

## Phase 1: Project Setup and Configuration

### Prompt 1.1: Basic Project Setup
```
Create a Python project structure for an AI agentic workflow launchpad. Create the following files:

1. requirements.txt with dependencies:
   - langchain==0.3.26
   - langchain-openai
   - langchain-anthropic
   - langchain-google-genai
   - pydantic
   - pyyaml
   - rich
   - python-dotenv

2. .gitignore file for Python project with common ignores including:
   - __pycache__/
   - *.pyc
   - .env
   - .venv/
   - config_local.yml
   - logs/

3. .env.example file with placeholder environment variables:
   - OPENAI_API_KEY=your_openai_key_here
   - ANTHROPIC_API_KEY=your_anthropic_key_here
   - GEMINI_API_KEY=your_gemini_key_here

4. Create all the empty __init__.py files for the package structure shown in the directory tree.
```

### Prompt 1.2: Configuration System
```
Create a configuration management system using the following requirements:

File: backend/utils/config_loader.py
- Create a ConfigLoader class that loads YAML configuration
- Support environment variable substitution using ${VAR_NAME} syntax
- Implement singleton pattern for global config access
- Include validation for required fields
- Support loading from multiple config files (default config.yml, optional config_local.yml)
- Use pydantic for configuration validation

File: config.yml
- Create the main configuration file with the structure provided in the project overview
- Include all sections: app_name, environment, LLM settings, agent settings, etc.
- Use environment variable placeholders for sensitive data
```

### Prompt 1.3: Logging System
```
Create a comprehensive logging system:

File: backend/utils/logger.py
- Create a Logger class that uses Rich for formatted output
- Support different log levels (DEBUG, INFO, WARNING, ERROR)
- Include file logging option (configurable)
- Support LangChain debug logging integration
- Include structured logging with timestamps and context
- Make it configurable through the config.yml file
- Support both console and file output
```

## Phase 2: LLM Client Abstraction Layer

### Prompt 2.1: Base LLM Client
```
Create an abstract base class for LLM clients:

File: backend/llm_clients/base_llm_client.py
- Create an abstract BaseClient class with ABC
- Define abstract methods: generate_response, get_model_name, validate_config
- Include common functionality: retry logic, error handling, response validation
- Support for streaming responses (optional)
- Include rate limiting considerations
- Add method for cost tracking (tokens used)
```

### Prompt 2.2: OpenAI Client Implementation
```
Implement OpenAI client:

File: backend/llm_clients/openai_client.py
- Inherit from BaseClient
- Use langchain-openai ChatOpenAI
- Implement all abstract methods
- Include error handling for API failures
- Support for different OpenAI models (gpt-3.5-turbo, gpt-4, etc.)
- Configuration-driven model selection
- Proper API key management
```

### Prompt 2.3: Anthropic Client Implementation
```
Implement Anthropic client:

File: backend/llm_clients/anthropic_client.py
- Inherit from BaseClient
- Use langchain-anthropic ChatAnthropic
- Implement all abstract methods
- Support for Claude models (claude-3-opus, claude-3-sonnet, etc.)
- Include proper error handling
- Configuration-driven model selection
```

### Prompt 2.4: Gemini Client Implementation
```
Implement Google Gemini client:

File: backend/llm_clients/gemini_client.py
- Inherit from BaseClient
- Use langchain-google-genai ChatGoogleGenerativeAI
- Implement all abstract methods
- Support for Gemini models
- Include error handling for Google API
- Configuration-driven setup
```

### Prompt 2.5: LLM Factory
```
Create a factory for LLM clients:

File: backend/llm_clients/llm_factory.py
- Create LLMFactory class
- Method to create LLM client based on configuration
- Support for all three providers (OpenAI, Anthropic, Gemini)
- Include validation for provider availability
- Error handling for unsupported providers
- Caching of client instances for performance
```

## Phase 3: System Prompts Management

### Prompt 3.1: Prompt Templates
```
Create system prompt management:

File: backend/system_prompts/router_prompts.py
- Create RouterPrompts class with templates for:
  - TASK_DECOMPOSITION_PROMPT: For breaking down user queries into tasks
  - AGENT_SELECTION_PROMPT: For selecting appropriate agents
  - CONTEXT_SUMMARY_PROMPT: For summarizing context between agents
  - REACT_PROMPT: For ReAct pattern implementation
- Use string templates with placeholder variables
- Include examples in prompts for better performance

File: backend/system_prompts/task_agent_prompts.py
- Create TaskAgentPrompts class with templates for:
  - GENERAL_TASK_PROMPT: For general purpose tasks
  - SPECIALIZED_TASK_PROMPT: For specific domain tasks
  - CONTEXT_INTEGRATION_PROMPT: For using context from previous agents
  - FINAL_RESPONSE_PROMPT: For formatting final responses

File: backend/system_prompts/common_prompts.py
- Create CommonPrompts class with shared templates:
  - ERROR_HANDLING_PROMPT: For error recovery
  - VALIDATION_PROMPT: For output validation
  - CLARIFICATION_PROMPT: For asking clarifying questions
```

### Prompt 3.2: Prompt Loader Utility
```
Create prompt loading utility:

File: backend/utils/prompt_loader.py
- Create PromptLoader class
- Method to load prompts from files or classes
- Support for prompt templating with variables
- Validation of prompt templates
- Caching of loaded prompts
- Support for dynamic prompt modification
```

## Phase 4: Context Management

### Prompt 4.1: Context Manager
```
Create context sharing system:

File: backend/utils/context_manager.py
- Create ContextManager class
- Methods to store, retrieve, and update context
- Support for different context types (conversation, task, agent)
- Context compression for long conversations
- Context relevance scoring
- Thread-safe context management
- Integration with LangChain memory components
```

## Phase 5: Base Agent Framework

### Prompt 5.1: Base Agent Class
```
Create abstract base agent:

File: backend/agents/base_agent.py
- Create abstract BaseAgent class
- Properties: name, description, tools, llm_client
- Abstract methods: execute, validate_input, format_output
- Common functionality: logging, error handling, context management
- Integration with LangChain Agent framework
- Support for tool usage
- State management for agent execution
```

### Prompt 5.2: Router Agent Implementation
```
Create the main router agent:

File: backend/agents/router_agent.py
- Inherit from BaseAgent
- Implement ReAct pattern using LangChain
- Methods for:
  - Task decomposition from user input
  - Agent selection based on available agents
  - Sequential task execution
  - Context passing between agents
  - Result aggregation
- Use LangChain's AgentExecutor
- Include retry logic for failed tasks
```

### Prompt 5.3: Task Agent Templates
```
Create template task agents:

File: backend/agents/task_agent_1.py
- Create TaskAgent1 class inheriting from BaseAgent
- Implement as a general-purpose agent
- Include placeholder logic for task execution
- Support for receiving context from previous agents
- Output formatting for next agent consumption

File: backend/agents/task_agent_2.py
- Create TaskAgent2 class inheriting from BaseAgent
- Implement as a specialized agent template
- Include different prompt templates
- Show how to customize agent behavior
- Demonstrate tool usage integration
```

### Prompt 5.4: Agent Registry
```
Create agent management system:

File: backend/agents/agent_registry.py
- Create AgentRegistry class
- Methods to register and discover agents
- Dynamic agent loading based on configuration
- Agent availability checking
- Agent capability matching
- Support for agent versioning
```

## Phase 6: Tools Integration

### Prompt 6.1: Base Tool Framework
```
Create tool framework:

File: backend/tools/base_tool.py
- Create abstract BaseTool class
- Integration with LangChain tools
- Standard interface for all tools
- Error handling and validation
- Tool metadata and documentation
```

### Prompt 6.2: Example Tools
```
Create example tools:

File: backend/tools/example_tools.py
- Create 2-3 example tools demonstrating:
  - Simple calculation tool
  - Text processing tool
  - Mock API call tool
- Show how to integrate with LangChain tool framework
- Include proper error handling and validation
```

## Phase 7: Workflow Management

### Prompt 7.1: Base Workflow
```
Create workflow framework:

File: backend/workflows/base_workflow.py
- Create abstract BaseWorkflow class
- Methods for workflow execution
- Support for different execution patterns
- Error handling and rollback capabilities
- Workflow state management
```

### Prompt 7.2: Sequential Workflow
```
Create sequential workflow implementation:

File: backend/workflows/sequential_workflow.py
- Inherit from BaseWorkflow
- Implement sequential task execution
- Context passing between steps
- Progress tracking
- Failure recovery mechanisms
```

## Phase 8: Main Application

### Prompt 8.1: Main Application Entry Point
```
Create the main application:

File: main.py
- Create main function that:
  - Loads configuration
  - Initializes logging
  - Sets up LLM clients
  - Registers agents
  - Creates workflow executor
  - Provides CLI interface for testing
- Include example usage
- Error handling and graceful shutdown
```

## Phase 9: Testing Framework

### Prompt 9.1: Test Structure
```
Create test framework:

Files: tests/test_*.py
- Create unit tests for:
  - Configuration loading
  - LLM client functionality
  - Agent execution
  - Context management
  - Workflow execution
- Use pytest framework
- Include mock objects for external APIs
- Create integration tests for full workflow
```

## Phase 10: Documentation and Examples

### Prompt 10.1: Documentation
```
Create documentation:

File: README.md
- Project overview and features
- Installation instructions
- Quick start guide
- Configuration options
- Examples of usage
- Architecture explanation

File: AGENTS.md
- Guide for creating new agents
- Agent interface documentation
- Best practices
- Examples of agent implementations
```

### Prompt 10.2: Example Implementations
```
Create example applications:

File: examples/simple_workflow_example.py
- Simple workflow demonstrating basic functionality
- Single agent execution
- Basic context sharing

File: examples/multi_agent_example.py
- Complex workflow with multiple agents
- Context sharing between agents
- Error handling demonstration
```

## Implementation Order

1. **Phase 1**: Project setup and configuration
2. **Phase 2**: LLM client abstraction layer
3. **Phase 3**: System prompts management
4. **Phase 4**: Context management
5. **Phase 5**: Base agent framework
6. **Phase 6**: Tools integration
7. **Phase 7**: Workflow management
8. **Phase 8**: Main application
9. **Phase 9**: Testing framework
10. **Phase 10**: Documentation and examples

Each phase builds upon the previous ones, ensuring a solid foundation for the agentic workflow launchpad.