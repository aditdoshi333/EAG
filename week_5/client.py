import os
import json
import uuid
import datetime
import gradio as gr
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai
from concurrent.futures import TimeoutError

# Load environment variables
load_dotenv()

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize conversation and log history
conversation_history = []
log_history = []

# Create logs directory
os.makedirs("logs", exist_ok=True)

async def generate_with_timeout(model, prompt, timeout=15, retry_count=0):
    """Generate content with a timeout, using Gemini Flash"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            ),
            timeout=timeout
        )
            
        print("LLM generation completed")
        return response
    except TimeoutError:
        print(f"LLM generation timed out! (Attempt {retry_count + 1} of 3)")
        if retry_count < 2:
            new_timeout = timeout * 1.5
            print(f"Retrying with increased timeout: {new_timeout:.1f} seconds")
            return await generate_with_timeout(model, prompt, timeout=new_timeout, retry_count=retry_count + 1)
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        if retry_count < 2:
            print(f"Retrying (Attempt {retry_count + 1} of 3)...")
            return await generate_with_timeout(model, prompt, timeout=timeout, retry_count=retry_count + 1)
        raise

def get_session_id():
    """Generate a unique session ID for logging"""
    return str(uuid.uuid4())

def log_interaction(session_id, user_query, tool_name, tool_input, tool_output, 
                     query_analysis=None, reasoning_type=None, verification=None, fallback_plan=None):
    """Log the interaction details"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "session_id": session_id,
        "user_query": user_query,
        "query_analysis": query_analysis,
        "reasoning_type": reasoning_type,
        "tool_decision": tool_name,
        "tool_input": tool_input,
        "verification": verification,
        "tool_output": tool_output,
        "fallback_plan": fallback_plan
    }
    log_history.append(log_entry)
    
    # Save log to file
    with open(f"logs/{session_id}.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    return log_entry

def format_log_for_display(logs):
    """Format logs for display in the interface"""
    formatted = ""
    for log in logs:
        formatted += f"Timestamp: {log['timestamp']}\n"
        formatted += f"User Query: {log['user_query']}\n"
        
        # Add new fields if available
        if log.get('query_analysis'):
            formatted += f"Query Analysis: {log['query_analysis']}\n"
        if log.get('reasoning_type'):
            formatted += f"Reasoning Type: {log['reasoning_type']}\n"
            
        formatted += f"Tool Selected: {log['tool_decision']}\n"
        formatted += f"Tool Input: {json.dumps(log['tool_input'], indent=2)}\n"
        
        if log.get('verification'):
            formatted += f"Verification: {log['verification']}\n"
            
        formatted += f"Tool Output: {json.dumps(log['tool_output'], indent=2)}\n"
        
        if log.get('fallback_plan'):
            formatted += f"Fallback Plan: {log['fallback_plan']}\n"
            
        formatted += "-" * 50 + "\n"
    return formatted

async def process_query(query, session_id, chatbot, logs_display):
    """Process user query using LLM and appropriate tools"""
    global conversation_history, log_history
    
    print(f"\n--- Processing query: {query} ---")
    
    # Initialize Gemini Flash model
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Add the user query to conversation history
    conversation_history.append({"role": "user", "parts": [query]})
    
    try:
        # Connect to the MCP server
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"],
            env=os.environ.copy()
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create tools description for the prompt
                tools_description = []
                for i, tool in enumerate(tools):
                    try:
                        params = tool.inputSchema
                        desc = getattr(tool, 'description', 'No description available')
                        name = getattr(tool, 'name', f'tool_{i}')
                        
                        if 'properties' in params:
                            param_details = []
                            for param_name, param_info in params['properties'].items():
                                param_type = param_info.get('type', 'unknown')
                                param_details.append(f"{param_name}: {param_type}")
                            params_str = ', '.join(param_details)
                        else:
                            params_str = 'no parameters'

                        tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                        tools_description.append(tool_desc)
                        print(f"Added tool: {tool_desc}")
                    except Exception as e:
                        print(f"Error processing tool {i}: {e}")
                
                tools_description = "\n".join(tools_description)
                
                # Create a prompt with instructions and query - Gemini doesn't support system role
                # So we'll include instructions as part of the main prompt
                prompt_text = f"""You are a Research Assistant Agent designed to help with scientific literature analysis.
Your job is to determine which tool(s) would be most appropriate to use based on the user's query.

Available tools:
{tools_description}

For each user query, you must follow this step-by-step reasoning process:
1. Analyze the query carefully
2. Identify the type of reasoning required (retrieval, analysis, comparison, synthesis, etc.)
3. Select the most appropriate tool(s) - you can use multiple tools when necessary
4. Format the input for each selected tool
5. Verify your selections by asking: "Is this the most efficient way to address this specific query?"
6. Self-check for potential errors or edge cases

Output your decision and reasoning in JSON format as follows:
{{
  "query_analysis": "Brief analysis of what the user is asking for",
  "reasoning_type": "The primary type of reasoning required (retrieval/analysis/comparison/synthesis/etc.)",
  "tools": [
    {{
      "tool": "tool_name1",
      "input": {{"param1": "value1", "param2": "value2"}},
      "reasoning": "Explanation of why this tool was chosen",
      "verification": "Confirmation this tool is optimal or any limitations"
    }},
    {{
      "tool": "tool_name2",
      "input": {{"param1": "value1", "param2": "value2"}},
      "reasoning": "Explanation of why this tool was chosen",
      "verification": "Confirmation this tool is optimal or any limitations"
    }}
  ],
  "fallback_plan": "What to do if the selected tools don't yield satisfactory results"
}}

Important:
- If no tools fully address the query, explain limitations and suggest alternative approaches
- If uncertain between multiple tools, explain the tradeoffs
- For follow-up queries, consider the conversation history to make appropriate tool selections
- If a tool might fail, include contingency steps in your fallback plan

User query: {query}

Think step-by-step before determining which tool(s) would be most appropriate for this query.
"""
                
                # Prepare content for the model - using a single string instead of role-based format
                # Get LLM's tool selection
                response = await generate_with_timeout(model, prompt_text)
                response_text = response.text.strip()
                print(f"LLM Response: {response_text}")
                
                # Remove markdown code block formatting if present
                if response_text.startswith("```"):
                    # Remove opening code block marker (```json or just ```)
                    if response_text.startswith("```json"):
                        response_text = response_text[7:]
                    else:
                        response_text = response_text[3:]
                    
                    # Remove closing code block marker if present
                    if "```" in response_text:
                        response_text = response_text.rsplit("```", 1)[0]
                
                response_text = response_text.strip()
                print(f"Cleaned response for parsing: {response_text}")
                
                try:
                    # Parse the JSON response
                    response_json = json.loads(response_text)
                    
                    # Extract fields from the enhanced format
                    query_analysis = response_json.get("query_analysis", "")
                    reasoning_type = response_json.get("reasoning_type", "")
                    fallback_plan = response_json.get("fallback_plan", "")
                    
                    # Handle both old format (single tool) and new format (multiple tools)
                    if "tool" in response_json:
                        # Old format - single tool
                        tool_selections = [{
                            "tool": response_json["tool"],
                            "input": response_json["input"],
                            "reasoning": response_json["reasoning"],
                            "verification": response_json.get("verification", "")
                        }]
                    else:
                        # New format - multiple tools
                        tool_selections = response_json.get("tools", [])
                    
                    # Store all tool results
                    all_tool_results = []
                    formatted_outputs = []
                    
                    # Include the initial analysis in the output
                    analysis_text = ""
                    if query_analysis:
                        analysis_text += f"📋 **Query Analysis**:\n{query_analysis}\n\n"
                    if reasoning_type:
                        analysis_text += f"🧠 **Reasoning Type**:\n{reasoning_type}\n\n"
                    
                    if analysis_text:
                        formatted_outputs.append(analysis_text)
                    
                    # Execute each tool in sequence
                    for i, tool_selection in enumerate(tool_selections):
                        tool_name = tool_selection["tool"]
                        tool_input = tool_selection["input"]
                        reasoning = tool_selection["reasoning"]
                        verification = tool_selection.get("verification", "")
                        
                        print(f"Selected tool {i+1}: {tool_name}")
                        print(f"Tool input: {tool_input}")
                        print(f"Reasoning: {reasoning}")
                        
                        # Find the matching tool
                        tool = next((t for t in tools if t.name == tool_name), None)
                        if not tool:
                            error_message = f"ERROR: Unknown tool: {tool_name}"
                            print(error_message)
                            formatted_outputs.append(f"❌ {error_message}")
                            continue
                        
                        # Execute the tool
                        print(f"Executing tool: {tool_name}")
                        result = await session.call_tool(tool_name, arguments=tool_input)
                        
                        # Process the result
                        if hasattr(result, 'content') and isinstance(result.content, list):
                            result_text = []
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    result_text.append(item.text)
                            result_str = "\n".join(result_text)
                            
                            try:
                                # Try to parse the result as JSON
                                tool_output = json.loads(result_str)
                            except json.JSONDecodeError:
                                tool_output = {"raw_result": result_str}
                        else:
                            tool_output = {"error": "No content in tool response"}
                        
                        print(f"Tool output: {tool_output}")
                        
                        # Log the interaction
                        log_interaction(session_id, query, tool_name, tool_input, tool_output, 
                                         query_analysis=query_analysis, reasoning_type=reasoning_type, verification=verification, fallback_plan=fallback_plan)
                        
                        # Add to results collection
                        all_tool_results.append({
                            "tool_name": tool_name,
                            "reasoning": reasoning,
                            "verification": verification,
                            "output": tool_output
                        })
                        
                        # Format individual tool output
                        tool_output_text = f"🔍 **Tool**: {tool_name}\n\n"
                        tool_output_text += f"**Reasoning**: {reasoning}\n\n"
                        if verification:
                            tool_output_text += f"**Verification**: {verification}\n\n"
                        
                        # Format the tool output in a more readable way
                        if isinstance(tool_output, dict) and "papers" in tool_output:
                            # Special formatting for paper results
                            papers = tool_output.get("papers", [])
                            tool_output_text += f"Found {len(papers)} papers"
                            
                            for i, paper in enumerate(papers[:3], 1):  # Show first 3 papers max
                                tool_output_text += f"\n\n{i}. **{paper.get('title')}**\n"
                                tool_output_text += f"   Authors: {', '.join(paper.get('authors', []))[:100]}...\n"
                                tool_output_text += f"   Year: {paper.get('year')}"
                            
                            if len(papers) > 3:
                                tool_output_text += f"\n\n...and {len(papers) - 3} more papers."
                        else:
                            # Add condensed result (limit size)
                            output_str = json.dumps(tool_output, ensure_ascii=False)
                            if len(output_str) > 500:
                                tool_output_text += f"Results: {output_str[:500]}...(truncated)"
                            else:
                                tool_output_text += f"Results: {output_str}"
                        
                        formatted_outputs.append(tool_output_text)
                    
                    # Add fallback plan if available
                    if fallback_plan:
                        formatted_outputs.append(f"🔄 **Fallback Plan**:\n{fallback_plan}")
                    
                    # Generate final summary using the LLM if we have results from multiple tools
                    if len(all_tool_results) > 1:
                        summary_prompt = f"""Based on the following tool outputs, provide a concise summary that integrates the findings.
                        
User query: {query}

Query analysis: {query_analysis}
Reasoning type: {reasoning_type}

Tool results:
{json.dumps(all_tool_results, indent=2, ensure_ascii=False)}

Generate a concise summary (max 300 words) that synthesizes these results and directly answers the user's query.
Focus on the most important insights and connections between the different tools' outputs.
"""
                        summary_response = await generate_with_timeout(model, summary_prompt)
                        summary_text = summary_response.text.strip()
                        
                        # Add the summary to our formatted response
                        response_to_user = "I've used multiple tools to answer your query:\n\n"
                        response_to_user += "\n\n---\n\n".join(formatted_outputs)
                        response_to_user += "\n\n---\n\n### Summary\n" + summary_text
                    else:
                        # Only one tool was used, no need for additional summary
                        response_to_user = "I've used a tool to answer your query:\n\n"
                        response_to_user += "\n\n---\n\n".join(formatted_outputs)
                    
                    # Add assistant response to conversation history
                    conversation_history.append({"role": "model", "parts": [response_to_user]})
                    
                    # Update the chat interface
                    chatbot.append((query, response_to_user))
                    logs_display = format_log_for_display(log_history)
                    
                except json.JSONDecodeError as e:
                    error_message = f"Error parsing LLM response: {e}. The response was not valid JSON."
                    print(error_message)
                    chatbot.append((query, error_message))
                
                except Exception as e:
                    error_message = f"Error processing tool: {str(e)}"
                    print(error_message)
                    chatbot.append((query, error_message))
                
                return chatbot, logs_display
                
    except Exception as e:
        error_message = f"Error connecting to MCP server: {str(e)}"
        print(error_message)
        chatbot.append((query, error_message))
        return chatbot, logs_display

def create_interface():
    """Create the Gradio interface"""
    # Initialize session
    session_id = get_session_id()
    
    with gr.Blocks(title="Research Assistant Agent") as interface:
        gr.Markdown("# Research Assistant Agent for Scientific Literature Analysis")
        gr.Markdown("Ask questions about scientific papers and datasets to discover insights and connections.")
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=500)
                query_input = gr.Textbox(
                    placeholder="Ask a research question...", 
                    label="Your Query"
                )
                submit_btn = gr.Button("Submit")
            
            with gr.Column(scale=1):
                logs_display = gr.Textbox(
                    label="Interaction Logs",
                    value="",
                    lines=25,
                    max_lines=25
                )
        
        def on_submit(query, chatbot, logs):
            return asyncio.run(process_query(query, session_id, chatbot, logs))
        
        submit_btn.click(
            on_submit,
            inputs=[query_input, chatbot, logs_display],
            outputs=[chatbot, logs_display]
        )
        
        query_input.submit(
            on_submit,
            inputs=[query_input, chatbot, logs_display],
            outputs=[chatbot, logs_display]
        )
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(share=True) 