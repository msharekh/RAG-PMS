# RAG-PMS

## Technologies Used
1. Python 3.8+ - Core programming language
1. Ollama - Local LLM for embeddings and text generation
1. ChromaDB - Lightweight vector database (in-memory)
1. LangChain - Framework for RAG pipeline (optional but helpful)
1. Pandas - Data manipulation


pip install ollama chromadb pandas langchain langchain-community sentence-transformers

packages:

Name: ollama
Version: 0.6.2
Summary: The official Python client for Ollama.
Home-page: https://ollama.com
License-Expression: MIT
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: httpx, pydantic

Name: chromadb
Version: 1.5.8
Summary: Chroma.
Home-page: https://github.com/chroma-core/chroma
Requires: bcrypt, build, grpcio, httpx, importlib-resources, jsonschema, kubernetes, mmh3, numpy, onnxruntime, opentelemetry-api, opentelemetry-exporter-otlp-proto-grpc, opentelemetry-sdk, orjson, overrides, pybase64, pydantic, pydantic-settings, pypika, pyyaml, rich, tenacity, tokenizers, tqdm, typer, typing-extensions, uvicorn
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages

Name: pandas
Version: 3.0.1
Summary: Powerful data structures for data analysis, time series, and statistics
Home-page: https://pandas.pydata.org
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: numpy, python-dateutil, tzdata
Required-by: streamlit

Name: sentence-transformers
Version: 5.4.1
Summary: Embeddings, Retrieval, and Reranking
Home-page: https://www.SBERT.net
License: Apache 2.0
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: huggingface-hub, numpy, scikit-learn, scipy, torch, tqdm, transformers, typing_extensions

Name: langchain
Version: 1.3.13
Summary: Building applications with LLMs through composability
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: langchain-core, langgraph, pydantic

Name: langchain-community
Version: 0.4.2
Summary: Community contributed LangChain integrations.
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: aiohttp, httpx-sse, langchain-classic, langchain-core, langsmith, numpy, pydantic-settings, pyyaml, requests, sqlalchemy, tenacity

Name: Flask
Version: 3.1.3
Summary: A simple framework for building complex web applications.
License-Expression: BSD-3-Clause
Location: C:\Users\Personal\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages
Requires: blinker, click, itsdangerous, jinja2, markupsafe, werkzeug


Complete Flow Diagram
text
1. START
   ↓
2. Create AECRAG System
   ↓
3. Generate 100 Sample Projects
   ↓
4. Convert Projects to Text (prepare_documents)
   ↓
5. Create Embeddings (generate_embeddings)
   ↓
6. Store in ChromaDB (index_projects)
   ↓
7. User Asks Question
   ↓
8. Convert Question to Embedding
   ↓
9. Find Similar Projects (query)
   ↓
10. Send to AI Model (generate_response)
   ↓
11. Display Answer to User
Memory Usage Breakdown
text
Ollama llama3.2 model:    ~2.5 GB RAM
Ollama embedding model:    ~1.5 GB RAM
ChromaDB storage:          ~100 MB
Python overhead:          ~200 MB
Total:                    ~4.3 GB (under 8GB limit)



Key Concepts for Beginners
What is RAG?
Retrieval Augmented Generation

Retrieval: Find relevant documents (projects)

Augmented: Add this info to the prompt

Generation: AI generates answer based on this

Why Use Ollama?
Runs locally (no internet needed)

Free and private

Works on modest hardware

Why ChromaDB?
Lightweight vector database

Fast similarity search

Works in-memory (fast for POC)

The "Less Code" Approach
~200 lines total

Each function does one thing

Clear comments throughout

No complex frameworks
