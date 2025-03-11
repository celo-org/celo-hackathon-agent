"""
Coordinator agent for orchestrating the entire analysis pipeline.

This file provides API compatibility with the new orchestrator.py module.
"""

from src.agents.orchestrator import AnalysisOrchestrator as AnalysisPipeline

# For backward compatibility
def create_coordinator_agent(*args, **kwargs):
    """
    Legacy function for creating a coordinator agent.
    
    This is maintained for backward compatibility.
    Use AnalysisOrchestrator from orchestrator.py instead.
    """
    from warnings import warn
    warn("create_coordinator_agent is deprecated. Use AnalysisOrchestrator instead.", 
         DeprecationWarning, stacklevel=2)
    return None