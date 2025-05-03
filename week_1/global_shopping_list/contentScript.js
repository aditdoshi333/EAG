// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'getProductInfo') {
    const productInfo = extractProductInfo();
    sendResponse({
      success: true,
      ...productInfo
    });
  }
  return true; // Keep the message channel open for async response
});

// Extract product information from the current page
function extractProductInfo() {
  // Initialize empty result
  const result = {
    title: '',
    price: '',
    imageUrl: ''
  };
  
  try {
    // Try to determine if we're on a product page and extract relevant information
    
    // 1. Extract product title - look for common title elements
    // Try common product title selectors
    const titleSelectors = [
      // Generic selectors
      'h1', 
      '.product-title', 
      '.product-name',
      '.product_title',
      '[data-ui="product-title"]',
      'meta[property="og:title"]',
      
      // Amazon
      '#productTitle',
      
      // Walmart
      '.prod-ProductTitle',
      
      // eBay
      '.x-item-title',
      
      // Best Buy
      '.heading-5',
      
      // Target
      '.Heading__StyledHeading-sc-1mp23s9-0',
      
      // Etsy
      '.wt-text-body-01'
    ];
    
    for (const selector of titleSelectors) {
      let titleElement;
      if (selector.startsWith('meta')) {
        titleElement = document.querySelector(selector);
        if (titleElement) {
          result.title = titleElement.getAttribute('content');
          break;
        }
      } else {
        titleElement = document.querySelector(selector);
        if (titleElement && titleElement.textContent.trim()) {
          result.title = titleElement.textContent.trim();
          break;
        }
      }
    }
    
    // If no title found, use document title as fallback
    if (!result.title) {
      result.title = document.title.replace(' - Amazon.com', '')
                                 .replace(' | eBay', '')
                                 .replace(' - Walmart.com', '')
                                 .replace(' - Target', '')
                                 .replace(' | Best Buy', '')
                                 .replace(' | Etsy', '')
                                 .trim();
    }
    
    // 2. Extract price - look for common price elements
    const priceSelectors = [
      // Generic
      '.price',
      '.product-price',
      '[data-ui="product-price"]',
      'meta[property="product:price:amount"]',
      
      // Amazon
      '#priceblock_ourprice',
      '.a-price .a-offscreen',
      
      // Walmart
      '.prod-PriceSection',
      
      // eBay
      '.x-price-primary',
      
      // Best Buy
      '.priceView-customer-price span',
      
      // Target
      '[data-test="product-price"]',
      
      // Etsy
      '.wt-text-title-03'
    ];
    
    for (const selector of priceSelectors) {
      let priceElement;
      if (selector.startsWith('meta')) {
        priceElement = document.querySelector(selector);
        if (priceElement) {
          result.price = priceElement.getAttribute('content');
          break;
        }
      } else {
        priceElement = document.querySelector(selector);
        if (priceElement && priceElement.textContent.trim()) {
          result.price = priceElement.textContent.trim();
          break;
        }
      }
    }
    
    // 3. Extract main product image
    const imgSelectors = [
      // Generic
      '.product-image-main img',
      '.product-image img',
      'meta[property="og:image"]',
      
      // Amazon
      '#landingImage',
      '#imgBlkFront',
      
      // Walmart
      '.prod-hero-image img',
      
      // eBay
      '.ux-image-carousel-item img',
      
      // Best Buy
      '.primary-image',
      
      // Target
      '[data-test="product-image"]',
      
      // Etsy
      '.wt-max-width-full'
    ];
    
    for (const selector of imgSelectors) {
      let imgElement;
      if (selector.startsWith('meta')) {
        imgElement = document.querySelector(selector);
        if (imgElement) {
          result.imageUrl = imgElement.getAttribute('content');
          break;
        }
      } else {
        imgElement = document.querySelector(selector);
        if (imgElement && imgElement.src) {
          result.imageUrl = imgElement.src;
          break;
        }
      }
    }
    
  } catch (error) {
    console.error('Error extracting product info:', error);
  }
  
  return result;
} 