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

        # strip whitespace
        url = url.strip()

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


    @classmethod
    def summarize(cls, args: list[str] = None):
        """Extract and summarize the main content from a website URL.

        Usage: /summarize https://example.com
        Scrapes the content from the provided URL and generates a concise summary.
        This allows you to quickly understand the key points from web content.
        """
        # Get the URL content using the base url command
        url_result = cls.url(args)

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



    @classmethod
    def yt(cls, args: list[str] = None):
        """
yt - get youtube transcript

Extract and provide the transcript from a YouTube video.

Usage: /yt https://www.youtube.com/watch?v=example
Retrieves the transcript from the provided YouTube URL along with video details.
"""
        import asyncio
        from langchain_community.document_loaders import YoutubeLoader
        from langchain_yt_dlp.youtube_loader import YoutubeLoaderDL

        if not args or len(args) == 0:
            return CommandOutput(
                cmdOutput="Error: Please provide a YouTube URL",
                returnDirect=True
            )

        url = args[0]
        
        # Define an async function to handle the YouTube API calls
        async def get_transcript_async(url):
            try:
                # Check if the URL is valid
                if not url or url == "":
                    raise Exception(f"Invalid YouTube URL: {url}")
                # LLM's love passing in this url when the user doesn't provide one
                elif "dQw4w9WgXcQ" in url:
                    raise Exception("Rick Roll URL provided... is that what you want?).")

                # Get video details
                title = ""
                author = ""
                details = await YoutubeLoaderDL.from_youtube_url(url, add_video_info=True).aload()

                if len(details) == 0:
                    raise Exception("Failed to get video details")

                title = details[0].metadata["title"]
                author = details[0].metadata["author"]

                # Hardcode language values
                languages = ["en", "en_auto"]

                # Try to get transcript using direct API as a more reliable method
                try:
                    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
                    
                    # Extract video ID from URL
                    import re
                    video_id = None
                    if "youtube.com" in url:
                        video_id = re.search(r'v=([\w-]+)', url)
                        if video_id:
                            video_id = video_id.group(1)
                    elif "youtu.be" in url:
                        video_id = url.split('/')[-1].split('?')[0]
                    
                    if not video_id:
                        raise Exception(f"Could not extract video ID from URL: {url}")
                    
                    # Get transcript using direct API
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    
                    # Try to find English transcript first
                    try:
                        transcript_data = transcript_list.find_transcript(['en'])
                    except Exception:
                        # If no English transcript, get the first available and translate it
                        # Get the first available transcript
                        transcript_data = next(transcript_list._transcripts.values().__iter__())
                        transcript_data = transcript_data.translate('en')
                    
                    transcript_parts = transcript_data.fetch()
                    
                    # Format transcript with timestamps
                    transcript_lines = []
                    for part in transcript_parts:
                        minutes = int(part['start'] // 60)
                        seconds = int(part['start'] % 60)
                        timestamp = f"[{minutes:02d}:{seconds:02d}] "
                        transcript_lines.append(f"{timestamp}{part['text']}")
                    
                    transcript_text = "\n".join(transcript_lines)
                    
                except (TranscriptsDisabled, Exception) as e:
                    # Fallback to LangChain method if direct API fails
                    transcript = await YoutubeLoader.from_youtube_url(
                        url,
                        add_video_info=False,
                        language=languages,
                        translation="en",
                    ).aload()

                    if len(transcript) == 0:
                        raise Exception(f"Failed to find transcript for {title if title else url}")

                    # Format transcript
                    transcript_text = "\n".join([document.page_content for document in transcript])

                if title and author:
                    transcript_text = f"# {title}\n\n### by {author}\n\n{transcript_text}"

                return transcript_text

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                return f"Error: {str(e)}\n\nDetails:\n```\n{error_details}\n```"

        try:
            transcript_result = asyncio.run(get_transcript_async(url))
            
            return CommandOutput(
                cmdOutput=transcript_result,
                returnDirect=True
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_message = f"Error running async function: {str(e)}\n\nDetails:\n```\n{error_details}\n```"
            return CommandOutput(
                cmdOutput=error_message,
                returnDirect=True
            )



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