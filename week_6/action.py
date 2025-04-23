import os
import json
from typing import Dict, Any, Optional, Union, List
from mcp import ClientSession
from pydantic import BaseModel
from decision import parse_tool_call

# Optional: import log from agent if shared, else define locally
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class ToolResult(BaseModel):
    """Container for tool execution results"""
    tool_name: str
    parameters: Dict[str, Any]
    output: Any
    raw_response: Optional[Any] = None

async def execute_tool(
    session: ClientSession,
    tools: List[Any],
    tool_call: str
) -> ToolResult:
    """Execute a tool call through the MCP session"""
    try:
        tool_name, parameters = parse_tool_call(tool_call)
        
        # Check if the tool exists
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        log("action", f"Executing tool '{tool_name}' with parameters: {parameters}")
        
        # Special parameter handling for citation_network_analyzer to ensure paper_ids is a list
        if tool_name == 'citation_network_analyzer' and 'paper_ids' in parameters:
            # If paper_ids is a string that looks like a list but isn't, convert it to a list
            if isinstance(parameters['paper_ids'], str):
                # Handle case where it's a string representation of a list
                if parameters['paper_ids'].startswith('[') and parameters['paper_ids'].endswith(']'):
                    try:
                        # Try to parse as JSON
                        import ast
                        parsed_list = ast.literal_eval(parameters['paper_ids'])
                        if isinstance(parsed_list, list):
                            parameters['paper_ids'] = parsed_list
                        else:
                            # If parsing doesn't give a list, convert to single-item list
                            parameters['paper_ids'] = [parameters['paper_ids']]
                    except:
                        # If parsing fails, convert to a single-item list
                        # Clean up the string by removing brackets
                        clean_str = parameters['paper_ids'].strip('[]')
                        # Split by commas and handle quotes
                        items = [item.strip().strip('"\'') for item in clean_str.split(',')]
                        parameters['paper_ids'] = [item for item in items if item]
                else:
                    # It's a single string, convert to a single-item list
                    parameters['paper_ids'] = [parameters['paper_ids']]
                
                log("action", f"Reformatted paper_ids parameter: {parameters['paper_ids']}")
                
            # Ensure the list items are strings, not nested lists or other objects
            if isinstance(parameters['paper_ids'], list):
                parameters['paper_ids'] = [str(item) if not isinstance(item, str) else item for item in parameters['paper_ids']]
        
        # Call the tool using the MCP session
        result = await session.call_tool(tool_name, arguments=parameters)
        
        # Extract the content based on MCP response format
        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                # Extract text from content items
                content_output = [
                    getattr(item, 'text', str(item)) 
                    for item in result.content
                ]
                # Join multiple text items if needed
                if len(content_output) == 1:
                    output = content_output[0]
                else:
                    output = content_output
            else:
                output = getattr(result.content, 'text', str(result.content))
        else:
            output = str(result)
            
        # Attempt to parse JSON if the output is a string and looks like JSON
        if isinstance(output, str):
            try:
                if output.strip().startswith('{') and output.strip().endswith('}'):
                    output = json.loads(output)
            except:
                pass
                
        log("action", f"Tool '{tool_name}' execution completed")
        
        return ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            output=output,
            raw_response=result
        )
        
    except Exception as e:
        log("action", f"Tool execution failed: {e}")
        error_message = f"Error executing {tool_call}: {str(e)}"
        return ToolResult(
            tool_name=tool_name if 'tool_name' in locals() else "unknown",
            parameters=parameters if 'parameters' in locals() else {},
            output={"error": error_message},
            raw_response=None
        )

def format_final_answer(answer: str) -> str:
    """Format the final answer from the decision layer"""
    if answer.startswith("FINAL_ANSWER:"):
        return answer.replace("FINAL_ANSWER:", "").strip()
    return answer 