# backend/llm_clients/base_llm_client.py
# This file contains the abstract base class for LLM clients with standardized response handling
# Purpose: Provide the foundational interface for all LLM providers with retry logic, validation, and response formatting. This is NOT for specific provider implementations or configuration loading.

"""
Simplified abstract base class for LLM clients.
Focus on essential functionality for agentic workflow foundation.
"""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..utils.logger import get_logger
from ..utils.config_loader import LLMConfig


@dataclass
class LLMResponse:
    """Standardized response object for LLM interactions."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseClient(ABC):
    """
    Abstract base class for LLM clients providing essential functionality.
    Designed to be simple and extensible for agentic workflows.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = get_logger(f"llm.{config.provider}")
        
        # Validate configuration on initialization
        self.validate_config()
        self.logger.info(f"🧠 Initialized {config.provider} client with model {config.model}")
    
    @abstractmethod
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object with the generated content
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the current model name."""
        pass
    
    @abstractmethod
    def validate_config(self) -> None:
        """Validate the client configuration."""
        pass
    
    def generate_response_with_retry(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response with simple retry logic.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_retries: Maximum number of retries
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse object
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.debug(f"🔄 Attempt {attempt + 1}/{max_retries + 1}")
                response = self.generate_response(prompt, system_prompt, **kwargs)
                
                if self.validate_response(response):
                    self.logger.debug(f"✅ Request completed successfully")
                    return response
                else:
                    raise ValueError("Invalid response received")
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries:
                    # Simple backoff - wait 1 second between retries
                    wait_time = 1.0
                    self.logger.info(f"🔄 Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"❌ All retry attempts exhausted")
        
        # If we get here, all retries failed
        raise last_exception
    
    def validate_response(self, response: LLMResponse) -> bool:
        """
        Basic response validation.
        
        Args:
            response: LLMResponse object
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not response or not response.content:
                self.logger.error("❌ Empty response received")
                return False
            
            if not isinstance(response.content, str):
                self.logger.error("❌ Response content is not a string")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Response validation failed: {str(e)}")
            return False
    
    def __str__(self) -> str:
        return f"{self.config.provider}({self.config.model})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.config.provider}/{self.config.model}>" 