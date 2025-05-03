class OpenAIApi {
  constructor() {
    this.apiKey = null;
    this.baseUrl = 'https://api.openai.com/v1';
  }

  setApiKey(apiKey) {
    this.apiKey = apiKey;
  }

  async callAPI(endpoint, data) {
    if (!this.apiKey) {
      throw new Error('OpenAI API key not set');
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async analyzeProductQuery(query) {
    const prompt = `Analyze the following product search query and identify key features and criteria to look for:
    Query: "${query}"
    
    Please provide:
    1. Key features to consider
    2. Price range (if specified)
    3. Important specifications
    4. Any specific requirements or preferences`;

    window.logger.logLLMInput(prompt);

    const response = await this.callAPI('/chat/completions', {
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are a shopping assistant that helps analyze product search queries.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.7,
      max_tokens: 500
    });

    window.logger.logLLMOutput(response.choices[0].message.content);
    return response.choices[0].message.content;
  }

  async analyzeProducts(products, searchCriteria) {
    const prompt = `Based on the following search criteria and product options, analyze and recommend the best options:
    
    Search Criteria:
    ${searchCriteria}
    
    Products:
    ${JSON.stringify(products, null, 2)}
    
    Please provide:
    1. Top 3 recommendations with reasoning
    2. Price comparison
    3. Key advantages and disadvantages of each option
    4. Best value for money option`;

    window.logger.logLLMInput(prompt);

    const response = await this.callAPI('/chat/completions', {
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are a shopping assistant that helps compare and recommend products.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.7,
      max_tokens: 1000
    });

    window.logger.logLLMOutput(response.choices[0].message.content);
    return response.choices[0].message.content;
  }
}

// Create a global API instance
window.openAIApi = new OpenAIApi(); 