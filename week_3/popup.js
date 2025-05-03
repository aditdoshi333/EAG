document.addEventListener('DOMContentLoaded', () => {
  const searchButton = document.getElementById('searchButton');
  const productQuery = document.getElementById('productQuery');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const results = document.getElementById('results');

  // Check for OpenAI API key in storage
  chrome.storage.local.get(['openaiApiKey'], (result) => {
    if (result.openaiApiKey) {
      window.openAIApi.setApiKey(result.openaiApiKey);
    } else {
      // Prompt for OpenAI API key if not set
      const apiKey = prompt('Please enter your OpenAI API key (required for product analysis):');
      if (apiKey) {
        window.openAIApi.setApiKey(apiKey);
        chrome.storage.local.set({ openaiApiKey: apiKey });
      }
    }
  });

  searchButton.addEventListener('click', async () => {
    const query = productQuery.value.trim();
    if (!query) {
      alert('Please enter a product to search for');
      return;
    }

    try {
      // Show loading state
      searchButton.disabled = true;
      loadingIndicator.classList.add('active');
      results.innerHTML = '';
      window.logger.clear();

      // Log initial query
      window.logger.logQuery(query);

      // Step 1: Analyze the query using LLM
      window.logger.logLLMInput(
        `Analyze the following product search query and identify key features and criteria to look for:
        Query: "${query}"
        
        Please provide:
        1. Key features to consider
        2. Price range (if specified)
        3. Important specifications
        4. Any specific requirements or preferences`,
        'Query Analysis'
      );
      
      const searchCriteria = await window.openAIApi.analyzeProductQuery(query);
      window.logger.logLLMOutput(searchCriteria, 'Query Analysis');
      
      // Step 2: Search for products across all sites
      window.logger.logToolInput('searchAllSites', { query }, 'Product Search');
      const products = await window.shoppingTools.searchAllSites(query);
      window.logger.logToolOutput('searchAllSites', products, 'Product Search');
      
      if (products.length === 0) {
        throw new Error('No products found. Please try a different search query.');
      }
      
      // Step 3: Get price comparison
      window.logger.logToolInput('comparePrices', { products }, 'Price Comparison');
      const priceComparison = await window.shoppingTools.comparePrices(products);
      window.logger.logToolOutput('comparePrices', priceComparison, 'Price Comparison');
      
      // Step 4: Get review aggregation
      window.logger.logToolInput('aggregateReviews', { products }, 'Review Analysis');
      const reviewAggregation = await window.shoppingTools.aggregateReviews(products);
      window.logger.logToolOutput('aggregateReviews', reviewAggregation, 'Review Analysis');
      
      // Step 5: Analyze results using LLM
      window.logger.logLLMInput(
        `Based on the following search criteria and product options, analyze and recommend the best options:
        
        Search Criteria:
        ${searchCriteria}
        
        Products:
        ${JSON.stringify(products, null, 2)}
        
        Price Comparison:
        ${JSON.stringify(priceComparison, null, 2)}
        
        Reviews:
        ${JSON.stringify(reviewAggregation, null, 2)}
        
        Please provide:
        1. Top 3 recommendations with reasoning
        2. Price comparison analysis
        3. Key advantages and disadvantages of each option
        4. Best value for money option
        5. Final recommendation with detailed explanation`,
        'Final Analysis'
      );
      
      const analysis = await window.openAIApi.analyzeProducts(products, searchCriteria);
      window.logger.logLLMOutput(analysis, 'Final Analysis');

      // Log final recommendation
      window.logger.logFinalRecommendation(analysis);

      // Display results
      results.innerHTML = `
        <h3>Analysis Results</h3>
        <div class="analysis">${analysis.replace(/\n/g, '<br>')}</div>
        
        <h3>Price Comparison</h3>
        <div class="price-comparison">
          <p>Lowest Price: $${priceComparison.lowestPrice.toFixed(2)}</p>
          <p>Highest Price: $${priceComparison.highestPrice.toFixed(2)}</p>
          <p>Average Price: $${priceComparison.averagePrice.toFixed(2)}</p>
          <div class="price-history">
            <h4>Price History (Last 7 Days)</h4>
            ${priceComparison.priceHistory.map(history => `
              <div class="price-history-item">
                <h5>${history.name}</h5>
                <p>Current Price: $${history.currentPrice.toFixed(2)}</p>
                <p>Trend: ${history.priceTrend}</p>
                <div class="historical-prices">
                  ${history.historicalPrices.map(hp => `
                    <div class="historical-price">
                      <span>${hp.date}</span>
                      <span>$${hp.price.toFixed(2)}</span>
                    </div>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
        
        <h3>Product Reviews</h3>
        <div class="reviews">
          ${reviewAggregation.map(review => `
            <div class="review-item">
              <h4>${review.name}</h4>
              <p>Rating: ${review.rating}/5 (${review.reviewCount} reviews)</p>
              <p>Sentiment: ${review.sentiment}</p>
              <ul>
                ${review.keyHighlights.map(highlight => `<li>${highlight}</li>`).join('')}
              </ul>
            </div>
          `).join('')}
        </div>
      `;

    } catch (error) {
      results.innerHTML = `
        <div class="error">
          <p>Error: ${error.message}</p>
          <p>Please make sure you have set up the OpenAI API key for product analysis.</p>
        </div>
      `;
    } finally {
      // Hide loading state
      searchButton.disabled = false;
      loadingIndicator.classList.remove('active');
    }
  });
}); 