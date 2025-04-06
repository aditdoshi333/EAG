# Screenshot-Based Drawing Automation

This project demonstrates how to automate drawing tasks in a custom paint application using:
1. Screenshot analysis
2. Colored button detection
3. Dynamic coordinate calculation
4. LLM-driven automation

## Components

- **example2-3_mac_screenshot.py**: Server that provides tools for:
  - Taking screenshots
  - Detecting colored buttons
  - Clicking buttons
  - Drawing rectangles
  - Adding text

- **talk2mcp-2_mac_screenshot.py**: Client that:
  - Uses Gemini LLM to decide what actions to take
  - Executes a sequence of function calls to complete drawing tasks
  - Maintains context of previous actions

## Setup

1. Clone this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Gemini API key:
   ```
   cp .env.example .env
   # Edit .env and add your API key
   ```

## Usage

Run the client:
```
python talk2mcp-2_mac_screenshot.py
```

The client will:
1. Start the server (example2-3_mac_screenshot.py)
2. Use the Gemini API to decide which function to call next
3. Execute the functions to draw a rectangle and add "Hello world" text inside it

## Extending

You can modify the client to:
- Change the text to display
- Add more drawing operations
- Create more complex automation workflows

## Requirements

- macOS (uses macOS-specific screenshot tools)
- Python 3.8+
- Gemini API key 