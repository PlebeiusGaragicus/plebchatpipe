from .VERSION import VERSION

from ..commands import CommandHandler as BaseCommandHandler

class CommandHandler(BaseCommandHandler):
    @classmethod
    def version(cls, args: list[str] = None):
        """Return the version of this graph."""
        return VERSION
        
    @classmethod
    def about(cls, args: list[str] = None):
        """Get information about the research agent."""
        return """
I am a research assistant powered by LangGraph that can search the web for information.

I use SearXNG to perform web searches and provide comprehensive answers with citations.

Try `/help` for a list of commands.

Here's my [source code on GitHub](https://github.com/PlebeiusGaragicus/plebchatpipe)
"""

    @classmethod
    def search(cls, args: list[str] = None):
        """Perform a web search on a specific topic.
        
        Usage: /search [query]
        Searches the web for information on the specified query and returns relevant results.
        """
        if not args or not args[0]:
            return "⚠️ Please provide a search query.\n\n**Example:**\n```\n/search latest AI developments\n```"
        
        # The actual search functionality is handled by the graph's search_web node
        # This command just provides an explicit way to trigger a search
        query = " ".join(args)
        return f"🔍 Searching for: {query}\n\nPlease wait while I retrieve information..."
