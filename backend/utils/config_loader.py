# backend/utils/config_loader.py
# This file contains the configuration management system with YAML loading and environment variable substitution
# Purpose: Load, validate, and manage application configuration from YAML files with environment variable support. This is NOT for runtime configuration changes or agent-specific settings.

"""
Configuration management system with YAML loading and environment variable substitution.
"""
import os
import re
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, ValidationError, Field
from dotenv import load_dotenv


class LLMConfig(BaseModel):
    """LLM client configuration model."""
    provider: str
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30


class AgentConfig(BaseModel):
    """Agent configuration model."""
    name: str
    description: str
    llm_provider: str
    system_prompt: str
    temperature: float = 0.7
    max_iterations: int = 10
    tools: List[str] = Field(default_factory=list)


class WorkflowConfig(BaseModel):
    """Workflow configuration model."""
    name: str
    description: str
    type: str
    agents: List[str]
    max_steps: int = 20
    timeout: int = 300


class LoggingConfig(BaseModel):
    """Logging configuration model."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5


class AppConfig(BaseModel):
    """Main application configuration model."""
    app_name: str
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # LLM configurations
    llm_clients: Dict[str, LLMConfig]
    default_llm: str
    
    # Agent configurations
    agents: Dict[str, AgentConfig]
    
    # Workflow configurations
    workflows: Dict[str, WorkflowConfig]
    
    # Logging configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Additional settings
    max_concurrent_agents: int = 5
    request_timeout: int = 30
    retry_attempts: int = 3


class ConfigLoader:
    """
    Singleton configuration loader with YAML support and environment variable substitution.
    """
    _instance: Optional['ConfigLoader'] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls) -> 'ConfigLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            # Load environment variables from .env file
            load_dotenv()
            self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML files with environment variable substitution."""
        try:
            # Load default config
            config_data = self._load_yaml_file("config.yml")
            
            # Load local config if exists (overrides default)
            local_config_path = Path("config_local.yml")
            if local_config_path.exists():
                local_config = self._load_yaml_file("config_local.yml")
                config_data = self._merge_configs(config_data, local_config)
            
            # Substitute environment variables
            config_data = self._substitute_env_vars(config_data)
            
            # Validate configuration
            self._config = AppConfig(**config_data)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")
    
    def _load_yaml_file(self, file_path: str) -> Dict[str, Any]:
        """Load YAML file and return parsed data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            if file_path == "config.yml":
                raise FileNotFoundError(f"Required configuration file '{file_path}' not found")
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in '{file_path}': {str(e)}")
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries recursively."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in configuration data."""
        if isinstance(data, dict):
            return {key: self._substitute_env_vars(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            return self._replace_env_vars_in_string(data)
        else:
            return data
    
    def _replace_env_vars_in_string(self, text: str) -> str:
        """Replace environment variables in string using ${VAR_NAME} syntax."""
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            # Support default values with syntax ${VAR_NAME:default_value}
            if ':' in var_name:
                var_name, default_value = var_name.split(':', 1)
                return os.getenv(var_name, default_value)
            else:
                value = os.getenv(var_name)
                if value is None:
                    raise ValueError(f"Environment variable '{var_name}' is not set")
                return value
        
        return re.sub(pattern, replace_var, text)
    
    @property
    def config(self) -> AppConfig:
        """Get the loaded configuration."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config
    
    def get_llm_config(self, provider: str) -> LLMConfig:
        """Get LLM configuration for a specific provider."""
        if provider not in self.config.llm_clients:
            raise ValueError(f"LLM provider '{provider}' not configured")
        return self.config.llm_clients[provider]
    
    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get agent configuration by name."""
        if agent_name not in self.config.agents:
            raise ValueError(f"Agent '{agent_name}' not configured")
        return self.config.agents[agent_name]
    
    def get_workflow_config(self, workflow_name: str) -> WorkflowConfig:
        """Get workflow configuration by name."""
        if workflow_name not in self.config.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not configured")
        return self.config.workflows[workflow_name]
    
    def reload(self) -> None:
        """Reload configuration from files."""
        self._config = None
        self._load_config()
    
    def validate_required_env_vars(self) -> List[str]:
        """Validate that all required environment variables are set."""
        missing_vars = []
        
        # Check LLM API keys
        for provider, llm_config in self.config.llm_clients.items():
            if not llm_config.api_key or llm_config.api_key.startswith("your_"):
                missing_vars.append(f"{provider.upper()}_API_KEY")
        
        return missing_vars


# Global configuration instance
config_loader = ConfigLoader()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config_loader.config 