"""Nodes for the research agent graph."""

import json
import logging
from typing import Dict, Any, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama

from langgraph.types import StreamWriter

from ..config import Config
from ..common import write_content, write_thoughts
from .state import State, SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


############################################################################
# HELPER FUNCTIONS
############################################################################
def get_llm(config: RunnableConfig):
    """Get the LLM model based on the configuration."""
    configurable = Config.from_runnable_config(config)
    
    return ChatOllama(
        model=configurable.LLM_MODEL,
        keep_alive=configurable.KEEP_ALIVE,
        base_url=configurable.OLLAMA_BASE_URL
    )


def perform_web_search(query: str, searxng_url: str) -> tuple:
    """
    Perform a web search using SearXNG.
    
    Args:
        query (str): The search query
        searxng_url (str): The URL of the SearXNG instance
        
    Returns:
        tuple: (results, error_message) where results is a list of search results
               and error_message is an error message if any
    """
    import requests
    
    try:
        # Try with the exposed port if using the default container URL
        if searxng_url == "http://searxng:8080":
            searxng_url = "http://host.docker.internal:4001"
        
        # Prepare the search parameters
        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo",  # Specify engines explicitly
            "language": "en",
            "time_range": "",  # No time restriction
            "safesearch": 0  # No safe search filtering
        }
        
        # Make the request to SearXNG with a browser-like User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Log the request
        logger.info(f"Sending search request to {searxng_url}/search for query: {query}")
        
        # Make the request to SearXNG - try POST method as it's more reliable
        response = requests.post(
            f"{searxng_url}/search", 
            data=params,
            headers=headers,
            timeout=15  # Increased timeout for better reliability
        )
        
        # Check if the request was successful
        if response.status_code != 200:
            error_msg = f"SearXNG returned status code {response.status_code}: {response.text[:200]}"
            logger.error(error_msg)
            return [], error_msg
        
        # Parse the response
        try:
            data = response.json()
        except Exception as e:
            error_msg = f"Failed to parse JSON response: {str(e)}. Response: {response.text[:200]}"
            logger.error(error_msg)
            return [], error_msg
        
        # Extract and format the results
        results = []
        for result in data.get("results", [])[:10]:  # Limit to top 10 results
            results.append({
                "title": result.get("title", "No title"),
                "content": result.get("content", "No content"),
                "url": result.get("url", "No URL"),
                "score": result.get("score", 0)
            })
        
        if not results:
            logger.warning(f"SearXNG returned 0 results for query: {query}")
            return [], "No search results found for the query"
        
        logger.info(f"SearXNG returned {len(results)} results for query: {query}")
        return results, None
        
    except Exception as e:
        error_msg = f"Error in web search: {str(e)}"
        logger.error(error_msg)
        return [], error_msg


############################################################################
# NODES
############################################################################
def search_web(state: State, config: RunnableConfig, writer: StreamWriter):
    """
    Node to perform web search.
    
    Args:
        state (State): The current state
        config (RunnableConfig): The configuration
        writer (StreamWriter): The stream writer for streaming output
        
    Returns:
        dict: Updated state with search results
    """
    configurable = Config.from_runnable_config(config)
    
    # Extract the query
    query = state.query or state.messages[-1]['content']
    
    # Output to thoughts using StreamWriter
    writer(write_thoughts(f"🔍 Searching the web for: {query}"))
    
    # Get SearXNG URL from config
    searxng_url = configurable.SEARXNG_URL or "http://searxng:8080"
    
    # Perform the web search
    search_results, error = perform_web_search(query, searxng_url)
    
    if error:
        writer(write_thoughts(f"⚠️ Search error: {error}"))
        return {"error": error}
    
    if not search_results:
        writer(write_thoughts("No search results found. Please try a different query."))
        return {"search_results": [], "error": "No search results found"}
    
    # Format search results for display in thoughts
    result_summary = f"Found {len(search_results)} results:"
    writer(write_thoughts(result_summary))
    
    # Display each search result in thoughts
    for i, result in enumerate(search_results):
        title = result.get("title", "No title")
        url = result.get("url", "No URL")
        writer(write_thoughts(f"[{i+1}] {title} - {url}"))
    
    # Return the updated state with search results
    return {"search_results": search_results}


