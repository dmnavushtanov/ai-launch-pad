# backend/utils/logger.py
# This file contains the comprehensive logging system with Rich formatting and file logging support
# Purpose: Provide centralized logging with console and file output, LangChain integration, and structured logging for agents and workflows. This is NOT for configuration management or direct application logic.

"""
Comprehensive logging system with Rich formatting and file logging support.
"""
import os
import logging
import logging.handlers
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from rich.traceback import install as install_rich_traceback

from .config_loader import get_config


class Logger:
    """
    Comprehensive logging system with Rich formatting and file logging.
    """
    
    _loggers: Dict[str, logging.Logger] = {}
    _console: Optional[Console] = None
    _initialized: bool = False
    
    @classmethod
    def get_logger(cls, name: str = "ai_launchpad") -> logging.Logger:
        """Get or create a logger instance."""
        if not cls._initialized:
            cls._initialize_logging()
        
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        
        return cls._loggers[name]
    
    @classmethod
    def _initialize_logging(cls) -> None:
        """Initialize the logging system with Rich and configuration."""
        try:
            config = get_config()
            logging_config = config.logging
            
            # Install Rich traceback handler for better error formatting
            install_rich_traceback(show_locals=config.debug)
            
            # Create Rich console with custom theme
            cls._console = Console(
                theme=Theme({
                    "logging.level.debug": "dim blue",
                    "logging.level.info": "green",
                    "logging.level.warning": "yellow",
                    "logging.level.error": "red bold",
                    "logging.level.critical": "red bold reverse",
                    "logging.timestamp": "dim",
                    "logging.logger": "blue",
                })
            )
            
            # Set global logging level
            logging.getLogger().setLevel(getattr(logging, logging_config.level.upper()))
            
            # Create logs directory if file logging is enabled
            if logging_config.file_path:
                log_path = Path(logging_config.file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
            
            cls._initialized = True
            
        except Exception as e:
            # Fallback to simple logging if config fails
            logging.basicConfig(level=logging.INFO)
            logging.error(f"Failed to initialize logging system: {e}")
    
    @classmethod
    def _create_logger(cls, name: str) -> logging.Logger:
        """Create a configured logger instance."""
        logger = logging.getLogger(name)
        logger.handlers.clear()  # Clear any existing handlers
        
        try:
            config = get_config()
            logging_config = config.logging
            
            # Console handler with Rich formatting
            # Special configuration for UI logger - no timestamps or levels
            if name == "ui":
                console_handler = RichHandler(
                    console=cls._console,
                    show_time=False,
                    show_level=False,
                    show_path=False,
                    markup=True,
                    rich_tracebacks=True,
                    tracebacks_show_locals=config.debug,
                )
            else:
                console_handler = RichHandler(
                    console=cls._console,
                    show_time=True,
                    show_level=True,
                    show_path=config.debug,
                    markup=True,
                    rich_tracebacks=True,
                    tracebacks_show_locals=config.debug,
                )
            console_handler.setLevel(getattr(logging, logging_config.level.upper()))
            logger.addHandler(console_handler)
            
            # File handler if configured
            if logging_config.file_path:
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=logging_config.file_path,
                    maxBytes=logging_config.max_file_size,
                    backupCount=logging_config.backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, logging_config.level.upper()))
                
                # Create detailed formatter for file output
                file_formatter = logging.Formatter(
                    fmt=logging_config.format,
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            
            logger.setLevel(getattr(logging, logging_config.level.upper()))
            
        except Exception as e:
            # Fallback handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(console_handler)
            logger.error(f"Failed to configure logger {name}: {e}")
        
        return logger
    
    @classmethod
    def setup_langchain_logging(cls) -> None:
        """Setup LangChain debug logging integration."""
        try:
            config = get_config()
            
            # Configure LangChain logging
            langchain_logger = logging.getLogger("langchain")
            langchain_openai_logger = logging.getLogger("langchain.llms.openai")
            langchain_anthropic_logger = logging.getLogger("langchain.llms.anthropic")
            
            # Set level based on debug mode
            if config.debug:
                langchain_logger.setLevel(logging.DEBUG)
                langchain_openai_logger.setLevel(logging.DEBUG)
                langchain_anthropic_logger.setLevel(logging.DEBUG)
                
                # Enable verbose logging for LangChain
                os.environ["LANGCHAIN_VERBOSE"] = "true"
                os.environ["LANGCHAIN_DEBUG"] = "true"
            else:
                langchain_logger.setLevel(logging.WARNING)
                langchain_openai_logger.setLevel(logging.WARNING)
                langchain_anthropic_logger.setLevel(logging.WARNING)
            
            # Add our handlers to LangChain loggers
            main_logger = cls.get_logger("langchain")
            for handler in main_logger.handlers:
                if handler not in langchain_logger.handlers:
                    langchain_logger.addHandler(handler)
            
        except Exception as e:
            cls.get_logger().error(f"Failed to setup LangChain logging: {e}")
    
    @classmethod
    def log_context(cls, logger: logging.Logger, context: Dict[str, Any], level: str = "INFO") -> None:
        """Log structured context information."""
        try:
            log_level = getattr(logging, level.upper())
            
            # Format context as structured data
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            logger.log(log_level, f"Context: {context_str}")
            
        except Exception as e:
            logger.error(f"Failed to log context: {e}")
    
    @classmethod
    def log_agent_activity(cls, agent_name: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log agent activity with structured format."""
        logger = cls.get_logger(f"agent.{agent_name}")
        
        context = {
            "agent": agent_name,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            context.update(details)
        
        cls.log_context(logger, context, "INFO")
    
    @classmethod
    def log_workflow_step(cls, workflow_name: str, step: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log workflow step execution."""
        logger = cls.get_logger(f"workflow.{workflow_name}")
        
        context = {
            "workflow": workflow_name,
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        if details:
            context.update(details)
        
        level = "ERROR" if status == "failed" else "INFO"
        cls.log_context(logger, context, level)
    
    @classmethod
    def log_llm_request(cls, provider: str, model: str, tokens_used: Optional[int] = None, cost: Optional[float] = None) -> None:
        """Log LLM API request details."""
        logger = cls.get_logger(f"llm.{provider}")
        
        context = {
            "provider": provider,
            "model": model,
            "timestamp": datetime.now().isoformat()
        }
        
        if tokens_used:
            context["tokens"] = tokens_used
        if cost:
            context["cost"] = f"${cost:.4f}"
        
        cls.log_context(logger, context, "INFO")
    
    @classmethod
    def configure_third_party_loggers(cls) -> None:
        """Configure third-party library loggers to reduce noise."""
        try:
            config = get_config()
            
            # Reduce noise from verbose libraries
            noisy_loggers = [
                "urllib3.connectionpool",
                "requests.packages.urllib3",
                "httpx",
                "httpcore",
                "openai._base_client",
                "anthropic._base_client"
            ]
            
            level = logging.DEBUG if config.debug else logging.WARNING
            
            for logger_name in noisy_loggers:
                logging.getLogger(logger_name).setLevel(level)
                
        except Exception as e:
            cls.get_logger().error(f"Failed to configure third-party loggers: {e}")


# Convenience functions for easy access
def get_logger(name: str = "ai_launchpad") -> logging.Logger:
    """Get a logger instance."""
    return Logger.get_logger(name)


def setup_logging() -> None:
    """Initialize the complete logging system."""
    Logger.setup_langchain_logging()
    Logger.configure_third_party_loggers()
    
    logger = get_logger()
    logger.info("🚀 AI Launchpad logging system initialized")


def log_agent_activity(agent_name: str, action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log agent activity."""
    Logger.log_agent_activity(agent_name, action, details)


def log_workflow_step(workflow_name: str, step: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log workflow step."""
    Logger.log_workflow_step(workflow_name, step, status, details)


def log_llm_request(provider: str, model: str, tokens_used: Optional[int] = None, cost: Optional[float] = None) -> None:
    """Log LLM request."""
    Logger.log_llm_request(provider, model, tokens_used, cost) 