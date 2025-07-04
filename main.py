# main.py
# This file is the main application entry point for the AI Agentic Workflow Launchpad
# Purpose: Orchestrates system initialization, CLI interface, and agent workflow execution. This is NOT for individual agent implementations or configuration management.

"""
AI Agentic Workflow Launchpad - Main Application Entry Point
"""
import sys
import signal
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure backend modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.logger import setup_logging, get_logger
from backend.utils.config_loader import get_config
from backend.llm_clients.llm_factory import LLMFactory
from backend.agents.agent_registry import AgentRegistry
from backend.agents.router_agent import RouterAgent
from backend.agents.task_agent_1 import CalculatorAgent
from backend.agents.task_agent_2 import TaskAgent2
from backend.workflows.sequential_workflow import SequentialWorkflow

# Module-level logger
logger = logging.getLogger(__name__)


class AILaunchpad:
    """Main application class for AI Agentic Workflow Launchpad."""
    
    def __init__(self):
        self.logger = None
        self.config = None
        self.llm_factory = None
        self.agent_registry = None
        self.workflow = None
        self.running = True
        self.ui_logger = None
    
    def setup(self) -> None:
        """Initialize all system components."""
        try:
            # Load configuration
            logger.debug("🔧 Loading configuration...")
            self.config = get_config()
            logger.info("✅ Configuration loaded successfully")
            
            # Initialize logging
            logger.debug("📝 Setting up logging...")
            setup_logging()
            self.logger = get_logger("main")
            self.ui_logger = get_logger("ui")
            self.logger.info("✅ Logging initialized")
            
            # Initialize LLM factory
            logger.debug("🤖 Initializing LLM clients...")
            self.llm_factory = LLMFactory()
            logger.info("✅ LLM factory initialized")
            
            # Initialize agent registry
            logger.debug("📋 Setting up agent registry...")
            self.agent_registry = AgentRegistry()
            logger.info("✅ Agent registry initialized")
            
            # Register agents
            logger.debug("📝 Registering agents...")
            self._register_agents()
            logger.info("✅ Agents registered")
            
            # Create default workflow
            logger.debug("🔄 Creating workflow...")
            self._create_workflow()
            logger.info("✅ Workflow created")
            
            self.logger.info("🚀 System initialization complete!")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Setup failed: {str(e)}")
            else:
                logger.error(f"❌ Setup failed: {str(e)}")
            logger.error(f"❌ Error details: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _register_agents(self) -> None:
        """Register all available agents."""
        logger.debug("🔧 Registering router agent...")
        
        # Register router agent
        self.agent_registry.register(
            name="router",
            agent_class=RouterAgent,
            version="1.0.0",
            capabilities=["routing", "task_analysis"],
            description="Routes tasks to appropriate agents"
        )
        logger.debug("✅ Router agent registered")
        
        # Register task agents
        logger.debug("🔧 Registering calculator agent...")
        self.agent_registry.register(
            name="task_agent_1",
            agent_class=CalculatorAgent,
            version="1.0.0",
            capabilities=["calculator", "mathematical_operations"],
            description="Mathematical calculator with step-by-step reasoning"
        )
        logger.debug("✅ Calculator agent registered")
        
        logger.debug("🔧 Registering task agent 2...")
        self.agent_registry.register(
            name="task_agent_2",
            agent_class=TaskAgent2,
            version="1.0.0",
            capabilities=["complex_reasoning", "planning"],
            description="Handles complex reasoning and planning"
        )
        logger.debug("✅ Task agent 2 registered")
        
        total_agents = len(self.agent_registry.discover())
        logger.info(f"📊 Total agents registered: {total_agents}")
    
    def _create_workflow(self) -> None:
        """Create the default workflow with agents."""
        logger.debug("🔧 Getting workflow configuration...")
        
        # Get default workflow config
        workflow_config = self.config.workflows.get("sequential")
        logger.debug(f"📋 Found workflow config: {workflow_config.name if workflow_config else 'None'}")
        
        # Create agent instances
        agents = []
        logger.debug(f"🔧 Creating agent instances for: {workflow_config.agents if workflow_config else 'None'}...")
        
        # First pass: create non-router agents
        non_router_agents = {}
        failed_agents = []
        for agent_name in workflow_config.agents:
            if agent_name == "router":
                continue  # Skip router for now
                
            logger.debug(f"🔧 Processing agent: {agent_name}")
            
            # Get agent config
            agent_config = self.config.agents.get(agent_name)
            if not agent_config:
                logger.warning(f"⚠️ Agent config not found: {agent_name}")
                failed_agents.append((agent_name, "No configuration found"))
                continue
            
            logger.debug(f"✅ Agent config found for: {agent_name}")
            
            # Get LLM client for agent
            try:
                logger.debug(f"🔧 Getting LLM client for provider: {agent_config.llm_provider}")
                llm_config = self.config.llm_clients.get(agent_config.llm_provider)
                if not llm_config:
                    raise ValueError(f"LLM config not found for provider: {agent_config.llm_provider}")
                    
                llm_client = self.llm_factory.create_client(llm_config)
                logger.debug(f"✅ LLM client created for: {agent_name}")
            except Exception as e:
                logger.error(f"❌ Failed to create LLM client for {agent_name}: {str(e)}")
                failed_agents.append((agent_name, f"LLM client error: {str(e)}"))
                continue
            
            # Create agent instance
            logger.debug(f"🔧 Creating agent instance: {agent_name}")
            try:
                agent = self.agent_registry.create_instance(agent_name, llm_client)
                if agent:
                    agents.append(agent)
                    non_router_agents[agent_name] = agent
                    logger.info(f"✅ Agent instance created: {agent_name}")
                else:
                    logger.error(f"❌ Agent registry returned None for: {agent_name}")
                    failed_agents.append((agent_name, "Agent creation returned None"))
            except Exception as e:
                logger.error(f"❌ Exception creating agent {agent_name}: {str(e)}")
                failed_agents.append((agent_name, f"Creation exception: {str(e)}"))
        
        # Log summary of agent creation
        if failed_agents:
            logger.warning(f"⚠️ Failed to create {len(failed_agents)} agents:")
            for agent_name, reason in failed_agents:
                logger.warning(f"   - {agent_name}: {reason}")
        
        logger.info(f"📊 Successfully created {len(non_router_agents)} non-router agents: {list(non_router_agents.keys())}")
        
        # Second pass: create router agent with available agents
        if "router" in workflow_config.agents:
            logger.debug(f"🔧 Processing router agent...")
            
            # Get router agent config
            router_config = self.config.agents.get("router")
            if router_config:
                logger.debug(f"✅ Router config found")
                
                # Get LLM client for router
                logger.debug(f"🔧 Getting LLM client for provider: {router_config.llm_provider}")
                llm_config = self.config.llm_clients.get(router_config.llm_provider)
                llm_client = self.llm_factory.create_client(llm_config)
                logger.debug(f"✅ LLM client created for router")
                
                # Create router instance with available agents
                logger.debug(f"🔧 Creating router instance with {len(non_router_agents)} available agents...")
                try:
                    router_agent = RouterAgent(
                        llm_client=llm_client,
                        available_agents=non_router_agents
                    )
                    agents.insert(0, router_agent)  # Router should be first
                    logger.info(f"✅ Router agent instance created")
                except Exception as e:
                    logger.error(f"❌ Failed to create router instance: {str(e)}")
            else:
                logger.warning(f"⚠️ Router config not found")
        
        # Create workflow
        logger.debug(f"🔧 Creating workflow with {len(agents)} agents...")
        self.workflow = SequentialWorkflow(
            name=workflow_config.name,
            description=workflow_config.description,
            agents=agents,
            max_steps=workflow_config.max_steps
        )
        
        logger.info(f"✅ Created workflow with {len(agents)} agents")
    
    def run_cli(self) -> None:
        """Run the CLI interface for user interaction."""
        self.ui_logger.info("\n" + "="*60)
        self.ui_logger.info("🚀 AI Agentic Workflow Launchpad")
        self.ui_logger.info("="*60)
        self.ui_logger.info("\n✅ System is ready and running!")
        self.ui_logger.info("Type your question or task. Type 'exit' or 'quit' to stop.")
        self.ui_logger.info("Type 'help' for available commands.\n")
        
        # Initial prompt to make it clear we're ready for input
        self.ui_logger.info("💡 What would you like me to help you with today?")
        
        while self.running:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                
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
                logger.info(f"🤔 Processing user request: {user_input[:50]}...")
                result = self.workflow.execute(user_input)
                
                # Display result
                self._display_result(result)
                
            except KeyboardInterrupt:
                logger.info("⚡ Interrupted by user")
                self.ui_logger.info("\n\n⚡ Interrupted by user")
                break
            except Exception as e:
                import traceback
                self.logger.error(f"❌ Error processing request: {str(e)}\n{traceback.format_exc()}")
                self.ui_logger.error(f"\n❌ An error occurred during processing: {str(e)}")
                self.ui_logger.error("Full traceback below:")
                self.ui_logger.error(traceback.format_exc())
    
    def _show_help(self) -> None:
        """Display help information."""
        self.ui_logger.info("\n📚 Available Commands:")
        self.ui_logger.info("  - Type any question or task to process")
        self.ui_logger.info("  - 'agents' - List available agents")
        self.ui_logger.info("  - 'help'   - Show this help message")
        self.ui_logger.info("  - 'exit'   - Exit the application\n")
    
    def _list_agents(self) -> None:
        """List all available agents."""
        self.ui_logger.info("\n🤖 Available Agents:")
        for name in self.agent_registry.discover():
            info = self.agent_registry.get_agent_info(name)
            self.ui_logger.info(f"  - {name}: {info.description}")
        self.ui_logger.info("")
    
    def _display_result(self, result: Dict[str, Any]) -> None:
        """Display workflow execution result."""
        self.ui_logger.info("\n" + "="*60)
        self.ui_logger.info("📊 Results:")
        self.ui_logger.info("="*60)
        
        if result.get("final_output"):
            self.ui_logger.info(f"\n🎯 Final Answer:\n{result['final_output']}")
        
        self.ui_logger.info(f"\n📈 Execution Summary:")
        self.ui_logger.info(f"  - Total steps: {result.get('total_steps', 0)}")
        self.ui_logger.info(f"  - Agents used: {result.get('agents_executed', 0)}")
        
        self.ui_logger.info("\n" + "="*60 + "\n")
    
    def shutdown(self) -> None:
        """Graceful shutdown of the application."""
        self.running = False
        if self.logger:
            self.logger.info("👋 Shutting down AI Launchpad...")
        
        # Clear LLM client cache
        if self.llm_factory:
            self.llm_factory.clear_cache()
        
        if self.logger:
            self.logger.info("✅ Shutdown complete")


def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logger.info("⚡ Received interrupt signal. Shutting down...")
    ui_logger = get_logger("ui")
    ui_logger.info("\n\n⚡ Received interrupt signal. Shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    logger.info("🚀 Starting AI Launchpad...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run application
    logger.debug("🔧 Creating application instance...")
    app = AILaunchpad()
    
    try:
        # Initialize system
        logger.debug("⚙️ Initializing system...")
        app.setup()
        
        # Run CLI interface
        logger.info("🎯 Starting CLI interface...")
        app.run_cli()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        ui_logger = get_logger("ui")
        ui_logger.error(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Ensure clean shutdown
        app.shutdown()
    
    ui_logger = get_logger("ui")
    ui_logger.info("\n👋 Goodbye!")


if __name__ == "__main__":
    main() 