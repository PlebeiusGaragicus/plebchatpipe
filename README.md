This is a test project that aims to dockerize LangGraph agents with FastAPI to be used in an OpenWebUI pipeline.



```

echo GRAPHS
curl -s http://localhost:9000/graphs | jq
echo MODELS
curl -s http://localhost:9000/models | jq

```

# DEVELOPMENT

### Create python environment
```
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# LangGraph needs it to be installed locally
python -m pip install -e .
```

### Launch LangGraph studio


```

langgraph dev --tunnel
```

# Create Ollama models

```
ollama create -f ./Modelfiles/llama llama3big
```

# Vibe coding 101

 - YouTube tutorial: https://www.youtube.com/watch?v=fk2WEVZfheI
 - MCPDoc: https://github.com/langchain-ai/mcpdoc
 - LangGraph LLMs.txt: https://langchain-ai.github.io/langgraph/llms.txt
 - Windsurf docs: https://docs.windsurf.com/windsurf/cascade/mcp
 - Example MCP servers: https://github.com/modelcontextprotocol/servers?tab=readme-ov-file

 ```sh
# test the server
uvx --from mcpdoc mcpdoc \
    --urls "LangGraph:https://langchain-ai.github.io/langgraph/llms.txt" "LangChain:https://python.langchain.com/llms.txt" \
    --transport sse \
    --port 8082 \
    --host localhost
 ```

 # Setup Ollama properly

 ```sh
launchctl setenv OLLAMA_FLASH_ATTENTION true
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_KEEP_ALIVE -1
launchctl setenv OLLAMA_NUM_PARALLEL 2
```

```sh
launchctl getenv OLLAMA_FLASH_ATTENTION
launchctl getenv OLLAMA_KV_CACHE_TYPE
launchctl getenv OLLAMA_KEEP_ALIVE
launchctl getenv OLLAMA_NUM_PARALLEL
```


```sh
ollama pull gemma3:12b-it-q8_0
ollama pull llama3.1:8b-instruct-q8_0
```
