# memory.py

import numpy as np
import faiss
import requests
from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path
import hashlib
from models import SearchResult, SearchOutput


class MemoryItem(BaseModel):
    text: str
    type: Literal["preference", "tool_output", "fact", "query", "system"] = "fact"
    timestamp: Optional[str] = datetime.now().isoformat()
    tool_name: Optional[str] = None
    user_query: Optional[str] = None
    tags: List[str] = []
    session_id: Optional[str] = None


class MemoryManager:
    def __init__(self, embedding_url="http://localhost:11434/api/embeddings", model_name="nomic-embed-text"):
        self.embedding_url = embedding_url
        self.model_name = model_name
        self.index = None
        self.metadata = []
        self.index_dir = Path("faiss_index")
        self.index_dir.mkdir(exist_ok=True)
        self.index_file = self.index_dir / "index.bin"
        self.metadata_file = self.index_dir / "metadata.json"
        self.embedding_dim = 768  # Updated to match Ollama's output dimension
        self.load_index()

    def load_index(self):
        """Load existing index and metadata or create new ones"""
        try:
            if self.index_file.exists():
                print("Loading existing index...")
                try:
                    self.index = faiss.read_index(str(self.index_file))
                    print(f"Loaded FAISS index with dimension: {self.index.d}")
                except Exception as e:
                    print(f"Error loading FAISS index: {e}")
                    print("Creating new index...")
                    self.index = faiss.IndexFlatL2(self.embedding_dim)
                
                try:
                    with open(self.metadata_file, 'r') as f:
                        loaded_metadata = json.load(f)
                        # Filter out any non-webpage entries
                        self.metadata = [
                            item for item in loaded_metadata 
                            if isinstance(item, dict) and 'url' in item and 'content' in item
                        ]
                    print(f"Loaded {len(self.metadata)} webpages from metadata")
                except Exception as e:
                    print(f"Error loading metadata: {e}")
                    self.metadata = []
            else:
                print("Creating new index...")
                self.index = faiss.IndexFlatL2(self.embedding_dim)
                self.metadata = []
                self.save_index()  # Create initial files
        except Exception as e:
            print(f"Error in load_index: {e}")
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = []
            self.save_index()

    def save_index(self):
        """Save index and metadata to disk"""
        try:
            print(f"Saving index with {len(self.metadata)} webpages...")
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
            print("Index saved successfully")
        except Exception as e:
            print(f"Error saving index: {e}")
            raise  # Re-raise the exception to handle it in the calling code

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using the embedding model"""
        try:
            print(f"Getting embedding for text of length {len(text)}...")
            response = requests.post(
                self.embedding_url,
                json={"model": self.model_name, "prompt": text}
            )
            response.raise_for_status()
            embedding = np.array(response.json()["embedding"], dtype=np.float32)
            print("Embedding generated successfully")
            return embedding
        except requests.exceptions.RequestException as e:
            print(f"Error getting embedding (HTTP error): {e}")
            raise
        except Exception as e:
            print(f"Error getting embedding (other error): {e}")
            raise

    def add(self, url: str, content: str) -> bool:
        """Add a web page to the index"""
        try:
            print(f"Indexing webpage: {url}")
            print(f"Content length: {len(content)} characters")
            
            # Validate input
            if not url or not content:
                print("Invalid input: URL and content are required")
                return False

            # Check if URL is already indexed
            for item in self.metadata:
                if item['url'] == url:
                    print(f"URL already indexed: {url}")
                    return True
            
            # Generate embedding
            try:
                embedding = self.get_embedding(content)
                print(f"Generated embedding with shape: {embedding.shape}")
            except Exception as e:
                print(f"Failed to generate embedding: {e}")
                return False
            
            # Validate embedding shape
            if embedding.shape[0] != self.embedding_dim:
                print(f"Invalid embedding shape: {embedding.shape}, expected ({self.embedding_dim},)")
                return False
            
            # Add to index
            try:
                # Reshape embedding to 2D array (1, embedding_dim)
                embedding_2d = embedding.reshape(1, -1)
                print(f"Reshaped embedding to: {embedding_2d.shape}")
                
                # Verify index is initialized
                if self.index is None:
                    print("Initializing new FAISS index")
                    self.index = faiss.IndexFlatL2(self.embedding_dim)
                
                # Add to index
                self.index.add(embedding_2d)
                print("Successfully added to FAISS index")
            except Exception as e:
                print(f"Failed to add to FAISS index: {str(e)}")
                print(f"Index type: {type(self.index)}")
                print(f"Index dimension: {self.index.d if hasattr(self.index, 'd') else 'unknown'}")
                return False
            
            # Store metadata
            try:
                page_data = {
                    'url': url,
                    'content': content,
                    'timestamp': datetime.now().isoformat(),
                    'hash': hashlib.md5(content.encode()).hexdigest()
                }
                self.metadata.append(page_data)
                print("Successfully stored metadata")
            except Exception as e:
                print(f"Failed to store metadata: {e}")
                return False
            
            # Save index
            try:
                self.save_index()
                print(f"Successfully indexed webpage: {url}")
                return True
            except Exception as e:
                print(f"Failed to save index: {e}")
                return False
        except Exception as e:
            print(f"Error adding webpage to index: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> SearchOutput:
        """Search for relevant pages"""
        if not self.index or len(self.metadata) == 0:
            return SearchOutput(results=[])
        
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            
            # Ensure top_k doesn't exceed available documents
            actual_top_k = min(top_k, len(self.metadata))
            
            # Search index
            D, I = self.index.search(query_embedding.reshape(1, -1), actual_top_k)
            
            # Get results
            results = []
            for i, idx in enumerate(I[0]):
                if idx < len(self.metadata):
                    result = self.metadata[idx]
                    results.append(SearchResult(
                        url=result['url'],
                        content=result['content'],
                        score=float(D[0][i]),  # Use i instead of idx for score
                        timestamp=datetime.fromisoformat(result['timestamp']),
                        hash=result['hash']
                    ))
            
            return SearchOutput(results=results)
        except Exception as e:
            print(f"Error searching index: {e}")
            return SearchOutput(results=[])

    def _get_embedding(self, text: str) -> np.ndarray:
        response = requests.post(
            self.embedding_url,
            json={"model": self.model_name, "prompt": text}
        )
        response.raise_for_status()
        return np.array(response.json()["embedding"], dtype=np.float32)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        type_filter: Optional[str] = None,
        tag_filter: Optional[List[str]] = None,
        session_filter: Optional[str] = None
    ) -> List[MemoryItem]:
        if not self.index or len(self.metadata) == 0:
            return []

        query_vec = self._get_embedding(query).reshape(1, -1)
        D, I = self.index.search(query_vec, top_k * 2)  # Overfetch to allow filtering

        results = []
        for idx in I[0]:
            if idx >= len(self.metadata):
                continue
            result = self.metadata[idx]

            # Filter by type
            if type_filter and result['type'] != type_filter:
                continue

            # Filter by tags
            if tag_filter and not any(tag in result['tags'] for tag in tag_filter):
                continue

            # Filter by session
            if session_filter and result['session_id'] != session_filter:
                continue

            results.append(MemoryItem(
                text=result['content'],
                type=result['type'],
                timestamp=result['timestamp'],
                tool_name=result['tool_name'],
                user_query=result['user_query'],
                tags=result['tags'],
                session_id=result['session_id']
            ))
            if len(results) >= top_k:
                break

        return results

    def bulk_add(self, items: List[MemoryItem]):
        for item in items:
            self.add(item.text, item.text)

    def list_pages(self) -> List[dict]:
        """List all indexed webpages"""
        try:
            print(f"Listing {len(self.metadata)} webpages...")
            pages = []
            for item in self.metadata:
                if isinstance(item, dict) and 'url' in item and 'timestamp' in item and 'hash' in item:
                    pages.append({
                        'url': item['url'],
                        'timestamp': item['timestamp'],
                        'hash': item['hash']
                    })
                else:
                    print(f"Skipping invalid webpage metadata: {item}")
            return pages
        except Exception as e:
            print(f"Error listing webpages: {e}")
            return []
