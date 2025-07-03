# backend/workflows/__init__.py
# Export workflow classes for easy import
# Purpose: Provide convenient access to workflow implementations

from .base_workflow import BaseWorkflow, WorkflowState
from .sequential_workflow import SequentialWorkflow

__all__ = [
    "BaseWorkflow",
    "WorkflowState", 
    "SequentialWorkflow"
] 