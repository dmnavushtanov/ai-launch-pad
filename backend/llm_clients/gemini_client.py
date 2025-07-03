# backend/llm_clients/gemini_client.py
# This file contains the Google Gemini client implementation using langchain-google-genai for LLM communication
# Purpose: Handle Google Gemini API interactions, token estimation, and response formatting with proper error handling. This is NOT for other LLM providers or configuration management.

"""
Google Gemini client implementation using langchain-google-genai.
"""
import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from .base_llm_client import BaseClient, LLMResponse
from ..utils.config_loader import LLMConfig


class GeminiClient(BaseClient):
    """Google Gemini client using langchain-google-genai ChatGoogleGenerativeAI."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = self._get_api_key()
        self.client = self._create_client()
    
    def _get_api_key(self) -> str:
        """Get Google API key from config or environment."""
        api_key = getattr(self.config, 'api_key', None) or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found in config or GOOGLE_API_KEY environment variable")
        return api_key
    
    def _create_client(self) -> ChatGoogleGenerativeAI:
        """Create ChatGoogleGenerativeAI client."""
        return ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.config.model,
            temperature=getattr(self.config, 'temperature', 0.7),
            max_tokens=getattr(self.config, 'max_tokens', None),
            timeout=getattr(self.config, 'timeout', 60)
        )
    
    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> list:
        """Build message list for ChatGoogleGenerativeAI."""
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        return messages
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Simple estimation: ~1.3 tokens per word for Gemini
        return int(len(text.split()) * 1.3)
    
    def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Google Gemini."""
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
            
            # Estimate tokens (Gemini doesn't provide exact counts in LangChain)
            input_text = system_prompt + " " + prompt if system_prompt else prompt
            input_tokens = self._estimate_tokens(input_text)
            output_tokens = self._estimate_tokens(response.content)
            total_tokens = input_tokens + output_tokens
            
            return LLMResponse(
                content=response.content,
                model=self.config.model,
                provider="gemini",
                tokens_used=total_tokens,
                finish_reason="stop",
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            
        except Exception as e:
            self.logger.error(f"Google Gemini API error: {str(e)}")
            raise
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.config.model
    
    def validate_config(self) -> None:
        """Validate Google Gemini configuration."""
        if not hasattr(self.config, 'model') or not self.config.model:
            raise ValueError("Model name is required for Gemini client")
        
        # Check if API key is available
        try:
            self._get_api_key()
        except ValueError as e:
            raise ValueError(f"Invalid Gemini configuration: {str(e)}")
        
        self.logger.info(f"✅ Gemini configuration validated for model: {self.config.model}") 