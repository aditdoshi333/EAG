# Shopping Comparison Agent Chrome Extension

A Chrome extension that helps you make informed purchase decisions by comparing products across multiple e-commerce sites using AI-powered analysis.

## Features

- Product search across multiple e-commerce sites (Amazon, Walmart, Best Buy)
- AI-powered analysis of product features and requirements
- Price comparison and tracking
- Review aggregation and sentiment analysis
- Personalized recommendations based on your preferences

## Installation

1. Clone this repository or download the source code
2. Open Chrome and go to `chrome://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the directory containing the extension files

## Setup

1. You'll need an OpenAI API key to use the extension
2. When you first open the extension, you'll be prompted to enter your API key
3. The API key will be securely stored in Chrome's local storage

## Usage

1. Click the extension icon in your Chrome toolbar
2. Enter the product you're looking to buy (e.g., "gaming laptop under $1000")
3. Click "Search" and wait for the analysis
4. Review the results, including:
   - AI analysis of your requirements
   - Price comparisons across sites
   - Product reviews and ratings
   - Personalized recommendations

## Development

The extension is built with:
- HTML/CSS for the UI
- JavaScript for functionality
- OpenAI API for AI-powered analysis
- Chrome Extension APIs for browser integration

## File Structure

```
├── manifest.json          # Extension configuration
├── popup.html            # Main UI
├── popup.js              # Main logic
├── background.js         # Background tasks
├── utils/
│   ├── logger.js        # Logging utility
│   ├── api.js           # OpenAI API integration
│   └── tools.js         # Shopping comparison tools
└── icons/               # Extension icons
```

## Note

This is a prototype version that uses mock data for product searches. In a production environment, you would need to:
1. Implement actual API calls to e-commerce sites
2. Add proper error handling and rate limiting
3. Implement user authentication
4. Add more robust security measures
5. Add proper data caching and storage 