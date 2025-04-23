import os
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import google.generativeai as genai
import json
from perception import PerceptionResult
from memory import MemoryItem

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

def generate_plan(
    perception: PerceptionResult,
    memory_items: List[MemoryItem],
    tool_descriptions: Optional[str] = None
) -> str:
    """Generates a plan (tool call or final answer) using LLM based on the perception and memory"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Format memory items for context
    memory_text = ""
    tool_results_found = False
    empty_results_found = False
    tools_used = set()
    failed_tools = set()
    has_paper_ids = False
    
    if memory_items:
        for item in memory_items:
            if item.type == "tool_output" and item.tool_name:
                tools_used.add(item.tool_name)
                
                # Check for empty results from specific tools
                if item.tool_name == "citation_network_analyzer" and ("nodes': []" in item.text or "papers': []" in item.text):
                    empty_results_found = True
                    failed_tools.add(item.tool_name)
                    memory_text += f"- Previous {item.tool_name} returned EMPTY RESULTS. Use a different tool.\n"
                    continue
                    
                # Check for paper IDs in results for potential follow-up tools
                if item.tool_name == "paper_retrieval_tool" and "id" in item.text:
                    has_paper_ids = True
                
                memory_text += f"- Previous {item.tool_name} result: {item.text}\n"
                tool_results_found = True
            else:
                memory_text += f"- {item.text}\n"
    else:
        memory_text = "None available"
        
    # Include tool descriptions if available
    tools_context = f"\nAvailable tools:\n{tool_descriptions}" if tool_descriptions else ""
    
    # Create targeted guidance based on the current state
    extra_instructions = ""
    
    if tool_results_found:
        extra_instructions += "\nIMPORTANT: If you have enough information from previous tool calls to answer the query, return a FINAL_ANSWER directly rather than making additional tool calls."
    
    if empty_results_found:
        extra_instructions += "\nWARNING: Some previous tool calls returned empty results. DO NOT use the same tool again with similar parameters."
        # Suggest alternative tools
        if "citation_network_analyzer" in failed_tools and has_paper_ids:
            extra_instructions += "\nSince citation_network_analyzer returned empty results, try using concept_extractor instead to analyze the paper content."
    
    if len(tools_used) >= 2:
        extra_instructions += "\nYou've already used multiple tools. Consider synthesizing the information you have into a FINAL_ANSWER."
    
    # First-time query recommendations
    if not tools_used:
        if "papers" in perception.user_input.lower() or "research" in perception.user_input.lower():
            extra_instructions += "\nThis query is about research papers. Start with paper_retrieval_tool to find relevant papers."
        elif "domain" in perception.user_input.lower() or "connection" in perception.user_input.lower() or "relation" in perception.user_input.lower():
            extra_instructions += "\nThis query is about connecting domains. Consider using cross_domain_connector."
    
    prompt = f"""
You are a research assistant agent that uses specialized tools to answer questions. 
Your job is to determine which tool to use next or provide a final answer.

User query: "{perception.user_input}"
Intent: {perception.intent or "Unknown"}
Entities detected: {', '.join(perception.entities) if perception.entities else "None"}
Tool suggestion: {perception.tool_hint or "None"}
Reasoning type required: {perception.reasoning_type or "Unknown"}

{tools_context}

Relevant context from memory:
{memory_text}
{extra_instructions}

Respond in ONE of these formats:
1. If you need to use a tool, reply with:
   TOOL_CALL: tool_name|param1=value1|param2=value2|param3=value3

2. If you have the final answer, reply with:
   FINAL_ANSWER: your detailed answer here

Your response should be exactly ONE of the above formats. No additional text or explanation.

Examples:
- TOOL_CALL: paper_retrieval_tool|keywords=["quantum computing"]|authors=["Feynman"]
- TOOL_CALL: concept_extractor|text="quantum superposition refers to..."
- FINAL_ANSWER: Based on the analysis, the relationship between domain X and domain Y is...
"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        log("decision", f"Generated plan: {response_text}")
        
        # Return the first valid line that follows the expected format
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("TOOL_CALL:") or line.startswith("FINAL_ANSWER:"):
                return line
                
        # If no valid format was found, assume the LLM is trying to give a final answer
        return f"FINAL_ANSWER: {response_text}"
        
    except Exception as e:
        log("decision", f"Plan generation failed: {e}")
        return "FINAL_ANSWER: I encountered an error while processing your request."

def parse_tool_call(tool_call: str) -> tuple[str, Dict[str, Any]]:
    """Parse a tool call string into tool name and parameters"""
    if not tool_call.startswith("TOOL_CALL:"):
        raise ValueError("Invalid tool call format")
        
    tool_parts = tool_call.replace("TOOL_CALL:", "").strip().split("|")
    
    if not tool_parts:
        raise ValueError("Empty tool call")
        
    tool_name = tool_parts[0]
    params = {}
    
    for part in tool_parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            # Try to parse JSON if it looks like a list or object
            if (value.startswith("[") and value.endswith("]")) or \
               (value.startswith("{") and value.endswith("}")):
                try:
                    params[key] = json.loads(value)
                except:
                    params[key] = value
            else:
                params[key] = value
                
    return tool_name, params 