def generate_answer(state: State, config: RunnableConfig, writer: StreamWriter):
    """
    Node to generate an answer based on search results.
    
    Args:
        state (State): The current state
        config (RunnableConfig): The configuration
        writer (StreamWriter): The stream writer for streaming output
        
    Returns:
        dict: Updated state with the answer
    """
    # Check if we have search results
    if not state.search_results:
        return {"answer": "I couldn't find any search results to answer your question."}
    
    # Get the LLM
    llm = get_llm(config)
    
    # Format search results for the prompt
    formatted_results = ""
    for i, result in enumerate(state.search_results):
        title = result.get("title", "No title")
        content = result.get("content", "No content")
        url = result.get("url", "No URL")
        
        formatted_results += f"[{i+1}] {title}\n{content}\nSource: {url}\n\n"
    
    # Create system prompt
    system_prompt = SYSTEM_PROMPT
    
    # Create messages list for the chat
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history if available
    if state.conversation_history:
        # Add previous conversation messages
        messages.extend(state.conversation_history)
        
        # For a follow-up question, we need to provide context
        user_prompt = f"""Follow-up Question: {state.query}
        
Search Results:
{formatted_results}

Please provide a comprehensive answer to this follow-up question based on these search results.
Include citations to the relevant sources using the format [1], [2], etc.
Remember to consider the conversation history for context."""
    else:
        # Initial question
        user_prompt = f"""Question: {state.query}
        
Search Results:
{formatted_results}

Please provide a comprehensive answer to the question based on these search results.
Include citations to the relevant sources using the format [1], [2], etc."""
    
    # Add the current user query with search results
    messages.append({"role": "user", "content": user_prompt})
    
    # Inform the user that we're generating an answer
    writer(write_thoughts("🤔 Analyzing search results and generating an answer..."))
    
    try:
        # Call the LLM with streaming
        response = llm.stream(messages)
        

        full_response = "".join(chunk.content for chunk in response)

        # Add the assistant's response to the message history
        assistant_message = {"role": "assistant", "content": full_response}
        state.messages.append(assistant_message)

        print('='*40)
        print("GENERATE ANSWER SAID...")
        print(assistant_message)
        print('='*40)

        # Return the updated state with the answer
        return {"answer": [assistant_message]}
        
    except Exception as e:
        error_message = f"Error generating answer: {str(e)}"
        logger.error(error_message)
        writer(write_thoughts(f"⚠️ {error_message}"))
        return {"error": error_message}


def ollama(state: State, config: RunnableConfig):
    """
    Node to process messages with Ollama.
    This is a fallback node for direct interaction without search.
    
    Args:
        state (State): The current state
        config (RunnableConfig): The configuration
        
    Returns:
        dict: Updated state with the assistant's response
    """
    llm = get_llm(config)
    
    # If we have a new user query, add it to the messages
    if state.query:
        # Add the user's query to the message history
        user_message = {"role": "user", "content": state.query}
        # Ensure we're not duplicating the message if it's already in the state
        if not state.messages or state.messages[-1] != user_message:
            state.messages.append(user_message)
    
    # Add system prompt to messages if it's not already there
    if not state.messages or state.messages[0].get("role") != "system":
        # Prepend system prompt to messages
        state.messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state.messages
    
    # Call the LLM with the full conversation history
    response = llm.stream(state.messages)
    
    # Join all chunks into a single response
    full_response = "".join(chunk.content for chunk in response)
    
    # Add the assistant's response to the message history
    assistant_message = {"role": "assistant", "content": full_response}
    state.messages.append(assistant_message)
    
    # Return the updated messages list with the new response
    return {"messages": [assistant_message]}
