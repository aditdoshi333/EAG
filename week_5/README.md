# Research Assistant Agent

A multi-tool agent that helps researchers analyze scientific papers and datasets, identifying connections between research fields that might not be obvious.

## Architecture

The system consists of two main components:

1. **MCP Server**: Backend server that hosts various research tools using FastMCP
2. **Client**: Gradio interface that uses Gemini Flash to determine which tools to use and communicates with the MCP server

### MCP Server Tools

- **paper_retrieval_tool**: Fetches scientific papers based on keywords, authors, or topics from arXiv
- **dataset_explorer_tool**: Analyzes and extracts insights from datasets found on data.gov
- **citation_network_analyzer**: Maps relationships between papers and identifies research clusters using Semantic Scholar API
- **concept_extractor**: Identifies key concepts and terminology across papers using Gemini Flash LLM
- **cross_domain_connector**: Finds unexpected connections between different research domains using LLM analysis

## Setup

### Prerequisites

- Python 3.9+
- Google Gemini API key

### Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following content:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

## Running the System

1. Start the client, which will automatically connect to the MCP server:
   ```
   python client.py
   ```

2. Open the Gradio interface in your browser (the URL will be displayed in the terminal)

## How it Works

1. User submits a research query through the Gradio interface
2. The client establishes a connection to the MCP server
3. The client retrieves the available tools from the MCP server
4. Google Gemini Flash analyzes the query following a structured reasoning process:
   - Analyzes what the query is asking for
   - Identifies the type of reasoning required (retrieval, analysis, comparison, synthesis)
   - Selects the most appropriate tool(s) to answer the query
   - Verifies selections and creates a fallback plan
5. The client executes the selected tools sequentially on the MCP server
6. Each tool processes its specific part of the request, integrating with external APIs and using Gemini Flash for advanced analysis
7. If multiple tools are used, the system generates a final summary that integrates findings from all tools
8. Results are returned to the client and displayed to the user in a structured format
9. All interactions are logged for review with detailed reasoning information

## Example Queries

- "Find papers on protein folding published in the last 2 years"
- "Analyze the climate trends dataset and show temperature correlations"
- "Map the citation network for papers on quantum computing in machine learning"
- "Extract key concepts from papers about drug discovery"
- "Find connections between NLP research and bioinformatics"

## External APIs Used

This agent integrates with several external services:

- **arXiv API**: For retrieving scientific paper metadata
- **data.gov API**: For searching and retrieving dataset information
- **Semantic Scholar API**: For citation network analysis
- **Google Gemini**: For advanced concept extraction and domain connection analysis 

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