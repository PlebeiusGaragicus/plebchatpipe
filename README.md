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
```


### Launch LangGraph studio


```

langgraph dev --tunnel
```