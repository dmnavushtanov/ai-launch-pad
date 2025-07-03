# README.md
# This is the main documentation for the AI Agentic Workflow Launchpad
# Purpose: Provide project overview, installation guide, usage examples, and architecture explanation

# 🚀 AI Agentic Workflow Launchpad

A simple, modular framework for building multi-agent AI systems using LangChain and various LLM providers.

## 📋 Features

- **Multi-Agent System**: Coordinate multiple AI agents to solve complex tasks
- **Multiple LLM Support**: OpenAI, Anthropic Claude, Google Gemini
- **Flexible Workflows**: Sequential task execution with context sharing
- **Router Agent**: Intelligent task routing to specialized agents
- **Clean Architecture**: Modular, extensible design
- **CLI Interface**: Interactive command-line for testing
- **Comprehensive Logging**: Rich formatted logs with file output

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- API keys for LLM providers (OpenAI, Anthropic, or Gemini)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-launch-pad
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here
```

## 🚀 Quick Start

Run the application:
```bash
python main.py
```

You'll see an interactive prompt:
```
🚀 AI Agentic Workflow Launchpad
============================================================

Type your question or task. Type 'exit' or 'quit' to stop.
Type 'help' for available commands.

👤 You: What is the weather like in Paris?
```

### Available Commands

- Type any question or task to process
- `agents` - List available agents
- `help` - Show help message
- `exit` - Exit the application

## ⚙️ Configuration

Edit `config.yml` to customize:

### LLM Providers
```yaml
llm_clients:
  openai:
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
```

### Agent Configuration
```yaml
agents:
  router:
    name: "Router Agent"
    llm_provider: "openai"
    system_prompt: "Your custom prompt..."
```

### Workflow Settings
```yaml
workflows:
  sequential:
    agents: ["router", "task_agent_1", "task_agent_2"]
    max_steps: 20
```

## 📖 Usage Examples

### Simple Question
```
👤 You: Explain quantum computing in simple terms

🤔 Processing your request...

📊 Results:
============================================================

🎯 Final Answer:
Quantum computing is like having a super-powered calculator that can try many solutions at once...

📈 Execution Summary:
  - Total steps: 3
  - Agents used: 3
```

### Complex Task
```
👤 You: Create a business plan outline for a sustainable coffee shop

🤔 Processing your request...

📊 Results:
============================================================

🎯 Final Answer:
Here's a comprehensive business plan outline:
1. Executive Summary
2. Market Analysis
...
```

## 🏗️ Architecture

### System Components

```
┌─────────────────┐
│   CLI Interface │
└────────┬────────┘
         │
┌────────▼────────┐
│   Main App      │
│  (Orchestrator) │
└────────┬────────┘
         │
┌────────▼────────┐     ┌─────────────┐
│  Agent Registry │────►│ LLM Factory │
└────────┬────────┘     └─────────────┘
         │
┌────────▼────────┐
│    Workflow     │
│    Executor     │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬────────┐
    │         │         │        │
┌───▼───┐ ┌──▼───┐ ┌───▼───┐ ┌──▼───┐
│Router │ │Agent1│ │Agent2 │ │ ...  │
└───────┘ └──────┘ └───────┘ └──────┘
```

### Key Modules

- **`main.py`**: Application entry point and CLI
- **`backend/agents/`**: Agent implementations
- **`backend/llm_clients/`**: LLM provider integrations
- **`backend/workflows/`**: Workflow execution logic
- **`backend/utils/`**: Configuration, logging, utilities

### Workflow Execution

1. User submits a task via CLI
2. Router agent analyzes and routes to appropriate agent
3. Task agents process sequentially
4. Each agent passes context to the next
5. Final result returned to user

## 🔧 Extending the System

### Adding New Agents

See [AGENTS.md](AGENTS.md) for detailed guide on creating custom agents.

### Adding LLM Providers

1. Create new client in `backend/llm_clients/`
2. Inherit from `BaseClient`
3. Register in `LLMFactory`

### Custom Workflows

1. Create new workflow in `backend/workflows/`
2. Inherit from `BaseWorkflow`
3. Configure in `config.yml`

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `GEMINI_API_KEY` | Google Gemini key | Optional |
| `LOG_LEVEL` | Logging level | INFO |
| `DEBUG` | Debug mode | false |

## 🤝 Contributing

1. Keep it simple - avoid over-engineering
2. Follow existing patterns
3. Add tests for new features
4. Update documentation

## 📄 License

[Your License Here] 