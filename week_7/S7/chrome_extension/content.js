// Function to extract text content from the page
function extractPageContent() {
    console.log('[WebPageIndexer] Extracting page content...');
    try {
        // Remove unwanted elements
        const unwantedSelectors = [
            'script', 'style', 'nav', 'footer', 'header',
            'iframe', 'noscript', 'svg', 'canvas',
            'button', 'input', 'select', 'textarea',
            // Add more UI elements to filter out
            '[role="navigation"]', '[role="banner"]', '[role="complementary"]',
            '.navigation', '.navbar', '.header', '.footer',
            '.sidebar', '.menu', '.banner', '.advertisement',
            // Common session/notification messages
            '[class*="notification"]', '[class*="alert"]', '[class*="message"]',
            '[id*="notification"]', '[id*="alert"]', '[id*="message"]',
            // Skip to content links
            'a[href="#content"]', 'a[href="#main"]',
            // Session-related elements
            '[class*="session"]', '[id*="session"]',
            '[class*="login"]', '[id*="login"]',
            '[class*="sign"]', '[id*="sign"]'
        ];
        
        const clone = document.cloneNode(true);
        
        // Remove unwanted elements
        unwantedSelectors.forEach(selector => {
            const elements = clone.querySelectorAll(selector);
            elements.forEach(el => el.remove());
        });

        // Get text content
        let text = clone.body.innerText;
        
        // Clean up whitespace and common UI messages
        text = text
            .replace(/\s+/g, ' ')
            .replace(/Skip to content/g, '')
            .replace(/You signed in with another tab or window\./g, '')
            .replace(/You signed out in another tab or window\./g, '')
            .replace(/You switched accounts on another tab\./g, '')
            .replace(/Reload to refresh your session\./g, '')
            .replace(/Click here to refresh your session\./g, '')
            .trim();
        
        // Remove any remaining empty lines
        text = text.split('\n')
            .filter(line => line.trim().length > 0)
            .join('\n');
        
        console.log(`[WebPageIndexer] Extracted ${text.length} characters of content`);
        return text;
    } catch (error) {
        console.error('[WebPageIndexer] Error extracting content:', error);
        return '';
    }
}

// Function to index the current page
async function indexCurrentPage() {
    try {
        console.log('[WebPageIndexer] Starting page indexing...');
        const content = extractPageContent();
        const url = window.location.href;

        if (!content) {
            console.error('[WebPageIndexer] No content extracted from page');
            return;
        }

        console.log(`[WebPageIndexer] Sending content to server for URL: ${url}`);
        const response = await fetch('http://localhost:5001/index', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                content: content
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('[WebPageIndexer] Page indexed successfully:', result);
    } catch (error) {
        console.error('[WebPageIndexer] Error indexing page:', error);
    }
}

// Function to highlight text on the page
function highlightText(query) {
    console.log('[WebPageIndexer] Starting highlight process for query:', query);
    try {
        // Remove existing highlights
        const existingHighlights = document.querySelectorAll('.search-highlight');
        console.log(`[WebPageIndexer] Found ${existingHighlights.length} existing highlights to remove`);
        
        existingHighlights.forEach(el => {
            const parent = el.parentNode;
            if (parent) {
                parent.replaceChild(document.createTextNode(el.textContent), el);
                parent.normalize();
            }
        });

        if (!query) {
            console.log('[WebPageIndexer] No query provided for highlighting');
            return;
        }

        // Create regex pattern for highlighting
        const pattern = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        console.log('[WebPageIndexer] Created regex pattern:', pattern);
        
        // Function to process a text node
        function processTextNode(node) {
            if (!node.textContent.match(pattern)) return;
            
            const text = node.textContent;
            console.log('[WebPageIndexer] Found matching text:', text);
            
            const highlighted = text.replace(pattern, '<span class="search-highlight" style="background-color: #fef7e0; padding: 2px 4px; border-radius: 4px; color: #b06000;">$1</span>');
            
            const temp = document.createElement('div');
            temp.innerHTML = highlighted;
            
            const fragment = document.createDocumentFragment();
            while (temp.firstChild) {
                fragment.appendChild(temp.firstChild);
            }
            
            if (node.parentNode) {
                node.parentNode.replaceChild(fragment, node);
                console.log('[WebPageIndexer] Replaced text node with highlighted version');
            }
        }

        // Process all text nodes in the document
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function(node) {
                    // Skip script, style, and already highlighted nodes
                    if (node.parentNode.nodeName === 'SCRIPT' || 
                        node.parentNode.nodeName === 'STYLE' ||
                        node.parentNode.classList.contains('search-highlight')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            },
            false
        );

        let node;
        let highlightCount = 0;
        let processedCount = 0;
        
        while (node = walker.nextNode()) {
            processedCount++;
            if (node.textContent.match(pattern)) {
                processTextNode(node);
                highlightCount++;
            }
        }

        console.log(`[WebPageIndexer] Processed ${processedCount} text nodes, found ${highlightCount} matches`);

        // Scroll to first highlight
        const firstHighlight = document.querySelector('.search-highlight');
        if (firstHighlight) {
            console.log('[WebPageIndexer] Found first highlight, scrolling to it');
            // Wait a bit for the DOM to update
            setTimeout(() => {
                firstHighlight.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'nearest'
                });
                console.log('[WebPageIndexer] Scrolled to first highlight');
            }, 100);
        } else {
            console.log('[WebPageIndexer] No highlights found to scroll to');
        }
    } catch (error) {
        console.error('[WebPageIndexer] Error highlighting text:', error);
        throw error;
    }
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[WebPageIndexer] Received message:', request);
    if (request.action === 'highlight') {
        try {
            console.log('[WebPageIndexer] Starting highlight process for text:', request.text);
            highlightText(request.text);
            console.log('[WebPageIndexer] Highlight process completed');
            sendResponse({ success: true });
        } catch (error) {
            console.error('[WebPageIndexer] Error handling highlight message:', error);
            sendResponse({ success: false, error: error.message });
        }
    } else {
        console.log('[WebPageIndexer] Unknown message action:', request.action);
        sendResponse({ success: false, error: 'Unknown action' });
    }
    return true; // Keep the message channel open for async response
});

// Initialize content script
console.log('[WebPageIndexer] Content script loaded and initialized');

// Index the page when it loads
window.addEventListener('load', () => {
    console.log('[WebPageIndexer] Page loaded, scheduling indexing...');
    // Wait a bit for dynamic content to load
    setTimeout(() => {
        console.log('[WebPageIndexer] Starting delayed indexing...');
        indexCurrentPage();
    }, 2000);
}); 