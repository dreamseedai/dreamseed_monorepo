# AI Orchestrator Service

This service provides language-based LLM model selection for the Dreamseed AI-powered learning portal.

## Features

- **Language-based Model Selection**: Automatically selects the appropriate LLM model based on the detected language:
  - Korean (`ko`) → `korean-llm`
  - Chinese (`zh`) → `deepseek`
  - All other languages → `gpt-4o-mini`

## API Endpoints

### POST /ai/assist

Processes AI assistance requests with automatic model selection based on language.

**Request Body:**
```json
{
  "language": "ko",
  "message": "안녕하세요, 도움이 필요합니다"
}
```

**Response:**
```json
{
  "model": "korean-llm",
  "language": "ko",
  "message": "안녕하세요, 도움이 필요합니다",
  "timestamp": "2023-12-07T10:30:00.000Z",
  "status": "processed"
}
```

**Parameters:**
- `language` (optional): Language code (e.g., 'ko', 'zh', 'en'). Defaults to 'en' if not provided.
- `message` (required): The user message to process.

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-orchestrator",
  "timestamp": "2023-12-07T10:30:00.000Z"
}
```

## Installation

```bash
npm install
```

## Running the Service

```bash
# Development mode
npm run dev

# Production mode
npm start
```

## Testing

```bash
npm test
```

## Environment Variables

- `PORT`: Server port (default: 3000)

## Model Selection Logic

The service uses the following logic to select LLM models:

1. **Korean** (`ko`, `korean`) → `korean-llm`
2. **Chinese** (`zh`, `chinese`) → `deepseek`
3. **All other languages** → `gpt-4o-mini`

Language codes are case-insensitive for flexibility.