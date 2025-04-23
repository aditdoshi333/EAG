import os
import json
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
import uuid
from pydantic import BaseModel

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    from datetime import datetime
    def log(stage: str, msg: str):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class MemoryItem(BaseModel):
    text: str
    type: Literal["user_query", "tool_output", "system_message", "agent_response"] = "user_query"
    timestamp: str = datetime.now().isoformat()
    tool_name: Optional[str] = None
    user_query: Optional[str] = None
    tags: List[str] = []
    session_id: Optional[str] = None

class MemoryManager:
    def __init__(self):
        self.memory: List[MemoryItem] = []
        self.logs_directory = "logs"
        os.makedirs(self.logs_directory, exist_ok=True)
        
    def add(self, item: MemoryItem) -> None:
        """Add an item to memory and save it to the log"""
        self.memory.append(item)
        self._save_to_log(item)
        log("memory", f"Added {item.type}: {item.text[:50]}...")
        
    def retrieve(self, 
                query: str, 
                top_k: int = 3, 
                type_filter: Optional[str] = None,
                session_filter: Optional[str] = None) -> List[MemoryItem]:
        """Retrieve relevant memory items"""
        
        # Filter by type and session if needed
        filtered_items = self.memory
        
        if type_filter:
            filtered_items = [item for item in filtered_items if item.type == type_filter]
            
        if session_filter:
            filtered_items = [item for item in filtered_items if item.session_id == session_filter]
        
        # Simple recency-based retrieval for now
        # In a real system, we would use embeddings for semantic similarity
        sorted_items = sorted(filtered_items, 
                             key=lambda x: x.timestamp, 
                             reverse=True)
        
        return sorted_items[:top_k]
    
    def _save_to_log(self, item: MemoryItem) -> None:
        """Save memory item to log file"""
        log_file = os.path.join(self.logs_directory, f"{item.session_id or 'unknown'}.json")
        
        with open(log_file, "a") as f:
            f.write(json.dumps(item.model_dump()) + "\n")
            
    def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the conversation history for a session"""
        history = []
        
        for item in self.memory:
            if item.session_id == session_id:
                if item.type == "user_query":
                    history.append({"role": "user", "content": item.text})
                elif item.type == "agent_response":
                    history.append({"role": "assistant", "content": item.text})
                    
        return history 