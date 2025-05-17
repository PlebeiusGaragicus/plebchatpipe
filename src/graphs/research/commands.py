from .VERSION import VERSION

from ..commands import CommandHandler as BaseCommandHandler, CommandOutput
from typing import Callable, Any
from ..utils.event_emitter import EventEmitter

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
