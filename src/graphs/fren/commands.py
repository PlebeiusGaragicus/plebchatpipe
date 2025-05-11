from .VERSION import VERSION

from ..commands import CommandHandler as BaseCommandHandler

class CommandHandler(BaseCommandHandler):
    # This class inherits all methods from BaseCommandHandler
    # We only need to define methods that are specific to this graph or that override base methods
    
    @classmethod
    def version(cls, args: list[str] = None):
        """Return the version of this graph."""
        return VERSION

    @classmethod
    def about(cls, args: list[str] = None):
        """Get information about the agent."""
        return """
I am proof of concept LangGraph agent that accepts direct bitcoin payments from users.

I aim to be a useful assistant that anyone can use anonymously.

There's a lot I can do with more features being added all the time!

Try `/help` for a list of commands.

Here's my [source code on GitHub](https://github.com/PlebeiusGaragicus/plebchatpipe)

Send me a message on nostr to chat about issues, features you'd like to see or anything AI-related.

Find me on [nostr](https://njump.me/npub1xegedgkkjf24pl4d76cdwhufacng5hapzjnrtgms3pyhlvmyqj9suym08k): `npub1xegedgkkjf24pl4d76cdwhufacng5hapzjnrtgms3pyhlvmyqj9suym08k`
"""

    @classmethod
    def cuss(cls, args: list[str] = None):
        """Let off some steam... 😡"""
        return "fuck\n\nteehee"

    @classmethod
    def hi(cls, args: list[str] = None):
        """Tell the bot to say hello to you."""
        return f"""👋 Hi there!

You must be the `pleb` I've heard so much about...

I'm `Ollama`.  I'm just a simple chatbot agent.

Type `/about` to learn more.

Type `/help` to see a list of commands.

Or, just start asking questions!  I'm here to help.
"""

    @classmethod
    def random(cls, args: list[str] = None):
        """Generate a random number.
        
        Usage: /random [max]
        If no maximum is provided, returns a random number between 1-100.
        If maximum is provided, returns a random number between 1 and that maximum.
        """
        import random
        
        # Debug output
        print("&"*30)
        print(f"DEBUG random command received args: {args}")

        # Handle None or empty list
        if args is None or not args:
            # Default behavior: random number between 1-100
            random_number = random.randint(1, 100)
            return f"Random number (1-100): {random_number}"

        # Handle case with arguments
        try:
            max_value = int(args[0])
            if max_value <= 0:
                return "Please provide a positive maximum value."
            if max_value > 1_000_000_000:
                return "For performance reasons, please limit to 1 billion or less."

            random_number = random.randint(1, max_value)
            return f"Random number (1-{max_value}): {random_number}"
        except (ValueError, IndexError):
            return "Invalid input. Usage: /random [max] - where max is a positive integer."
