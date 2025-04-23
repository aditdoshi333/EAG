import os
import json
import uuid
import datetime
import gradio as gr
import asyncio
from dotenv import load_dotenv
import time

from agent import ResearchAssistantAgent, log
from models import UserQuery, AgentResponse

# Load environment variables
load_dotenv()

# Initialize conversation and log history
conversation_history = []
log_history = []

# Create logs directory
os.makedirs("logs", exist_ok=True)

def get_session_id():
    """Generate a unique session ID for logging"""
    return str(uuid.uuid4())

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
    """Process user query using our agent architecture"""
    global conversation_history, log_history
    
    print(f"\n--- Processing query: {query} ---")
    
    # Add the user query to conversation history
    conversation_history.append({"role": "user", "parts": [query]})
    
    # Create a copy of the chatbot list that we can modify
    updated_chatbot = list(chatbot)
    
    try:
        # Initialize the agent
        agent = ResearchAssistantAgent()
        
        # Process the query
        response = await agent.process_query(query, session_id)
        
        # Add the response to conversation history
        conversation_history.append({"role": "assistant", "parts": [response.response_text]})
        
        # Update the chatbot UI with a proper tuple
        updated_chatbot.append((query, response.response_text))
        
        # Return the updated chatbot and logs
        return updated_chatbot, logs_display
        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(error_message)
        conversation_history.append({"role": "assistant", "parts": [error_message]})
        updated_chatbot.append((query, error_message))
        return updated_chatbot, logs_display

def create_interface():
    """Create the Gradio interface"""
    with gr.Blocks(title="Research Assistant Agent", theme=gr.themes.Soft()) as interface:
        gr.HTML("<h1 style='text-align: center; margin-bottom: 1rem'>Research Assistant Agent</h1>")
        gr.HTML("<p style='text-align: center; margin-bottom: 2rem'>An AI-powered research assistant to help with scientific literature analysis</p>")
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    [],
                    elem_id="chatbot",
                    show_label=False
                )
                
                with gr.Row():
                    user_input = gr.Textbox(
                        show_label=False,
                        placeholder="Ask me something about scientific research...",
                        container=False
                    )
                    submit_btn = gr.Button("Send", variant="primary")
                
            with gr.Column(scale=1):
                logs = gr.Textbox(
                    label="Agent Logs",
                    placeholder="Logs will appear here...",
                    interactive=False,
                    lines=20,
                    max_lines=30
                )
        
        session_id = get_session_id()
        
        def on_submit(query, chatbot, logs):
            if not query:
                return chatbot, ""
            
            try:
                updated_chatbot, _ = asyncio.run(process_query(query, session_id, chatbot, logs))
                return updated_chatbot, ""
            except Exception as e:
                error = f"Error: {str(e)}"
                print(error)
                chatbot.append((query, error))
                return chatbot, ""
        
        submit_btn.click(
            on_submit,
            inputs=[user_input, chatbot, logs],
            outputs=[chatbot, user_input]
        )
        
        user_input.submit(
            on_submit,
            inputs=[user_input, chatbot, logs],
            outputs=[chatbot, user_input]
        )
        
    return interface

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True) 