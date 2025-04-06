# Screenshot-Based Drawing Automation

This project demonstrates how to automate drawing tasks in a custom paint application using:
1. Screenshot analysis
2. Colored button detection
3. Dynamic coordinate calculation
4. LLM-driven automation
5. Email notifications

## Components

- **example2-3_mac_screenshot.py**: Server that provides tools for:
  - Taking screenshots
  - Detecting colored buttons
  - Clicking buttons
  - Drawing rectangles
  - Adding text
  - Sending emails with screenshots

- **talk2mcp-2_mac_screenshot.py**: Client that:
  - Uses Gemini LLM to decide what actions to take
  - Executes a sequence of function calls to complete drawing tasks
  - Maintains context of previous actions
  - Sends email notifications when complete

- **mac_paint_colored.py**: Custom paint application with:
  - Simple drawing interface
  - Rectangle drawing tool
  - Text adding capability

## Setup

1. Clone this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your credentials:
   ```
   cp .env.example .env
   # Edit .env and add your API key and Gmail credentials
   ```

### Gmail Setup for Email Notifications
To use the email notification feature, you need to:
1. Enable 2-Step Verification on your Google account
2. Generate an App Password:
   - Go to your Google Account > Security
   - Navigate to App Passwords (under 2-Step Verification)
   - Select "Mail" and "Other" (name it "Screenshot Automator")
   - Copy the 16-character password to your .env file

## Usage

Run the client:
```
python talk2mcp-2_mac_screenshot.py
```

The client will:
1. Start the server (example2-3_mac_screenshot.py)
2. Use the Gemini API to decide which function to call next
3. Execute the functions to draw a rectangle and add "Hello world" text inside it
4. Send an email with the screenshot attached

## Extending

You can modify the client to:
- Change the text to display
- Add more drawing operations
- Create more complex automation workflows
- Customize email notifications

## Requirements

- macOS (uses macOS-specific screenshot tools)
- Python 3.8+
- Gemini API key
- Gmail account with App Password 