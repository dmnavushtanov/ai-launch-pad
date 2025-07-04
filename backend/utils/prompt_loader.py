# backend/utils/prompt_loader.py
# This file handles loading and managing prompt templates from YAML files
# Purpose: Load prompt templates from YAML files for agent use. This is NOT for agent implementation or direct prompt usage.

"""
Prompt template loader utility - loads prompts from YAML files.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from langchain_core.prompts import PromptTemplate


class PromptLoader:
    """Loads and manages prompt templates from YAML files."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing YAML prompt files
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def load_prompts(self, filename: str) -> Dict[str, Any]:
        """
        Load prompts from a YAML file.
        
        Args:
            filename: Name of the YAML file (without .yml extension)
            
        Returns:
            Dictionary of prompt templates
        """
        # Check cache first
        if filename in self._cache:
            return self._cache[filename]
        
        # Load from file
        filepath = self.prompts_dir / f"{filename}.yml"
        if not filepath.exists():
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
        
        # Cache the loaded prompts
        self._cache[filename] = prompts
        return prompts
    
    def get_prompt(self, filename: str, prompt_name: str) -> str:
        """
        Get a specific prompt by name.
        
        Args:
            filename: YAML file name (without extension)
            prompt_name: Name of the prompt in the file
            
        Returns:
            Prompt template string
        """
        prompts = self.load_prompts(filename)
        if prompt_name not in prompts:
            raise KeyError(f"Prompt '{prompt_name}' not found in {filename}.yml")
        return prompts[prompt_name]
    
    def get_prompt_template(self, filename: str, prompt_name: str) -> PromptTemplate:
        """
        Get a LangChain PromptTemplate object.
        
        Args:
            filename: YAML file name (without extension)
            prompt_name: Name of the prompt in the file
            
        Returns:
            LangChain PromptTemplate object
        """
        prompt_str = self.get_prompt(filename, prompt_name)
        return PromptTemplate.from_template(prompt_str)
    
    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()


# Global instance for convenience
prompt_loader = PromptLoader() 