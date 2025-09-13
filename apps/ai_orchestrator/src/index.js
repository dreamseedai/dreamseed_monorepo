const express = require('express');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// LLM Model selection based on language
function selectLLMModel(language) {
  switch (language.toLowerCase()) {
    case 'ko':
    case 'korean':
      return 'korean-llm';
    case 'zh':
    case 'chinese':
      return 'deepseek';
    default:
      return 'gpt-4o-mini';
  }
}

// POST /ai/assist endpoint
app.post('/ai/assist', (req, res) => {
  try {
    const { language, message } = req.body;

    // Validate required fields
    if (!message) {
      return res.status(400).json({
        error: 'Message is required'
      });
    }

    // Default language to 'en' if not provided
    const detectedLanguage = language || 'en';
    
    // Select appropriate LLM model
    const selectedModel = selectLLMModel(detectedLanguage);

    // Return response with selected model and processing info
    const response = {
      model: selectedModel,
      language: detectedLanguage,
      message: message,
      timestamp: new Date().toISOString(),
      status: 'processed'
    };

    res.json(response);

  } catch (error) {
    console.error('Error processing AI assist request:', error);
    res.status(500).json({
      error: 'Internal server error'
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'ai-orchestrator',
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`AI Orchestrator service running on port ${PORT}`);
});

module.exports = app;