import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
import time

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Track iteration state
max_iterations = 10
iteration = 0
steps_performed = []

async def generate_with_timeout(client, prompt, timeout=15, retry_count=0):
    """Generate content with a timeout, using Gemini-2.0-flash"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
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
            return await generate_with_timeout(client, prompt, timeout=new_timeout, retry_count=retry_count + 1)
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        if retry_count < 2:
            print(f"Retrying (Attempt {retry_count + 1} of 3)...")
            return await generate_with_timeout(client, prompt, timeout=timeout, retry_count=retry_count + 1)
        raise

async def main():
    # Reset tracking variables
    global iteration, steps_performed
    iteration = 0
    steps_performed = []
    
    # Get user input (in this case, we'll use a predefined text)
    user_text = "Hello world"
    print(f"User input text: {user_text}")
    
    try:
        # Connect to the MCP server
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3_mac_screenshot.py"]
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

                # Create a simple system prompt with available tools
                print("Creating system prompt...")
                
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
                
                system_prompt = f"""You are a helpful assistant that can display text in a paint application by taking screenshots and analyzing them to detect UI elements.

Available tools:
{tools_description}

You must respond with EXACTLY ONE function call in this format (no additional text):
FUNCTION_CALL: function_name|param1|param2|...

For example:
- FUNCTION_CALL: open_paint
- FUNCTION_CALL: take_screenshot
- FUNCTION_CALL: detect_colored_buttons
- FUNCTION_CALL: click_button|rectangle_button
- FUNCTION_CALL: draw_rectangle|400|300
- FUNCTION_CALL: add_text|Hello world

Your goal is to display the text "{user_text}" inside a rectangle in the paint app.
Follow these steps carefully and in order:
1. Open the paint app
2. Wait a moment (2-3 seconds) for the app to fully load
3. Maximize the paint window for better visibility
4. Take a screenshot to see the current state
5. Detect the colored buttons in the screenshot
6. Click on the rectangle button
7. Wait a moment (1-2 seconds) for the app to process
8. Draw a rectangle (provide width and height, recommended 400x300)
9. Wait a moment (1-2 seconds) for the rectangle to be drawn
10. Take another screenshot
11. Detect the colored buttons again
12. Click on the text button
13. Wait a moment (1-2 seconds) for the app to process
14. Add the text inside the rectangle

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with FUNCTION_CALL:
"""

                # Start iteration loop
                while iteration < max_iterations:
                    print(f"\n--- Step {iteration + 1} ---")
                    
                    # Create context-aware prompt
                    if iteration == 0:
                        current_prompt = f"{system_prompt}\n\nWhat is the first function you should call?"
                    else:
                        # Add history of previous steps
                        history = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps_performed)])
                        current_prompt = f"{system_prompt}\n\nPrevious steps:\n{history}\n\nWhat function should you call next?"
                    
                    # Get LLM's suggestion for next step
                    response = await generate_with_timeout(client, current_prompt)
                    response_text = response.text.strip()
                    print(f"LLM Response: {response_text}")
                    
                    # Extract and validate function call
                    if not response_text.startswith("FUNCTION_CALL:"):
                        print("LLM didn't provide a valid function call. Trying again...")
                        continue
                    
                    # Parse function call
                    _, function_info = response_text.split(":", 1)
                    parts = [p.strip() for p in function_info.split("|")]
                    func_name, params = parts[0], parts[1:]
                    
                    print(f"Function call: {func_name} with parameters {params}")
                    
                    try:
                        # Find the matching tool
                        tool = next((t for t in tools if t.name == func_name), None)
                        if not tool:
                            print(f"ERROR: Unknown tool: {func_name}")
                            steps_performed.append(f"ERROR: Unknown tool: {func_name}")
                            continue

                        # Prepare arguments
                        arguments = {}
                        schema_properties = tool.inputSchema.get('properties', {})
                        
                        for param_name, param_info in schema_properties.items():
                            if not params:  # Check if we have enough parameters
                                raise ValueError(f"Not enough parameters provided for {func_name}")
                                
                            value = params.pop(0)  # Get and remove the first parameter
                            param_type = param_info.get('type', 'string')
                            
                            # Convert the value to the correct type
                            if param_type == 'integer':
                                arguments[param_name] = int(value)
                            elif param_type == 'number':
                                arguments[param_name] = float(value)
                            else:
                                arguments[param_name] = str(value)

                        # Execute the function
                        result = await session.call_tool(func_name, arguments=arguments)
                        
                        # Process result
                        if hasattr(result, 'content') and isinstance(result.content, list):
                            result_text = []
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    result_text.append(item.text)
                            result_str = "\n".join(result_text)
                        else:
                            result_str = str(result)
                        
                        print(f"Result: {result_str}")
                        
                        # Record the step for history
                        step_record = f"Called {func_name}({', '.join(str(v) for v in arguments.values())}) → {result_str.splitlines()[0] if result_str and result_str.splitlines() else 'No result'}"
                        steps_performed.append(step_record)
                        
                        # Add a pause to give the paint app time to update
                        # Different pauses depending on function type
                        if func_name == "open_paint":
                            print("Waiting for paint app to open fully...")
                            await asyncio.sleep(3)
                        elif func_name in ["click_button", "draw_rectangle", "add_text"]:
                            print("Waiting for paint app to process action...")
                            await asyncio.sleep(2)
                        else:
                            await asyncio.sleep(1)
                            
                        # Check if we've completed all necessary steps
                        if func_name == "add_text" and user_text == arguments.get("text", ""):
                            print("\n=== Task Completed ===")
                            print(f"Successfully displayed '{user_text}' in a rectangle.")
                            break
                        
                    except Exception as e:
                        print(f"ERROR: {str(e)}")
                        steps_performed.append(f"ERROR: {str(e)}")
                    
                    # Move to next iteration
                    iteration += 1
                    time.sleep(0.5)
                
                # Output summary of steps
                print("\n=== Summary ===")
                print(f"Total steps performed: {len(steps_performed)}")
                for i, step in enumerate(steps_performed):
                    print(f"Step {i+1}: {step}")

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 