# Research Assistant Agent

An AI-powered research assistant for scientific literature analysis.

## Overview

This project implements a research assistant agent that helps with scientific literature analysis. The agent can retrieve papers, explore datasets, analyze citation networks, extract concepts, and find connections between research domains.

## Architecture

The project follows a modular, layered architecture:

1. **Perception Layer** - Understanding Input
   - Analyzes user input to extract intent, entities, and reasoning type
   - Determines appropriate tools for the task
   - Uses natural language understanding to identify the core information needs
   - Extracts relevant keywords and entities for tool parameter preparation

2. **Memory Layer** - Remembering Context
   - Stores conversation history and tool outputs
   - Retrieves relevant information for decision-making
   - Maintains session-based persistence for coherent multi-turn interactions
   - Logs interaction details for debugging and improvement

3. **Decision-Making Layer** - Planning Next Step
   - Generates plans based on perception and memory
   - Decides when to use tools or provide a final answer
   - Implements sophisticated heuristics to avoid repeated or unproductive tool calls
   - Provides targeted guidance based on previous results and query context

4. **Action Layer** - Execution
   - Executes the selected tools
   - Formats results for user consumption
   - Ensures proper parameter formatting for reliable tool execution
   - Includes robust error handling and recovery strategies

### Advanced Features

The architecture includes several advanced capabilities:

#### Empty Results Detection and Handling
- Detects when tools return empty or insufficient results
- Avoids repeating tool calls that previously returned empty results
- Suggests alternative tools that might be more effective
- Provides informative responses even when research tools fail

#### Direct Knowledge Integration
- Supplements tool-based research with direct LLM knowledge
- Extracts the main topic from user queries to generate targeted knowledge prompts
- Combines tool outputs with general knowledge for comprehensive responses
- Provides valuable information even when structured data sources are limited

#### Parameter Optimization
- Sophisticated parameter parsing and validation
- Handles various string-to-list conversions for robust tool execution
- Ensures valid parameter formatting to prevent execution errors
- Detailed logging of parameter transformations for debugging

#### Adaptive Tool Selection
- Tracks previously used tools to avoid repetition
- Recommends alternative tools when previous ones fail
- Topic-specific guidance for first-time tool selection
- Encourages synthesizing information after multiple tool calls

## Files

- `models.py` - Data models using Pydantic for validation
- `perception.py` - Understanding and structuring user input
- `memory.py` - Storing and retrieving contextual information
- `decision.py` - Planning and determining next steps
- `action.py` - Executing tools and formatting results
- `agent.py` - Integrating all layers into a coherent agent
- `mcp_server.py` - Server with research tools
- `client.py` - Gradio web interface for interacting with the agent

## Layer Implementation Details

### Perception Layer (`perception.py`)
The perception layer extracts structured data from unstructured user inputs:
- Extracts intents to understand what the user is trying to accomplish
- Identifies entities (keywords, topics, named entities) relevant to the query
- Suggests appropriate tools based on query analysis
- Determines the type of reasoning required (retrieval, analysis, comparison, synthesis)

### Memory Layer (`memory.py`)
The memory layer provides context-aware information retrieval:
- Stores conversation history with timestamps and session IDs
- Records tool outputs for later reference and analysis
- Implements recency-based retrieval for relevant context
- Supports filtering by memory type, tags, or session ID

### Decision-Making Layer (`decision.py`)
The decision layer determines the next best action:
- Analyzes previous tool results to avoid repetition
- Detects empty or failed tool calls and suggests alternatives
- Leverages contextual understanding to select appropriate tools
- Decides when to synthesize information into a final answer

### Action Layer (`action.py`)
The action layer executes tools and processes their outputs:
- Implements robust parameter validation and formatting
- Handles different response formats from various tools
- Provides consistent error handling and recovery
- Formats tool results for further processing

## Setup

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```
GOOGLE_API_KEY=your_gemini_api_key
```

3. Run the agent:
```
python agent.py
```

4. Or run the web interface:
```
python client.py
```

## Tools

The agent has access to the following tools:

- **Paper Retrieval Tool** - Searches for scientific papers by keywords, authors, topics, or year
- **Dataset Explorer Tool** - Analyzes and extracts insights from datasets
- **Citation Network Analyzer** - Maps relationships between papers and identifies research clusters
- **Concept Extractor** - Identifies key concepts and terminology across papers
- **Cross-Domain Connector** - Finds unexpected connections between different research domains

## External APIs Used

This agent integrates with several external services:

- **arXiv API**: For retrieving scientific paper metadata
- **data.gov API**: For searching and retrieving dataset information
- **Semantic Scholar API**: For citation network analysis
- **Google Gemini**: For advanced concept extraction and domain connection analysis 

## Workflow and Reasoning Process

The complete research workflow follows these steps:

1. **Query Understanding**: The perception layer extracts intent, entities, and reasoning type
2. **Memory Retrieval**: The system checks for relevant context from previous interactions
3. **Tool Selection**: The decision layer determines which tool(s) to use based on the query
4. **Tool Execution**: The action layer runs the selected tools with appropriate parameters
5. **Result Analysis**: The system analyzes tool outputs and detects empty/failed results
6. **Knowledge Integration**: Direct knowledge is obtained when needed to supplement tool results
7. **Response Synthesis**: A comprehensive response is generated combining tool outputs and knowledge
8. **Memory Storage**: The interaction and results are stored for future reference

This process creates a robust research assistant that can effectively handle a wide range of queries, even when faced with limited data or empty tool results.

## Prompt Engineering

Our system uses a carefully designed prompt structure that guides the LLM to make better tool selection decisions. The prompt has been evaluated against the following criteria:

### Prompt Evaluation Report

**Explicit Reasoning Instructions** ✅
- The prompt explicitly instructs "Think step-by-step" at the end
- Provides a numbered sequential reasoning process (steps 1-6)
- Includes analysis before action, promoting careful consideration

**Structured Output Format** ✅
- Enforces a specific, detailed JSON structure with clearly defined fields
- The format is consistent, comprehensive, and machine-parsable
- Includes nested structure for tool-specific information

**Separation of Reasoning and Tools** ✅
- Clear distinction between reasoning process and tool selection/execution
- Separate fields for query analysis, tool selection, and verification

**Conversation Loop Support** ✅
- Explicitly mentions handling "follow-up queries"
- Instructs to consider "conversation history" for subsequent interactions

**Instructional Framing** ✅
- Provides a comprehensive JSON template as an example
- Clearly defines the expected structure and includes descriptive field explanations

**Internal Self-Checks** ✅
- Includes explicit verification step: "Verify your selections by asking..."
- Requires a "verification" field for each tool to confirm appropriateness
- Explicit instruction to "Self-check for potential errors or edge cases"

**Reasoning Type Awareness** ✅
- Explicitly asks to "Identify the type of reasoning required"
- Provides examples of reasoning types (retrieval, analysis, comparison, synthesis)
- Includes dedicated "reasoning_type" field in the output structure

**Error Handling or Fallbacks** ✅
- Includes a dedicated "fallback_plan" field in the output structure
- Explicit instructions for handling cases where no tools fully address the query
- Guidance for uncertainty cases and tool failures

**Overall Clarity** ✅
- The prompt is well-organized, with logical flow from analysis to output
- Instructions are specific, detailed, and comprehensive
- Balances structure with flexibility for different query types 