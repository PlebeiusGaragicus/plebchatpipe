class CommandOutput:
    def __init__(self,
            cmdOutput: str,
            returnDirect: bool = True,
            reinjectionPrompt: str = None
        ):
        """
        Container for command output with options for how to process it.
        
        Args:
            cmdOutput: The output text of the command
            returnDirect: If True, return the output directly to the user without LLM processing
            reinjectionPrompt: If provided, this prompt will be used when reinjecting the output to an LLM
        """
        self.cmdOutput = cmdOutput  # The output of the command
        self.returnDirect = returnDirect  # Return directly to user or reinject to LLM?
        self.reinjectionPrompt = reinjectionPrompt  # Prompt to use when reinjecting



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

        # commands starting in '_' can't be called (like this one, '_run()')
        if callable(method) and not command.startswith('_'):
            # If method exists and is callable, invoke it
            return method(arguments)
        else:
            # Get the help command output
            help_output = cls.help()
            help_text = help_output.cmdOutput
            return CommandOutput(cmdOutput=f"""# ⛓️‍💥\n{help_text}""")


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
                output = f"""## Help: /{command}

```
{doc}
```
"""
                return CommandOutput(cmdOutput=output)
            else:
                output = f"Command '/{command}' not found. Type `/help` to see all available commands."
                return CommandOutput(cmdOutput=output)
        
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

        output = f"""### Commands Available

{chr(10).join(command_docs)}

For detailed help on a specific command, type `/help command_name`
"""
        return CommandOutput(cmdOutput=output)


####################################################################################
    @classmethod
    def version(cls, args: list[str] = None):
        """Return the version of this graph."""
        raise NotImplementedError("Each graph must implement its own version method")
        # Implementation should return CommandOutput like:
        # return CommandOutput(cmdOutput="v1.0.0", returnDirect=True)

####################################################################################
    @classmethod
    def about(cls, args: list[str] = None):
        """Get information about the agent."""
        raise NotImplementedError("Each graph must implement its own about method")
        # Implementation should return CommandOutput like:
        # return CommandOutput(
        #     cmdOutput="About this agent...", 
        #     returnDirect=True
        # )


####################################################################################
    @classmethod
    def url(cls, args: list[str] = None):
        """Extract and display the main content from a website URL.

        Usage: /url https://example.com
        Scrapes the content from the provided URL and displays it in the chat.
        This allows you to discuss, summarize, or analyze web content directly.
        """
        import requests
        from readability import Document
        import html2text

        # Check if URL was provided
        if not args or len(args) == 0:
            error_msg = "⚠️ Please provide a URL.\n\n**Example:**\n```\n/url https://example.com\n```"
            return CommandOutput(cmdOutput=error_msg)

        # Get the first argument as the URL
        url = args[0]

        # Check if URL uses HTTP instead of HTTPS
        if url.startswith("http://"):
            error_msg = f"⚠️ The URL must start with `https://`\n\n**Example:**\n```\n/url https://example.com\n```"
            return CommandOutput(cmdOutput=error_msg)

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

            return CommandOutput(cmdOutput=result)

        except requests.exceptions.RequestException as e:
            error_msg = f"⚠️ Error fetching the URL: {str(e)}"
            return CommandOutput(cmdOutput=error_msg)
        except Exception as e:
            error_msg = f"⚠️ Error processing the webpage content: {str(e)}"
            return CommandOutput(cmdOutput=error_msg)




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