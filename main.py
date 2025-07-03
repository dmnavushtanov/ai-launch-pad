"""
AI Agentic Workflow Launchpad - Main Application Entry Point
"""
import sys
import signal
from typing import Optional, Dict, Any

# Ensure backend modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.logger import setup_logging, get_logger
from backend.utils.config_loader import get_config
from backend.llm_clients.llm_factory import LLMFactory
from backend.agents.agent_registry import AgentRegistry
from backend.agents.router_agent import RouterAgent
from backend.agents.task_agent_1 import TaskAgent1
from backend.agents.task_agent_2 import TaskAgent2
from backend.workflows.sequential_workflow import SequentialWorkflow


class AILaunchpad:
    """Main application class for AI Agentic Workflow Launchpad."""
    
    def __init__(self):
        self.logger = None
        self.config = None
        self.llm_factory = None
        self.agent_registry = None
        self.workflow = None
        self.running = True
    
    def setup(self) -> None:
        """Initialize all system components."""
        try:
            # Load configuration
            print("🔧 Loading configuration...")
            self.config = get_config()
            
            # Initialize logging
            print("📝 Setting up logging...")
            setup_logging()
            self.logger = get_logger("main")
            self.logger.info("✅ Logging initialized")
            
            # Initialize LLM factory
            self.logger.info("🤖 Initializing LLM clients...")
            self.llm_factory = LLMFactory()
            
            # Initialize agent registry
            self.logger.info("📋 Setting up agent registry...")
            self.agent_registry = AgentRegistry()
            
            # Register agents
            self._register_agents()
            
            # Create default workflow
            self._create_workflow()
            
            self.logger.info("🚀 System initialization complete!")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Setup failed: {str(e)}")
            else:
                print(f"❌ Setup failed: {str(e)}")
            raise
    
    def _register_agents(self) -> None:
        """Register all available agents."""
        self.logger.info("📝 Registering agents...")
        
        # Register router agent
        self.agent_registry.register(
            name="router",
            agent_class=RouterAgent,
            version="1.0.0",
            capabilities=["routing", "task_analysis"],
            description="Routes tasks to appropriate agents"
        )
        
        # Register task agents
        self.agent_registry.register(
            name="task_agent_1",
            agent_class=TaskAgent1,
            version="1.0.0",
            capabilities=["general_tasks", "analysis"],
            description="Handles general tasks and analysis"
        )
        
        self.agent_registry.register(
            name="task_agent_2",
            agent_class=TaskAgent2,
            version="1.0.0",
            capabilities=["complex_reasoning", "planning"],
            description="Handles complex reasoning and planning"
        )
        
        self.logger.info(f"✅ Registered {len(self.agent_registry.discover())} agents")
    
    def _create_workflow(self) -> None:
        """Create the default workflow with agents."""
        self.logger.info("🔄 Creating workflow...")
        
        # Get default workflow config
        workflow_config = self.config.workflows.get("sequential")
        
        # Create agent instances
        agents = []
        for agent_name in workflow_config.agents:
            # Get agent config
            agent_config = self.config.agents.get(agent_name)
            if not agent_config:
                self.logger.warning(f"⚠️ Agent config not found: {agent_name}")
                continue
            
            # Get LLM client for agent
            llm_config = self.config.llm_clients.get(agent_config.llm_provider)
            llm_client = self.llm_factory.create_client(llm_config)
            
            # Create agent instance
            agent = self.agent_registry.create_instance(agent_name, llm_client)
            if agent:
                agents.append(agent)
        
        # Create workflow
        self.workflow = SequentialWorkflow(
            name=workflow_config.name,
            agents=agents,
            max_steps=workflow_config.max_steps
        )
        
        self.logger.info(f"✅ Created workflow with {len(agents)} agents")
    
    def run_cli(self) -> None:
        """Run the CLI interface for user interaction."""
        print("\n" + "="*60)
        print("🚀 AI Agentic Workflow Launchpad")
        print("="*60)
        print("\nType your question or task. Type 'exit' or 'quit' to stop.")
        print("Type 'help' for available commands.\n")
        
        while self.running:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'agents':
                    self._list_agents()
                    continue
                elif not user_input:
                    continue
                
                # Process the task
                print("\n🤔 Processing your request...\n")
                result = self.workflow.execute(user_input)
                
                # Display result
                self._display_result(result)
                
            except KeyboardInterrupt:
                print("\n\n⚡ Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error processing request: {str(e)}")
                print(f"\n❌ Error: {str(e)}\n")
    
    def _show_help(self) -> None:
        """Display help information."""
        print("\n📚 Available Commands:")
        print("  - Type any question or task to process")
        print("  - 'agents' - List available agents")
        print("  - 'help'   - Show this help message")
        print("  - 'exit'   - Exit the application\n")
    
    def _list_agents(self) -> None:
        """List all available agents."""
        print("\n🤖 Available Agents:")
        for name in self.agent_registry.discover():
            info = self.agent_registry.get_agent_info(name)
            print(f"  - {name}: {info.description}")
        print()
    
    def _display_result(self, result: Dict[str, Any]) -> None:
        """Display workflow execution result."""
        print("\n" + "="*60)
        print("📊 Results:")
        print("="*60)
        
        if result.get("final_output"):
            print(f"\n🎯 Final Answer:\n{result['final_output']}")
        
        print(f"\n📈 Execution Summary:")
        print(f"  - Total steps: {result.get('total_steps', 0)}")
        print(f"  - Agents used: {result.get('agents_executed', 0)}")
        
        print("\n" + "="*60 + "\n")
    
    def shutdown(self) -> None:
        """Graceful shutdown of the application."""
        self.running = False
        self.logger.info("👋 Shutting down AI Launchpad...")
        
        # Clear LLM client cache
        if self.llm_factory:
            self.llm_factory.clear_cache()
        
        self.logger.info("✅ Shutdown complete")


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n\n⚡ Received interrupt signal. Shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run application
    app = AILaunchpad()
    
    try:
        # Initialize system
        app.setup()
        
        # Run CLI interface
        app.run_cli()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        # Ensure clean shutdown
        app.shutdown()
    
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main() 