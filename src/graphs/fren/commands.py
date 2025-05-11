import os
import json

import logging
logger = logging.getLogger(__name__)

from .VERSION import VERSION


class CommandHandler:
    @classmethod
    def _run(cls, command: str, arguments: list[str]):
        """Handle a command and its arguments.

        Args:
            command: The command name without the leading slash
            arguments: String arguments for the command
        """
        # Try to get the method corresponding to the command
        method = getattr(cls, command, None)

        # If method exists and is callable, invoke it
        if callable(method) and not command.startswith('_'):
            return method(arguments)
        else:
            # return f"""# ⛓️‍💥\n`/{command}` command not found!\n## Commands available:\n{cls.help()}"""
            return f"""# ⛓️‍💥\n{cls.help()}"""

####################################################################################
    @classmethod
    def help(cls, args: list[str] = None):
        """Get a list of commands.
        
        Usage: /help [command]
        Without arguments, shows a list of all available commands with brief descriptions.
        With a command name, shows detailed help for that specific command.
        """
        # Check if help was requested for a specific command
        if args and len(args) > 0:
            command = args[0].lower()
            # Check if the command exists
            if hasattr(cls, command) and callable(getattr(cls, command)) and not command.startswith("_"):
                method = getattr(cls, command)
                doc = method.__doc__ or "No description available."
                return f"""## Help: /{command}

```
{doc}
```

Type `/help` to see all available commands.
"""
            else:
                return f"Command '/{command}' not found. Type `/help` to see all available commands."
        
        # Generate usage text from available methods
        command_list = [
            method for method in dir(cls)
            if callable(getattr(cls, method)) and not method.startswith("_")
        ]
        # Only show admin commands to admins
        command_list = [cmd for cmd in command_list if not cmd.endswith("_")]

        # Format as markdown with clear sections
        command_docs = []
        for cmd in sorted(command_list):
            doc = getattr(cls, cmd).__doc__ or "No description available."
            # Get only the first line of the docstring
            first_line = doc.strip().split('\n')[0]
            command_docs.append(f"- `/{cmd}` - {first_line}")

        return f"""### Commands Available

{chr(10).join(command_docs)}

For detailed help on a specific command, type `/help command_name`
"""



####################################################################################
    @classmethod
    def cuss(cls, args: list[str] = None):
        """Let off some steam... 😡"""
        return "fuck\n\nteehee"

####################################################################################
    @classmethod
    def version(cls, args: list[str] = None):
        """Return the version of this graph."""
        return VERSION

####################################################################################
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

####################################################################################
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


####################################################################################
# KEEP THIS
    # def usage(self, request, *args):
    #     """Track your **token usage** for this conversation."""

    #     is_admin = request.body['user']['role'] == 'admin'
    #     if is_admin:
    #         return "You're a system administrator - I don't track your usage!\nYou can use me for free!"

    #     lud16 = request.body['user']['email']
    #     if not lud16:
    #         return "⚠️ No user LUD16 provided."

    #     thread_id = request.body['chat_id']
    #     if not thread_id:
    #         return "⚠️ No thread ID provided."

    #     try:
    #         from .payment import get_usage
    #         usage = get_usage(lud16, thread_id)
    #         return f"User: `{lud16}`\nThread: `{thread_id}`\nYou have used: **`{0 if not usage else usage}`** generation tokens in this conversation."
    #     except Exception as e:
    #         return f"Error checking usage: {e}"

