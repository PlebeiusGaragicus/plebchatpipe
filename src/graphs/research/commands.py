from .VERSION import VERSION

from ..commands import CommandHandler as BaseCommandHandler, CommandOutput

class CommandHandler(BaseCommandHandler):
    @classmethod
    def version(cls, args: list[str] = None):
        """Return the version of this graph."""
        return CommandOutput(cmdOutput=VERSION)

    @classmethod
    def about(cls, args: list[str] = None):
        """Get information about the research agent."""
        about_text = """
Hi, I'm Abby, an AI research assistant.

I was created to be your personal, open-source, self-hosted, internet-research companion.  I can search the web for information and answer your questions about what we find.

I ampowered by LangGraph and Ollama, and written for an Open WebUI front-end.

I use SearXNG to perform web searches and provide comprehensive answers with citations.

Try `/help` for a list of commands.

Here's my [source code on GitHub](https://github.com/PlebeiusGaragicus/plebchatpipe)
"""
        return CommandOutput(cmdOutput=about_text)
        
    @classmethod
    def summarize(cls, args: list[str] = None):
        """Extract and summarize the main content from a website URL.

        Usage: /summarize https://example.com
        Scrapes the content from the provided URL and generates a concise summary.
        This allows you to quickly understand the key points from web content.
        """
        # Get the URL content using the base url command
        url_result = BaseCommandHandler.url(args)

        # Create a reinjection prompt for summarization
        reinjection_prompt = f"""
You are a helpful AI assistant that summarizes web content.

Please provide a concise summary that includes:
1. The main topic or purpose of the page
2. Key points and important information
3. Any relevant conclusions or takeaways

Format your response in a clear, well-structured way using markdown formatting.
"""

        return CommandOutput(
            cmdOutput=url_result.cmdOutput,
            returnDirect=False,  # Process through LLM
            reinjectionPrompt=reinjection_prompt
        )
