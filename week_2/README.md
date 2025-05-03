# Page Summarizer Chrome Extension

A Chrome extension that generates concise summaries of web pages.

## Features

- Extracts content from the current webpage
- Sends the content to an AI service for summarization
- Displays a concise summary of the page

## Installation

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top-right corner
4. Click "Load unpacked" and select the extension directory
5. The extension icon should appear in your browser toolbar

## Configuration

Before using the extension, you need to add your API key to the `config.js` file:

1. Open the `config.js` file in the extension directory
2. Replace `"your-api-key-here"` with your actual API key
3. Save the file

## Usage

1. Navigate to any webpage you want to summarize
2. Click the extension icon in the toolbar
3. Click "Summarize This Page"
4. Wait a few seconds for the summary to appear

## Notes

- The extension works best on article or content-heavy pages
- There are token limits, so very long pages may be truncated
- Make sure your API key in config.js is kept private 