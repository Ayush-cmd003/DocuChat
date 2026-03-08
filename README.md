# DocuChat

An AI-powered document question-answering system built with **Streamlit, LangChain, ChromaDB, and Groq LLM**.

The application allows users to upload documents and ask questions about them using Retrieval-Augmented Generation (RAG).

---

## Features

* Upload **PDF or DOCX documents**
* AI-powered document Q&A
* Multi-chat support
* Vector search using **ChromaDB**
* Streaming responses like ChatGPT
* Groq-powered LLM inference
* Persistent vector database

---

## Architecture

```
Streamlit UI
    ↓
Document Upload
    ↓
Text Extraction
    ↓
Chunking
    ↓
Embeddings (BGE)
    ↓
Chroma Vector DB
    ↓
Similarity Search
    ↓
Groq LLM
    ↓
Streaming Answer
```

---

## Installation

### 1 Install dependencies

```
pip install -r requirements.txt
```

---

### 2 Run the application

```
streamlit run app.py
```

---

## API Key Setup

### Create a Groq Account

1. Sign up at https://console.groq.com
 if you don’t already have an account.

### Generate an API Key

1. Go to https://console.groq.com

2. Click API Keys

3. Select + Create API Key

4. Name it (for example: DocuChat Integration) and click Submit

5. Copy the key — it will only be shown once.

---

## Project Structure

```
ai-document-assistant
│
├── app.py
├── requirements.txt
├── README.md
│
├── assests
├── config
├── docuchat_vector_db
├── prompts
├── services
├── sessions
├── styles
└── utils
```

---

## Technologies Used

* Streamlit
* LangChain
* ChromaDB
* HuggingFace Embeddings
* Groq LLM (Qwen3-32B)

---

## License

MIT License
