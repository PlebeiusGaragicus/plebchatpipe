# Which Ollama models are we to use?

Well... perhaps it's ok to be opinionated... Let's select a few and solidify their roles.

- **Chat:** `gemma3:12b-it-q8_0`
- **Tool use:** `llama3.1:8b-instruct-q8_0`
- **Reasoning:** `phi4-reasoning:14b-q8_0`
- **Vision:** `gemma3:12b-it-q8_0`

```
llama3.1:8b-instruct-q8_0    8.5 GB
llama3.2:3b-instruct-q8_0    3.4 GB
gemma3:12b-it-q8_0           13 GB
phi4:14b-q8_0                15 GB
phi4-reasoning:14b-q8_0      17 GB
```

## How to create a "large context" Ollama models

NOTE: Ollama's default context length for models is 2048 tokens

```sh
ollama create -f ./llama llama3.1longctx
```
