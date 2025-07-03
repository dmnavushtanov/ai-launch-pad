"""
OpenAI client implementation using langchain-openai.
"""
import os
import tiktoken
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .base_llm_client import BaseClient, LLMResponse
from ..utils.config_loader import LLMConfig


class OpenAIClient(BaseClient):
    """OpenAI client using langchain-openai ChatOpenAI."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = self._get_api_key()
        self.client = self._create_client()
        self.tokenizer = self._get_tokenizer()
    
    def _get_api_key(self) -> str:
        """Get OpenAI API key from config or environment."""
        api_key = getattr(self.config, 'api_key', None) or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or OPENAI_API_KEY environment variable")
        return api_key
    
    def _create_client(self) -> ChatOpenAI:
        """Create ChatOpenAI client."""
        return ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.config.model,
            temperature=getattr(self.config, 'temperature', 0.7),
            max_tokens=getattr(self.config, 'max_tokens', None),
            request_timeout=getattr(self.config, 'timeout', 60)
        )
    
    def _get_tokenizer(self):
        """Get tokenizer for the model."""
        try:
            # Map model names to tiktoken encodings
            if "gpt-4" in self.config.model:
                return tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in self.config.model:
                return tiktoken.encoding_for_model("gpt-3.5-turbo")
            else:
                return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return tiktoken.get_encoding("cl100k_base")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception:
            # Fallback estimation
            return int(len(text.split()) * 1.3)
    
    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> list:
        """Build message list for ChatOpenAI."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        return messages
    
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI."""
        try:
            messages = self._build_messages(prompt, system_prompt)
            
            # Update client parameters if provided
            if kwargs:
                client_kwargs = {
                    'temperature': kwargs.get('temperature', self.client.temperature),
                    'max_tokens': kwargs.get('max_tokens', self.client.max_tokens)
                }
                self.client = self.client.bind(**client_kwargs)
            
            response = self.client.invoke(messages)
            
            # Calculate tokens
            input_tokens = sum(self._count_tokens(msg.content) for msg in messages)
            output_tokens = self._count_tokens(response.content)
            total_tokens = input_tokens + output_tokens
            
            return LLMResponse(
                content=response.content,
                model=self.config.model,
                provider="openai",
                tokens_used=total_tokens,
                finish_reason="stop",
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.config.model
    
    def validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not hasattr(self.config, 'model') or not self.config.model:
            raise ValueError("Model name is required for OpenAI client")
        
        # Check if API key is available
        try:
            self._get_api_key()
        except ValueError as e:
            raise ValueError(f"Invalid OpenAI configuration: {str(e)}")
        
        self.logger.info(f"✅ OpenAI configuration validated for model: {self.config.model}")
