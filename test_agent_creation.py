#!/usr/bin/env python3
"""
Test script to diagnose agent creation issues.
Run this to see detailed error messages about why agents might be failing to initialize.
"""

import sys
from pathlib import Path

# Ensure backend modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from backend.utils.logger import setup_logging, get_logger
from backend.utils.config_loader import get_config
from backend.llm_clients.llm_factory import LLMFactory
from backend.agents.task_agent_1 import CalculatorAgent
from backend.agents.task_agent_2 import TaskAgent2

def test_agent_creation():
    """Test creating each agent individually to identify issues."""
    
    print("=" * 60)
    print("Agent Creation Test")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    logger = get_logger("test")
    
    # Load config
    print("\n1. Loading configuration...")
    try:
        config = get_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return
    
    # Create LLM factory
    print("\n2. Creating LLM factory...")
    try:
        llm_factory = LLMFactory()
        print("✅ LLM factory created")
    except Exception as e:
        print(f"❌ Failed to create LLM factory: {e}")
        return
    
    # Create LLM client
    print("\n3. Creating LLM client...")
    try:
        llm_config = config.llm_clients.get("openai")
        if not llm_config:
            print("❌ OpenAI config not found")
            return
            
        llm_client = llm_factory.create_client(llm_config)
        print("✅ LLM client created")
        print(f"   Client type: {type(llm_client)}")
        print(f"   Has 'client' attribute: {hasattr(llm_client, 'client')}")
    except Exception as e:
        print(f"❌ Failed to create LLM client: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test CalculatorAgent (task_agent_1)
    print("\n4. Testing CalculatorAgent (task_agent_1)...")
    try:
        agent1 = CalculatorAgent(llm_client=llm_client)
        print("✅ CalculatorAgent created successfully!")
        print(f"   Name: {agent1.name}")
        print(f"   Description: {agent1.description}")
        print(f"   Tools: {[tool.name for tool in agent1.tools]}")
    except ImportError as e:
        print(f"❌ ImportError creating CalculatorAgent: {e}")
        print("   This suggests missing dependencies.")
        print("   Please run: pip install langchain langchain-community")
    except Exception as e:
        print(f"❌ Failed to create CalculatorAgent: {e}")
        import traceback
        traceback.print_exc()
    
    # Test TaskAgent2
    print("\n5. Testing TaskAgent2...")
    try:
        agent2 = TaskAgent2(llm_client=llm_client)
        print("✅ TaskAgent2 created successfully!")
        print(f"   Name: {agent2.name}")
        print(f"   Description: {agent2.description}")
        print(f"   Tools: {[tool.name for tool in agent2.tools] if agent2.tools else 'None'}")
    except Exception as e:
        print(f"❌ Failed to create TaskAgent2: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test complete. Check the output above for any errors.")
    print("=" * 60)

if __name__ == "__main__":
    test_agent_creation() 