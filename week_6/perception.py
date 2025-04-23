from typing import List, Dict, Optional, Any
import os
from dotenv import load_dotenv
import google.generativeai as genai
import re
import json
from models import UserQuery

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class PerceptionResult:
    def __init__(self, 
                 user_input: str, 
                 intent: Optional[str] = None, 
                 entities: List[str] = None, 
                 tool_hint: Optional[str] = None,
                 reasoning_type: Optional[str] = None):
        self.user_input = user_input
        self.intent = intent
        self.entities = entities or []
        self.tool_hint = tool_hint
        self.reasoning_type = reasoning_type

def extract_perception(user_input: str) -> PerceptionResult:
    """Extracts intent, entities, tool hints, and reasoning type using LLM"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
You are an AI that extracts structured information from user input to help a research assistant agent.

Input: "{user_input}"

Return the response as a JSON object with these keys:
- intent: (brief phrase describing what the user wants to do)
- entities: (list of strings representing keywords, topics, or named entities from the query)
- tool_hint: (suggest one of these tools: paper_retrieval_tool, dataset_explorer_tool, citation_network_analyzer, concept_extractor, cross_domain_connector, or None)
- reasoning_type: (one of: retrieval, analysis, comparison, synthesis)

Only output valid JSON without any additional text or explanation.
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        log("perception", f"LLM output: {response_text}")
        
        # Clean response to ensure valid JSON
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        parsed = json.loads(response_text)
        
        # Ensure entities is always a list
        if isinstance(parsed.get("entities"), dict):
            parsed["entities"] = list(parsed["entities"].values())
        elif not parsed.get("entities"):
            parsed["entities"] = []
            
        return PerceptionResult(
            user_input=user_input,
            intent=parsed.get("intent"),
            entities=parsed.get("entities", []),
            tool_hint=parsed.get("tool_hint"),
            reasoning_type=parsed.get("reasoning_type")
        )
    except Exception as e:
        log("perception", f"Extraction failed: {e}")
        return PerceptionResult(user_input=user_input) 