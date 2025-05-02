from flask import Flask, request, jsonify
from flask_cors import CORS
from action import Action
from models import WebPageInput, SearchInput, HighlightInput
import logging
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configure CORS to allow all origins during development
CORS(app, supports_credentials=True)

# Initialize action handler
action_handler = Action()

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is running"})

@app.route('/index', methods=['POST'])
def index_page():
    try:
        data = request.json
        logger.info(f"Received indexing request for URL: {data.get('url', 'unknown')}")
        
        if not data or 'url' not in data or 'content' not in data:
            logger.error("Invalid request data: missing url or content")
            return jsonify({"success": False, "error": "Missing url or content"})
        
        input_data = WebPageInput(url=data['url'], content=data['content'])
        result = action_handler.index_page(input_data)
        
        if not result.success:
            error_msg = result.error if result.error else "Unknown error during indexing"
            logger.error(f"Indexing failed: {error_msg}")
            return jsonify({"success": False, "error": error_msg})
        
        logger.info(f"Successfully indexed page: {data['url']}")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error in index_page: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'No query provided'}), 400
            
        logger.info(f"Searching for: {query}")
        
        # Use action handler to search
        input_data = SearchInput(query=query)
        result = action_handler.search_pages(input_data)
        
        # Filter results based on similarity threshold
        SIMILARITY_THRESHOLD = 0.000005  # Adjust this value to control result relevance
        filtered_results = []
        
        for search_result in result.results:
            # Calculate text similarity using difflib
            similarity = difflib.SequenceMatcher(None, query.lower(), search_result.content.lower()).ratio()
            
            # Only include results that are relevant enough
            if similarity > SIMILARITY_THRESHOLD:
                # Add similarity score to result
                filtered_results.append({
                    'url': search_result.url,
                    'content': search_result.content,
                    'similarity': similarity
                })
        
        # Sort by similarity score
        filtered_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Take top 5 most relevant results
        top_results = filtered_results[:5]
        
        logger.info(f"Found {len(top_results)} relevant results")
        return jsonify({'results': top_results})
        
    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/highlight', methods=['POST'])
def highlight():
    try:
        data = request.json
        logger.info(f"Received highlight request for query: {data.get('query', 'unknown')}")
        
        if not data or 'text' not in data or 'query' not in data:
            logger.error("Invalid request data: missing text or query")
            return jsonify({"success": False, "error": "Missing text or query"})
        
        input_data = HighlightInput(text=data['text'], query=data['query'])
        result = action_handler.highlight_text(input_data)
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error in highlight: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/pages', methods=['GET'])
def list_pages():
    try:
        logger.info("Received request to list pages")
        result = action_handler.list_indexed_pages()
        return jsonify(result.model_dump())
    except Exception as e:
        logger.error(f"Error in list_pages: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(port=5001, debug=True, host='0.0.0.0') 