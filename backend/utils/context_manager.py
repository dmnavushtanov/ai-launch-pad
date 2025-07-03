# backend/utils/context_manager.py
# This file contains the context management system using LangChain memory components for conversation and task context
# Purpose: Manage, store, retrieve, and compress conversation context between agents and users with relevance scoring. This is NOT for configuration management or direct LLM communication.

"""
Context management using LangChain memory components.
"""
import threading
from typing import Dict, Any, Optional, List
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryBufferMemory,
    ConversationBufferWindowMemory
)
from langchain.schema import BaseMessage
from langchain_core.messages import HumanMessage, AIMessage

from ..llm_clients.base_llm_client import BaseClient
from .logger import get_logger


class ContextManager:
    """Manages context using LangChain memory components."""
    
    def __init__(self, llm_client: Optional[BaseClient] = None):
        self.logger = get_logger("context_manager")
        self.llm_client = llm_client
        self._lock = threading.RLock()
        
        # Different memory types for different contexts
        self._memories: Dict[str, Any] = {
            "conversation": ConversationBufferMemory(return_messages=True),
            "task": ConversationBufferMemory(return_messages=True),
            "agent": ConversationBufferMemory(return_messages=True)
        }
        
        # Summary memories for compression
        self._summary_memories: Dict[str, Any] = {}
        
    def store_context(self, context_type: str, human_input: str, ai_output: str) -> None:
        """
        Store context in the appropriate memory.
        
        Args:
            context_type: Type of context ('conversation', 'task', 'agent')
            human_input: Human/user input
            ai_output: AI/agent output
        """
        with self._lock:
            if context_type not in self._memories:
                self._memories[context_type] = ConversationBufferMemory(return_messages=True)
            
            memory = self._memories[context_type]
            memory.save_context({"input": human_input}, {"output": ai_output})
            self.logger.debug(f"💾 Stored {context_type} context")
    
    def retrieve_context(self, context_type: str, last_k: Optional[int] = None) -> List[BaseMessage]:
        """
        Retrieve context from memory.
        
        Args:
            context_type: Type of context
            last_k: Number of recent messages to retrieve (None for all)
            
        Returns:
            List of messages
        """
        with self._lock:
            if context_type not in self._memories:
                return []
            
            memory = self._memories[context_type]
            messages = memory.chat_memory.messages
            
            if last_k:
                return messages[-last_k:]
            return messages
    
    def update_context(self, context_type: str, message_index: int, new_content: str) -> None:
        """
        Update a specific message in context.
        
        Args:
            context_type: Type of context
            message_index: Index of message to update
            new_content: New content for the message
        """
        with self._lock:
            if context_type not in self._memories:
                raise ValueError(f"Context type '{context_type}' not found")
            
            memory = self._memories[context_type]
            messages = memory.chat_memory.messages
            
            if 0 <= message_index < len(messages):
                # Preserve message type
                if isinstance(messages[message_index], HumanMessage):
                    messages[message_index] = HumanMessage(content=new_content)
                else:
                    messages[message_index] = AIMessage(content=new_content)
                self.logger.debug(f"✏️ Updated message at index {message_index}")
            else:
                raise IndexError(f"Message index {message_index} out of range")
    
    def compress_context(self, context_type: str, max_token_limit: int = 2000) -> None:
        """
        Compress context using LangChain's summary memory.
        
        Args:
            context_type: Type of context to compress
            max_token_limit: Maximum tokens to keep
        """
        if not self.llm_client:
            raise ValueError("LLM client required for context compression")
        
        with self._lock:
            if context_type not in self._memories:
                return
            
            # Create summary memory if not exists
            if context_type not in self._summary_memories:
                self._summary_memories[context_type] = ConversationSummaryBufferMemory(
                    llm=self.llm_client.client,
                    max_token_limit=max_token_limit,
                    return_messages=True
                )
            
            # Transfer messages to summary memory
            summary_memory = self._summary_memories[context_type]
            original_messages = self._memories[context_type].chat_memory.messages
            
            for msg in original_messages:
                if isinstance(msg, HumanMessage):
                    summary_memory.save_context({"input": msg.content}, {"output": ""})
                elif isinstance(msg, AIMessage) and msg.content:
                    # Update last context with AI message
                    contexts = summary_memory.buffer
                    if contexts:
                        summary_memory.save_context({"input": contexts[-1]}, {"output": msg.content})
            
            # Replace original memory with compressed
            self._memories[context_type] = summary_memory
            self.logger.info(f"🗜️ Compressed {context_type} context to {max_token_limit} tokens")
    
    
    def clear_context(self, context_type: Optional[str] = None) -> None:
        """
        Clear context memory.
        
        Args:
            context_type: Specific type to clear (None for all)
        """
        with self._lock:
            if context_type:
                if context_type in self._memories:
                    self._memories[context_type].clear()
                    self.logger.info(f"🧹 Cleared {context_type} context")
            else:
                for memory in self._memories.values():
                    memory.clear()
                self._summary_memories.clear()
                self.logger.info("🧹 Cleared all contexts")
    
    def get_context_window(self, context_type: str, window_size: int = 10) -> ConversationBufferWindowMemory:
        """
        Get a windowed view of context.
        
        Args:
            context_type: Type of context
            window_size: Number of recent interactions
            
        Returns:
            Window memory with recent messages
        """
        with self._lock:
            window_memory = ConversationBufferWindowMemory(
                k=window_size,
                return_messages=True
            )
            
            # Copy recent messages to window
            messages = self.retrieve_context(context_type, last_k=window_size * 2)
            for i in range(0, len(messages) - 1, 2):
                if i + 1 < len(messages):
                    window_memory.save_context(
                        {"input": messages[i].content},
                        {"output": messages[i + 1].content}
                    )
            
            return window_memory 