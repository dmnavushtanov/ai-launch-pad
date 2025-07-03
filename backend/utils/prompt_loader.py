# backend/utils/prompt_loader.py
# This file contains the prompt loading and management utility for dynamic prompt template handling
# Purpose: Load, cache, validate, and format prompt templates from classes and files with dynamic modification support. This is NOT for LLM communication or configuration management.

"""
Prompt loading and management utility.
"""
import re
from typing import Dict, Any, Optional
from pathlib import Path
import importlib
import inspect

from .logger import get_logger


class PromptLoader:
    """Load and manage prompt templates."""
    
    def __init__(self):
        self.logger = get_logger("prompt_loader")
        self._cache: Dict[str, str] = {}
        self._modified_prompts: Dict[str, str] = {}
    
    def load_from_class(self, module_path: str, class_name: str) -> Dict[str, str]:
        """
        Load prompts from a class.
        
        Args:
            module_path: Module path (e.g., 'backend.prompts.router_prompts')
            class_name: Class name (e.g., 'RouterPrompts')
            
        Returns:
            Dictionary of prompt_name: prompt_template
        """
        try:
            module = importlib.import_module(module_path)
            prompt_class = getattr(module, class_name)
            
            # Get all string attributes (prompts)
            prompts = {}
            for name, value in inspect.getmembers(prompt_class):
                if isinstance(value, str) and name.isupper():
                    cache_key = f"{module_path}.{class_name}.{name}"
                    self._cache[cache_key] = value
                    prompts[name] = value
            
            self.logger.info(f"✅ Loaded {len(prompts)} prompts from {class_name}")
            return prompts
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load prompts from {module_path}.{class_name}: {str(e)}")
            raise
    
    def load_from_file(self, file_path: str) -> str:
        """
        Load a prompt from a text file.
        
        Args:
            file_path: Path to the prompt file
            
        Returns:
            Prompt content
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Prompt file not found: {file_path}")
            
            content = path.read_text(encoding='utf-8')
            self._cache[file_path] = content
            self.logger.info(f"✅ Loaded prompt from {file_path}")
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load prompt from {file_path}: {str(e)}")
            raise
    
    def get_prompt(self, key: str) -> str:
        """
        Get a prompt by key (from cache or modified).
        
        Args:
            key: Prompt key
            
        Returns:
            Prompt template
        """
        # Check modified prompts first
        if key in self._modified_prompts:
            return self._modified_prompts[key]
        
        # Then check cache
        if key in self._cache:
            return self._cache[key]
        
        raise KeyError(f"Prompt not found: {key}")
    
    def format_prompt(self, template: str, **variables) -> str:
        """
        Format a prompt template with variables.
        
        Args:
            template: Prompt template
            **variables: Template variables
            
        Returns:
            Formatted prompt
        """
        try:
            return template.format(**variables)
        except KeyError as e:
            self.logger.error(f"❌ Missing template variable: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Failed to format prompt: {str(e)}")
            raise
    
    def validate_template(self, template: str) -> Dict[str, Any]:
        """
        Validate a prompt template.
        
        Args:
            template: Prompt template to validate
            
        Returns:
            Validation results with placeholders found
        """
        # Find all placeholders
        placeholder_pattern = r'\{(\w+)\}'
        placeholders = re.findall(placeholder_pattern, template)
        
        # Check for invalid syntax
        try:
            # Test format with dummy values
            test_vars = {p: "test" for p in placeholders}
            template.format(**test_vars)
            valid = True
            error = None
        except Exception as e:
            valid = False
            error = str(e)
        
        return {
            "valid": valid,
            "placeholders": list(set(placeholders)),
            "error": error
        }
    
    def modify_prompt(self, key: str, new_template: str) -> None:
        """
        Dynamically modify a prompt.
        
        Args:
            key: Prompt key
            new_template: New template content
        """
        # Validate before modifying
        validation = self.validate_template(new_template)
        if not validation["valid"]:
            raise ValueError(f"Invalid template: {validation['error']}")
        
        self._modified_prompts[key] = new_template
        self.logger.info(f"✅ Modified prompt: {key}")
    
    def reset_prompt(self, key: str) -> None:
        """Reset a modified prompt to original."""
        if key in self._modified_prompts:
            del self._modified_prompts[key]
            self.logger.info(f"✅ Reset prompt: {key}")
    
    def clear_cache(self) -> None:
        """Clear all cached prompts."""
        self._cache.clear()
        self._modified_prompts.clear()
        self.logger.info("🧹 Cleared prompt cache")
    
    def list_cached_prompts(self) -> Dict[str, str]:
        """List all cached prompt keys."""
        return {
            "cached": list(self._cache.keys()),
            "modified": list(self._modified_prompts.keys())
        } 