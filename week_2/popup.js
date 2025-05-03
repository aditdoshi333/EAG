document.addEventListener('DOMContentLoaded', function() {
  const summarizeButton = document.getElementById('summarize');
  const loadingDiv = document.getElementById('loading');
  const summaryContainer = document.getElementById('summary-container');
  const summaryDiv = document.getElementById('summary');
  const errorDiv = document.getElementById('error');

  // Summarize current page
  summarizeButton.addEventListener('click', function() {
    if (!CONFIG || !CONFIG.API_KEY || CONFIG.API_KEY === 'your-openai-api-key-here') {
      showError('Please update the config.js file with your API key');
      return;
    }

    // Clear previous results
    hideError();
    summaryDiv.textContent = '';
    summaryContainer.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    // Get current tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      const currentTab = tabs[0];
      
      // Execute content script to extract page content
      chrome.scripting.executeScript({
        target: {tabId: currentTab.id},
        function: extractPageContent
      }, (injectionResults) => {
        if (!injectionResults || !injectionResults[0]) {
          showError('Failed to extract page content');
          loadingDiv.classList.add('hidden');
          return;
        }
        
        const pageContent = injectionResults[0].result;
        const pageTitle = currentTab.title || '';
        
        // Show content length for debugging
        console.log(`Page title: ${pageTitle}`);
        console.log(`Content length: ${pageContent ? pageContent.length : 0} characters`);
        
        // Get summary using API
        getSummary(CONFIG.API_KEY, pageTitle, pageContent);
      });
    });
  });

  function extractPageContent() {
    // Extract useful content from the page
    const article = document.querySelector('article');
    if (article) {
      return article.innerText;
    }
    
    // If no article tag found, get the main content
    const mainContent = document.querySelector('main') || 
                       document.querySelector('.main-content') || 
                       document.querySelector('#content') ||
                       document.querySelector('.content');
    
    if (mainContent) {
      return mainContent.innerText;
    }
    
    // Fallback to body text with some filtering
    const bodyText = document.body.innerText;
    // Limit to reasonable size (API has token limits)
    return bodyText.substring(0, 15000);
  }

  function getSummary(apiKey, pageTitle, pageContent) {
    const endpoint = CONFIG.API_ENDPOINT;
    
    // Prepare the content to be summarized
    let content = `Title: ${pageTitle}\n\nContent: ${pageContent}`;
    
    // Limit content length to avoid token limits
    if (content.length > 15000) {
      content = content.substring(0, 15000) + '...';
    }
    
    // OpenAI API format
    const requestData = {
      model: CONFIG.MODEL,
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant that summarizes web page content concisely."
        },
        {
          role: "user",
          content: `Please provide a concise summary of this web page:\n\n${content}`
        }
      ],
      max_tokens: CONFIG.MAX_TOKENS
    };

    console.log('Sending request to API...');
    
    fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(requestData)
    })
    .then(response => {
      console.log('Response status:', response.status);
      if (!response.ok) {
        return response.text().then(text => {
          console.error('Error response:', text);
          throw new Error(`API request failed with status ${response.status}`);
        });
      }
      return response.json();
    })
    .then(data => {
      console.log('Response data:', data);
      loadingDiv.classList.add('hidden');
      
      if (data.choices && data.choices.length > 0) {
        summaryContainer.classList.remove('hidden');
        summaryDiv.textContent = data.choices[0].message.content.trim();
      } else {
        throw new Error('No summary generated or unexpected response format');
      }
    })
    .catch(error => {
      console.error('Error:', error);
      loadingDiv.classList.add('hidden');
      showError(`Error: ${error.message}`);
    });
  }

  function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
  }

  function hideError() {
    errorDiv.classList.add('hidden');
    errorDiv.textContent = '';
  }
}); 