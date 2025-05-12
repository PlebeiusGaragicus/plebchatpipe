"""State definition for the research agent graph."""

import operator
from typing import Optional, Annotated, List, Dict, Any
from pydantic import BaseModel, Field


############################################################################
# PROMPTS
############################################################################
SYSTEM_PROMPT = """You are a helpful research assistant that provides comprehensive answers based on web search results.

Your goal is to:
1. Analyze search results thoroughly
2. Provide accurate, well-structured responses
3. Include relevant citations to sources using the format [1], [2], etc.
4. Be objective and factual in your analysis

Always base your answers solely on the provided search results. If the search results don't contain enough information to answer the question, say so clearly.
"""


############################################################################
# STATE
############################################################################
class State(BaseModel):
    """State for the research agent graph."""
    query: Optional[str] = None
    messages: Annotated[list, operator.add] = Field(default_factory=list)
    search_results: List[Dict[str, Any]] = Field(default_factory=list, description="Results from search engine")
    answer: Optional[str] = Field(default=None, description="The final answer to return to the user")
    error: Optional[str] = Field(default=None, description="Error message if any")
    conversation_id: Optional[int] = Field(default=None, description="The conversation ID")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Previous conversation history")
