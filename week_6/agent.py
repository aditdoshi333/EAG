import os
import asyncio
import time
import uuid
import datetime
import json
import re
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from perception import extract_perception, PerceptionResult
from memory import MemoryManager, MemoryItem
from decision import generate_plan
from action import execute_tool, format_final_answer
from models import UserQuery, AgentResponse
import google.generativeai as genai

def log(stage: str, msg: str):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

# Maximum number of reasoning steps before giving a final answer
MAX_STEPS = 5

class ResearchAssistantAgent:
    def __init__(self):
        self.memory = MemoryManager()
        self.previous_tool_calls = set()  # Keep track of previously used tool+param combinations
        
    async def process_query(self, user_query: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process a user query through the perception-memory-decision-action loop"""
        if not session_id:
            session_id = f"session-{int(time.time())}"
            
        log("agent", f"Processing query: {user_query}")
        
        # Store the query in memory
        self.memory.add(MemoryItem(
            text=user_query,
            type="user_query",
            session_id=session_id
        ))
        
        # Connect to the MCP server
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_server.py"],
            env=os.environ.copy()
        )

        try:
            async with stdio_client(server_params) as (read, write):
                log("agent", "Established connection to MCP server")
                
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Get available tools
                    tools_result = await session.list_tools()
                    tools = tools_result.tools
                    
                    tool_descriptions = "\n".join([
                        f"- {tool.name}: {getattr(tool, 'description', 'No description')}"
                        for tool in tools
                    ])
                    
                    log("agent", f"Loaded {len(tools)} tools")
                    
                    # Begin reasoning loop
                    original_query = user_query
                    step = 0
                    should_force_summary = False
                    consecutive_repeats = 0
                    
                    while step < MAX_STEPS and not should_force_summary:
                        log("loop", f"Starting step {step + 1}/{MAX_STEPS}")
                        
                        # 1. Perception Layer - Understanding Input
                        perception = extract_perception(user_query)
                        log("perception", f"Intent: {perception.intent}, Tool hint: {perception.tool_hint}")
                        
                        # 2. Memory Layer - Retrieving Relevant Context
                        retrieved_memories = self.memory.retrieve(
                            query=user_query,
                            top_k=5,  # Increase to get more context
                            session_filter=session_id
                        )
                        log("memory", f"Retrieved {len(retrieved_memories)} relevant memories")
                        
                        # After first step, explicitly ask for synthesis if we've gathered information
                        if step > 0 and retrieved_memories:
                            tool_outputs = [m for m in retrieved_memories if m.type == "tool_output"]
                            if len(tool_outputs) >= 2:
                                # Force a summarization step by modifying the query
                                user_query = f"Original query: {original_query}\nI've collected multiple pieces of information. Please provide a FINAL_ANSWER that synthesizes what we've learned so far."
                        
                        # 3. Decision-Making Layer - Planning Next Step
                        plan = generate_plan(perception, retrieved_memories, tool_descriptions)
                        log("decision", f"Generated plan: {plan}")
                        
                        # If the plan is a final answer, return it
                        if plan.startswith("FINAL_ANSWER:"):
                            final_answer = format_final_answer(plan)
                            
                            # Save the response to memory
                            self.memory.add(MemoryItem(
                                text=final_answer,
                                type="agent_response",
                                user_query=original_query,
                                session_id=session_id
                            ))
                            
                            return AgentResponse(
                                response_text=final_answer,
                                tool_used=None,
                                data=None
                            )
                            
                        # Check for repeated tool calls
                        tool_call_key = plan.strip()
                        if tool_call_key in self.previous_tool_calls:
                            consecutive_repeats += 1
                            log("agent", f"Detected repeated tool call: {tool_call_key} (repeat #{consecutive_repeats})")
                            
                            # If we've repeated the same call 2+ times, force a summary
                            if consecutive_repeats >= 2:
                                log("agent", "Too many repeated tool calls, forcing summary")
                                should_force_summary = True
                                break
                        else:
                            consecutive_repeats = 0
                            self.previous_tool_calls.add(tool_call_key)
                        
                        # 4. Action Layer - Execute the Tool
                        try:
                            result = await execute_tool(session, tools, plan)
                            log("action", f"Tool result: {result.tool_name} returned data")
                            
                            # Check if result is empty or failed
                            has_useful_results = True
                            if result.output:
                                # Check if the output has empty results
                                if isinstance(result.output, dict):
                                    # Check specific fields that might indicate emptiness
                                    if ('papers' in result.output and len(result.output.get('papers', [])) == 0) or \
                                       ('network' in result.output and len(result.output.get('network', {}).get('nodes', [])) == 0):
                                        has_useful_results = False
                                        log("action", f"Tool {result.tool_name} returned empty results")
                            else:
                                has_useful_results = False
                            
                            # Store tool result in memory
                            self.memory.add(MemoryItem(
                                text=str(result.output)[:1000],  # Limit length for storage
                                type="tool_output",
                                tool_name=result.tool_name,
                                user_query=original_query,
                                session_id=session_id
                            ))
                            
                            # Update query for next iteration
                            if has_useful_results:
                                user_query = f"Original query: {original_query}\nPrevious tool result: {str(result.output)[:500]}\nWhat should I do next?"
                            else:
                                user_query = f"Original query: {original_query}\nPrevious tool {result.tool_name} returned empty results. Try a different approach or provide a final answer."
                            
                        except Exception as e:
                            log("error", f"Tool execution failed: {e}")
                            return AgentResponse(
                                response_text=f"I'm sorry, I encountered an error: {str(e)}",
                                tool_used=None,
                                data={"error": str(e)}
                            )
                        
                        step += 1
                    
                    # Create a synthetic prompt to summarize findings
                    log("agent", "Creating final summary")
                    
                    # Retrieve all relevant info from this session
                    all_memories = self.memory.retrieve(
                        query=original_query,
                        session_filter=session_id,
                        top_k=10  # Get more items for a better summary
                    )
                    
                    # Extract useful information from tool outputs
                    paper_titles = []
                    paper_ids = []
                    topics = []
                    useful_data = []
                    used_tools = set()
                    
                    for item in all_memories:
                        if item.type == "tool_output" and item.tool_name:
                            used_tools.add(item.tool_name)
                            try:
                                # Try to extract main content from the tool output
                                if item.tool_name == "paper_retrieval_tool":
                                    # Try to extract titles if possible
                                    title_matches = re.findall(r'"title":\s*"([^"]+)"', item.text)
                                    if title_matches:
                                        for title in title_matches[:3]:
                                            if title not in paper_titles:
                                                paper_titles.append(title)
                                                useful_data.append(f"Found paper: {title}")
                                    
                                    # Extract paper IDs
                                    id_matches = re.findall(r'"id":\s*"([^"]+)"', item.text)
                                    if id_matches:
                                        for paper_id in id_matches:
                                            if paper_id not in paper_ids:
                                                paper_ids.append(paper_id)
                                    
                                    # Extract topics/keywords
                                    if "keywords" in item.text:
                                        keyword_matches = re.findall(r'"keywords":\s*\[(.*?)\]', item.text)
                                        if keyword_matches:
                                            extracted_keywords = re.findall(r'"([^"]+)"', keyword_matches[0])
                                            topics.extend([k for k in extracted_keywords if k not in topics])
                            except Exception as e:
                                log("error", f"Error extracting data: {e}")
                                # If parsing fails, just use the raw text
                                useful_data.append(f"Data from {item.tool_name}: {item.text[:100]}...")
                    
                    # Determine the topic from the query and paper titles
                    main_topic = original_query
                    for word in ["tell me about", "what is", "explain", "information on", "details about"]:
                        main_topic = main_topic.replace(word, "").strip()
                    
                    # If we have useful data or if we identified the topic, get information 
                    final_response = ""
                    
                    # Get direct knowledge about the topic even if we have no paper data
                    try:
                        knowledge_prompt = f"""
As a research assistant, I need to provide information about: {main_topic}

Here's what I already know:
- User query: {original_query}
{"- Found papers on this topic: " + ", ".join(paper_titles[:3]) if paper_titles else "- No specific papers found on this topic"}
{"- Related topics/keywords: " + ", ".join(topics[:5]) if topics else ""}

Please provide:
1. A comprehensive explanation about {main_topic} (what it is, key concepts, importance)
2. Current state of research (main approaches, challenges)
3. Applications and significance 

Keep the information factual, educational, and well-organized.
"""
                        log("knowledge", f"Getting topic knowledge for: {main_topic}")
                        model = genai.GenerativeModel('gemini-2.0-flash')
                        knowledge_response = model.generate_content(knowledge_prompt)
                        topic_knowledge = knowledge_response.text.strip()
                        
                        # Now generate a final response that combines tool results with direct knowledge
                        if useful_data:
                            # If we have papers or other tool results
                            final_prompt = f"""
I need to provide a research assistant response about: {main_topic}

Based on my search, I found:
{os.linesep.join(useful_data)}

And here's additional information about the topic:
{topic_knowledge[:1500]}

Please provide a well-structured, helpful response that:
1. Acknowledges what was found from my search tools
2. Provides comprehensive information about {main_topic}
3. Maintains an educational, informative tone

The response should be useful even if the search tools didn't return complete information.
"""
                        else:
                            # If we have no tool results, just use the topic knowledge
                            final_prompt = f"""
I need to provide a research assistant response about: {main_topic}

My search tools didn't return specific results, but I can provide general information:
{topic_knowledge[:2000]}

Please generate a helpful, educational response about {main_topic} that:
1. Acknowledges that specific search results weren't available
2. Provides valuable information about the topic
3. Suggests what other approaches might be helpful

The response should be useful and informative despite limited search results.
"""
                        
                        summary_response = model.generate_content(final_prompt)
                        final_response = summary_response.text.strip()
                        
                    except Exception as e:
                        log("error", f"Failed to generate knowledge-based response: {e}")
                        if useful_data:
                            # Fallback when we have some data but knowledge generation failed
                            final_response = f"Based on my research about {main_topic}, I found several relevant papers including {', '.join(paper_titles[:2]) if paper_titles else 'some scientific articles'}. However, I wasn't able to extract comprehensive information from these sources. I'd recommend trying a more specific query or exploring alternative research databases for more detailed information."
                        else:
                            # Complete fallback
                            final_response = f"I attempted to research information about {main_topic}, but I wasn't able to find sufficient data through my available tools. This topic might be very specialized or not well-represented in the research databases I have access to. You might try rephrasing your query or exploring specialized academic databases for more information."
                    
                    # Save the response to memory
                    self.memory.add(MemoryItem(
                        text=final_response,
                        type="agent_response",
                        user_query=original_query,
                        session_id=session_id
                    ))
                    
                    log("agent", "Returning final summary")
                    return AgentResponse(
                        response_text=final_response,
                        tool_used=None,
                        data={"reached_max_steps": True}
                    )
                    
        except Exception as e:
            log("error", f"Agent processing error: {e}")
            return AgentResponse(
                response_text=f"I'm sorry, but I encountered an error while processing your request: {str(e)}",
                tool_used=None,
                data={"error": str(e)}
            )

async def main():
    agent = ResearchAssistantAgent()
    
    print("\n🔍 Research Assistant Agent\n")
    query = input("What would you like to know? ")
    
    session_id = f"session-{int(time.time())}"
    response = await agent.process_query(query, session_id)
    
    print("\n🤖 Response:")
    print(response.response_text)

if __name__ == "__main__":
    asyncio.run(main()) 