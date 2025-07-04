# backend/agents/agent_registry.py
# This file contains the AgentRegistry for managing and discovering agents
# Purpose: Register agents, load them dynamically from config, check availability, match capabilities, and support versioning

import importlib
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from .base_agent import BaseAgent
from ..utils.logger import get_logger
from ..utils.config_loader import ConfigLoader


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    name: str
    agent_class: Type[BaseAgent]
    version: str
    capabilities: List[str]
    description: str


class AgentRegistry:
    """Registry for managing agent discovery and instantiation."""
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._instances: Dict[str, BaseAgent] = {}
        self.logger = get_logger("agent_registry")
        self.config_loader = ConfigLoader()
    
    def register(
        self,
        name: str,
        agent_class: Type[BaseAgent],
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None,
        description: str = ""
    ) -> None:
        """
        Register an agent class.
        
        Args:
            name: Agent name
            agent_class: Agent class
            version: Agent version
            capabilities: List of capabilities
            description: Agent description
        """
        if name in self._agents:
            self.logger.warning(f"Overwriting existing agent: {name}")
        
        agent_info = AgentInfo(
            name=name,
            agent_class=agent_class,
            version=version,
            capabilities=capabilities or [],
            description=description
        )
        
        self._agents[name] = agent_info
        self.logger.info(f"Registered agent: {name} v{version}")
    
    def discover(self, capability: Optional[str] = None) -> List[str]:
        """
        Discover available agents.
        
        Args:
            capability: Optional capability filter
            
        Returns:
            List of agent names
        """
        if capability:
            return [
                name for name, info in self._agents.items()
                if capability in info.capabilities
            ]
        return list(self._agents.keys())
    
    def load_from_config(self) -> None:
        """Load agents dynamically based on configuration."""
        config = self.config_loader.load_config()
        agents_config = config.get("agents", {})
        
        for agent_name, agent_config in agents_config.items():
            try:
                # Try to import the agent module dynamically
                module_name = f"backend.agents.{agent_name}"
                module = importlib.import_module(module_name)
                
                # Get the agent class
                class_name = self._get_class_name(agent_name)
                agent_class = getattr(module, class_name, None)
                
                if agent_class and issubclass(agent_class, BaseAgent):
                    # Extract capabilities from tools
                    tools = agent_config.get("tools", [])
                    
                    # Register the agent
                    self.register(
                        name=agent_name,
                        agent_class=agent_class,
                        version="1.0.0",
                        capabilities=tools,
                        description=agent_config.get("description", "")
                    )
                else:
                    self.logger.warning(f"No valid agent class found for: {agent_name}")
                    
            except ImportError:
                self.logger.debug(f"Agent module not found: {agent_name}")
            except Exception as e:
                self.logger.error(f"Error loading agent {agent_name}: {str(e)}")
    
    def is_available(self, name: str) -> bool:
        """
        Check if an agent is available.
        
        Args:
            name: Agent name
            
        Returns:
            True if available
        """
        return name in self._agents
    
    def match_capability(self, required_capabilities: List[str]) -> List[str]:
        """
        Find agents matching required capabilities.
        
        Args:
            required_capabilities: List of required capabilities
            
        Returns:
            List of matching agent names
        """
        matching_agents = []
        
        for name, info in self._agents.items():
            if all(cap in info.capabilities for cap in required_capabilities):
                matching_agents.append(name)
        
        return matching_agents
    
    def get_agent_info(self, name: str) -> Optional[AgentInfo]:
        """
        Get agent information.
        
        Args:
            name: Agent name
            
        Returns:
            AgentInfo or None
        """
        return self._agents.get(name)
    
    def create_instance(self, name: str, llm_client: Any) -> Optional[BaseAgent]:
        """
        Create an agent instance.
        
        Args:
            name: Agent name
            llm_client: LLM client instance
            
        Returns:
            Agent instance or None
        """
        if name not in self._agents:
            self.logger.error(f"Agent not found: {name}")
            return None
        
        try:
            agent_info = self._agents[name]
            self.logger.info(f"Creating instance of {name} using {agent_info.agent_class.__name__}")
            
            # Try to create the agent instance with detailed error tracking
            try:
                agent_instance = agent_info.agent_class(llm_client=llm_client)
            except TypeError as e:
                self.logger.error(f"TypeError creating {name}: {str(e)}")
                self.logger.error(f"Agent class: {agent_info.agent_class}")
                self.logger.error(f"This might be due to missing or incorrect constructor parameters")
                raise
            except ImportError as e:
                self.logger.error(f"ImportError creating {name}: {str(e)}")
                self.logger.error(f"Missing dependency. Please ensure all required packages are installed.")
                self.logger.error(f"For {name}, you might need: pip install langchain langchain-community")
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error creating {name}: {type(e).__name__}: {str(e)}")
                import traceback
                self.logger.error(f"Full traceback:\n{traceback.format_exc()}")
                raise
            
            # Cache the instance
            self._instances[name] = agent_instance
            
            self.logger.info(f"✅ Successfully created instance of agent: {name}")
            return agent_instance
            
        except Exception as e:
            self.logger.error(f"Failed to create agent {name}: {str(e)}")
            return None
    
    def get_instance(self, name: str) -> Optional[BaseAgent]:
        """
        Get cached agent instance.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None
        """
        return self._instances.get(name)
    
    def list_versions(self) -> Dict[str, str]:
        """
        List all agents with versions.
        
        Returns:
            Dictionary of agent names to versions
        """
        return {name: info.version for name, info in self._agents.items()}
    
    def _get_class_name(self, agent_name: str) -> str:
        """Convert agent name to class name."""
        # Convert snake_case to PascalCase
        parts = agent_name.split("_")
        return "".join(part.capitalize() for part in parts) 