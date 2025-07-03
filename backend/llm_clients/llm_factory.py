"""
LLM client factory for creating and managing LLM client instances.
"""
from typing import Dict, Type
from .base_llm_client import BaseClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from ..utils.config_loader import LLMConfig
from ..utils.logger import get_logger


class LLMFactory:
    """Factory for creating and caching LLM client instances."""
    
    # Provider mapping
    _providers: Dict[str, Type[BaseClient]] = {
        "openai": OpenAIClient,
        "gemini": GeminiClient,
        # "anthropic": AnthropicClient,  # Uncomment when implemented
    }
    
    # Client cache
    _clients: Dict[str, BaseClient] = {}
    
    def __init__(self):
        self.logger = get_logger("llm_factory")
    
    def create_client(self, config: LLMConfig) -> BaseClient:
        """
        Create or retrieve cached LLM client based on configuration.
        
        Args:
            config: LLM configuration object
            
        Returns:
            BaseClient instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = config.provider.lower()
        
        # Validate provider
        if provider not in self._providers:
            supported = ", ".join(self._providers.keys())
            raise ValueError(f"Unsupported provider: '{provider}'. Supported: {supported}")
        
        # Check cache
        cache_key = f"{provider}:{config.model}"
        if cache_key in self._clients:
            self.logger.debug(f"🔄 Returning cached client for {cache_key}")
            return self._clients[cache_key]
        
        # Create new client
        try:
            client_class = self._providers[provider]
            client = client_class(config)
            
            # Cache the client
            self._clients[cache_key] = client
            self.logger.info(f"✅ Created new {provider} client for model {config.model}")
            
            return client
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create {provider} client: {str(e)}")
            raise
    
    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return list(self._providers.keys())
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available."""
        return provider.lower() in self._providers
    
    def clear_cache(self) -> None:
        """Clear all cached clients."""
        self._clients.clear()
        self.logger.info("🧹 Cleared client cache")
    
    def get_cached_client(self, provider: str, model: str) -> BaseClient | None:
        """Get cached client if exists."""
        cache_key = f"{provider.lower()}:{model}"
        return self._clients.get(cache_key)
