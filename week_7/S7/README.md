# Intelligent Web Search and Memory System

This project implements an intelligent web search and memory system that combines web page indexing, semantic search, and memory management capabilities. The system uses advanced natural language processing and vector embeddings to provide intelligent search and information retrieval.

## Features

- Web page indexing and storage
- Semantic search with relevance scoring
- Memory management with FAISS vector indexing
- Chrome extension integration
- RESTful API server
- Intelligent agent system for task execution

## Project Structure

### Core Components

- `server.py`: Main Flask server that handles HTTP requests and provides REST API endpoints
- `agent.py`: Intelligent agent system that processes user queries and executes tasks
- `memory.py`: Memory management system using FAISS for vector storage and retrieval
- `perception.py`: Handles perception and understanding of user inputs
- `decision.py`: Decision-making system for planning and executing actions
- `action.py`: Action execution system for carrying out planned tasks
- `models.py`: Data models and schemas used throughout the system

### Chrome Extension

The `chrome_extension/` directory contains a browser extension that allows users to:
- Index web pages for later retrieval
- Search through indexed content
- Highlight relevant text on web pages

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Ollama (for embeddings)
- Chrome browser (for extension)

### Installation

1. Clone the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start Ollama server (for embeddings):
```bash
ollama serve
```

4. Start the main server:
```bash
python server.py
```

5. Install the Chrome extension:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `chrome_extension` directory

## API Endpoints

### `/index` (POST)
Index a web page for later retrieval
- Input: URL and content
- Output: Success status

### `/search` (POST)
Search through indexed pages
- Input: Search query
- Output: List of relevant results with similarity scores

### `/highlight` (POST)
Highlight relevant text based on a query
- Input: Text and query
- Output: Highlighted text

### `/pages` (GET)
List all indexed pages
- Output: List of indexed pages with metadata

## Usage

1. Start the server and ensure Ollama is running
2. Use the Chrome extension to index web pages
3. Search through indexed content using the extension or API
4. The system will automatically manage memory and provide relevant results

## Technical Details

### Memory System
- Uses FAISS for efficient vector similarity search
- Stores embeddings in a persistent index
- Supports metadata filtering and session management

### Search System
- Implements semantic search using vector embeddings
- Provides relevance scoring and filtering
- Supports highlighting of relevant text

### Agent System
- Processes natural language queries
- Plans and executes tasks
- Maintains context through memory management

