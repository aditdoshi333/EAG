# Web Page Indexer Chrome Extension

A Chrome extension that allows you to index and search web pages, with semantic search capabilities powered by Ollama and FAISS.

## Features

- Index web pages as you browse
- Semantic search across indexed pages
- Highlight matching text when clicking search results
- Automatic content extraction and cleaning
- Efficient vector storage using FAISS
- Powered by Ollama for embeddings

## Project Structure

### Chrome Extension (`chrome_extension/`)

- `manifest.json` - Extension configuration and permissions
- `popup.html` - Extension popup interface
- `popup.js` - Popup logic and search functionality
- `content.js` - Content script for page indexing and text highlighting
- `background.js` - Background script for tab management
- `icons/` - Extension icons in various sizes

### Server (`server/`)

- `server.py` - Main Flask server and API endpoints
- `action.py` - Action handler for search and indexing operations
- `memory.py` - Memory manager for FAISS index and vector storage
- `models.py` - Pydantic models for request/response validation
- `faiss_index/` - Directory for storing FAISS index files

## Prerequisites

- Python 3.8+
- Chrome browser
- Ollama running locally (for embeddings)

## Setup Instructions

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Ollama**
   ```bash
   ollama serve
   ```

3. **Start the Flask Server**
   ```bash
   python server/server.py
   ```
   The server will start on `http://localhost:5001`

4. **Install Chrome Extension**
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (top right)
   - Click "Load unpacked"
   - Select the `chrome_extension` directory

## Usage

1. **Indexing Pages**
   - Browse any webpage
   - The extension automatically indexes the page content
   - You can see indexing status in the browser console

2. **Searching**
   - Click the extension icon to open the popup
   - Enter your search query
   - Results will show matching pages with previews
   - Click a result to navigate to the page with highlighted text

## Server Components

### `server.py`
- Main Flask application
- Handles API endpoints for indexing and searching
- Manages request validation and response formatting
- Implements similarity filtering for search results

### `action.py`
- Contains `ActionHandler` class for business logic
- Manages search and indexing operations
- Interfaces with the memory manager
- Handles content processing and embedding generation

### `memory.py`
- Contains `MemoryManager` class for vector storage
- Manages FAISS index operations
- Handles vector storage and retrieval
- Implements similarity search functionality

### `models.py`
- Defines Pydantic models for data validation
- Includes models for:
  - `IndexInput`: Page indexing requests
  - `SearchInput`: Search requests
  - `SearchResult`: Individual search results
  - `SearchOutput`: Search response format

## Unused Files

The following files are not currently being used in the project and can be safely removed:

### Root Directory
- `generate_icons.py` - Icon generation script (icons are already generated)
- `decision.py` - Unused decision-making module
- `perception.py` - Unused perception module
- `example3.py` - Example file
- `agent.py` - Unused agent module
- `example2.py` - Example file

These files appear to be from earlier development stages or example implementations and are not required for the current functionality of the application.

## Development

### Adding New Features
1. Update the Chrome extension files as needed
2. Modify server endpoints in `server.py`
3. Add new models in `models.py` if required
4. Update the memory manager in `memory.py` for new functionality

### Testing
1. Ensure Ollama is running
2. Start the Flask server
3. Reload the Chrome extension
4. Test new features in the browser

## Troubleshooting

1. **Extension Not Working**
   - Check if the server is running
   - Verify Ollama is running
   - Check browser console for errors
   - Reload the extension

2. **Search Not Working**
   - Verify page indexing in console
   - Check server logs for errors
   - Ensure FAISS index is properly initialized

3. **Highlighting Not Working**
   - Check content script logs in the webpage console
   - Verify message passing between popup and content script
   - Ensure proper permissions in manifest.json

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 