####################################################################################
    @classmethod
    def url(cls, args: list[str] = None):
        """Extract and display the main content from a website URL.

        Usage: /url [https://example.com]
        Scrapes the content from the provided URL and displays it in the chat.
        This allows you to discuss, summarize, or analyze web content directly.

        The URL must start with https:// for security reasons.
        """
        import requests
        from readability import Document
        import html2text

        # Check if URL was provided
        if not args or len(args) == 0:
            return "⚠️ Please provide a URL.\n\n**Example:**\n```\n/url https://example.com\n```"

        # Get the first argument as the URL
        url = args[0]

        # Check if URL uses HTTP instead of HTTPS
        if url.startswith("http://"):
            return f"⚠️ The URL must start with `https://`\n\n**Example:**\n```\n/url https://example.com\n```"

        # Add https:// prefix if missing
        if not url.startswith("https://"):
            url = f"https://{url}"

        try:
            # Fetch the webpage content
            print(f"Fetching content from: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Decode the content - handle encoding issues
            try:
                # Try to get the encoding from the response
                content = response.content.decode(response.encoding or 'utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1 which rarely fails
                content = response.content.decode('latin-1')

            # Parse the content with readability
            doc = Document(content)
            title = doc.title()
            summary = doc.summary()

            # Convert HTML to markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = False
            h.body_width = 0  # No wrapping
            markdown_content = h.handle(summary)

            # Prepare the output
            result = f"# {title}\n\n"
            result += f"*Source: [{url}]({url})*\n\n"
            result += "---\n\n"
            result += markdown_content

            # Truncate if too long
            if len(result) > 30_000:
                result = result[:30_000] + "\n\n... *Content truncated due to length* ..."

            return result

        except requests.exceptions.RequestException as e:
            return f"⚠️ Error fetching the URL: {str(e)}"
        except Exception as e:
            return f"⚠️ Error processing the webpage content: {str(e)}"


# def url(request):
#     split = request.user_message.split(" ")
#     first_arg = split[1] if len(split) > 1 else None

#     if not first_arg:
#         return "⚠️ Please provide a URL.\n\n**Example:**\n```\n/url https://example.com\n```"

#     if first_arg.startswith("http://"):
#         return f"⚠️ The URL must start with `https://`\n\n**Example:**\n```\n/url https://example.com\n```"

#     if not first_arg.startswith("https://"):
#         first_arg = f"https://{first_arg}"

#     return f"""
# This command will scrape the provided url and reply with the "readability" text.

# This way, the contents of the url can be injected into the context of the conversation and can be discussed, summariezed, etc.

# This is a placeholder for the implementation of the url command.

# The URL you provided is: {first_arg}
# """




# [Click here to view the content of the URL]({first_arg})
# The content of the URL will be displayed here.
# #NOTE: providing just the url link like so:
# # [Click here to view the content of the URL]({first_arg})
# # will prepend the base url/c/ so that we can link TO CONVERSATIONS!!! WOW!



####################################################################################
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


# THIS method gives you the number of digits that you ask for
    # @classmethod
    # def random(cls, args: list[str] = None):
    #     """Generate a random number.
        
    #     Usage: /random [digits]
    #     If no digits are provided, returns a random number between 1-100.
    #     If digits are provided, returns a random number with that many digits.
    #     """
    #     import random
        
    #     # Debug output
    #     print("&"*30)
    #     print(f"DEBUG random command received args: {args}")

    #     # Handle None or empty list
    #     if args is None or not args:
    #         # Default behavior: random number between 1-100
    #         random_number = random.randint(1, 100)
    #         return f"Random number (1-100): {random_number}"

    #     # Handle case with arguments
    #     try:
    #         digits = int(args[0])
    #         if digits <= 0:
    #             return "Please provide a positive number of digits."
    #         if digits > 10:
    #             return "For performance reasons, please limit to 10 digits or fewer."

    #         min_val = 10**(digits-1) if digits > 1 else 1
    #         max_val = (10**digits) - 1
    #         random_number = random.randint(min_val, max_val)
    #         return f"Random {digits}-digit number: {random_number}"
    #     except (ValueError, IndexError):
    #         return "Invalid input. Usage: /random [digits] - where digits is a positive integer."

####################################################################################
    @classmethod
    def read(cls, args: list[str] = None):
        return "Not yet implemented"
#     # TODO: I want to consider charging the user for intensive commands like this...
#     split = request.user_message.split(" ")
#     first_arg = split[1] if len(split) > 1 else None

#     #TODO: modularize this code.  Maybe have a _ensure_proper_url() function that can be reused in other commands.
#     if not first_arg:
#         return "⚠️ Please provide a URL.\n\n**Example:**\n```\n/article https://example.com\n```"

#     if first_arg.startswith("http://"):
#         return f"⚠️ The URL must start with `https://`\n\n**Example:**\n```\n/article https://example.com\n```"

#     if not first_arg.startswith("https://"):
#         first_arg = f"https://{first_arg}"

#     try:
#         from readability import Document
#         # url = "https://tftc.io/home-and-car-insurance-providers-retreating/"
#         # response = requests.get( url )
#         response = requests.get( first_arg )
#         doc = Document(response.content)

#         article_markdown_contents = f""

#         article_markdown_contents += doc.title()
#         article_markdown_contents += doc.summary()
#         article_markdown_contents += doc.content()



#         return f"""
# This command will scrape the provided url and reply with a summary of the content.

# The URL you provided is: {first_arg}

# Here's the article:

# ---

# {article_markdown_contents}
# """

#     except Exception as e:
#         return f"""error in scraping this URL: {e}"""