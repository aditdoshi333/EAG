class Logger {
  constructor() {
    this.logs = [];
    this.logContainer = document.getElementById('logContainer');
    this.sequenceNumber = 1;
  }

  log(type, data, step) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      sequence: this.sequenceNumber++,
      timestamp,
      type,
      step,
      data
    };
    
    this.logs.push(logEntry);
    this.updateUI();
  }

  logQuery(query) {
    this.log('QUERY', {
      query,
      timestamp: new Date().toISOString()
    }, 'Initial Query');
  }

  logLLMInput(prompt, step) {
    this.log('LLM_INPUT', {
      prompt,
      model: 'gpt-4-mini',
      step
    }, 'LLM Analysis');
  }

  logLLMOutput(response, step) {
    this.log('LLM_OUTPUT', {
      response,
      step
    }, 'LLM Response');
  }

  logToolInput(toolName, params, step) {
    this.log('TOOL_INPUT', {
      tool: toolName,
      parameters: params,
      step
    }, 'Tool Execution');
  }

  logToolOutput(toolName, result, step) {
    this.log('TOOL_OUTPUT', {
      tool: toolName,
      result,
      step
    }, 'Tool Result');
  }

  logFinalRecommendation(recommendation) {
    this.log('FINAL_RECOMMENDATION', {
      recommendation,
      timestamp: new Date().toISOString()
    }, 'Final Result');
  }

  updateUI() {
    if (!this.logContainer) return;
    
    this.logContainer.innerHTML = this.logs
      .map(log => {
        const formattedData = JSON.stringify(log.data, null, 2);
        return `
          <div class="log-entry">
            <div class="log-header">
              <span class="sequence">#${log.sequence}</span>
              <span class="timestamp">${log.timestamp}</span>
              <span class="type">${log.type}</span>
              <span class="step">${log.step}</span>
            </div>
            <pre class="log-data">${formattedData}</pre>
          </div>
        `;
      })
      .join('\n');
    
    this.logContainer.scrollTop = this.logContainer.scrollHeight;
  }

  clear() {
    this.logs = [];
    this.sequenceNumber = 1;
    this.updateUI();
  }
}

// Create a global logger instance
window.logger = new Logger(); 