# BYOM (Bring Your Own Model) Integration Guide

## Overview

Vaktram supports BYOM (Bring Your Own Model) for the summarization step. Enterprise customers can configure their own LLM provider and model for generating meeting summaries, action items, decisions, and follow-ups.

## Supported Providers

| Provider | Models | Configuration |
|----------|--------|---------------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo | API key |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-3-haiku | API key |
| Google | gemini-1.5-pro, gemini-1.5-flash | API key |
| Azure OpenAI | Any Azure-deployed model | API key + base URL |
| Groq | llama-3.1-70b, mixtral-8x7b | API key |
| Together AI | Any model on Together platform | API key |
| Ollama | Any locally-hosted model | Base URL (no key needed) |

## Setup via API

### Add a BYOM Configuration

```bash
curl -X POST https://api.vaktram.com/api/v1/byom/configs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "model_name": "claude-3-sonnet-20240229",
    "api_key": "sk-ant-api03-..."
  }'
```

### For Azure OpenAI

```bash
curl -X POST https://api.vaktram.com/api/v1/byom/configs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "azure",
    "model_name": "azure/my-gpt4-deployment",
    "api_key": "your-azure-key",
    "base_url": "https://your-resource.openai.azure.com/"
  }'
```

### For Self-Hosted Ollama

```bash
curl -X POST https://api.vaktram.com/api/v1/byom/configs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "model_name": "ollama/llama3.1:70b",
    "base_url": "http://your-ollama-server:11434"
  }'
```

## Setup via Dashboard

1. Navigate to **Settings** > **AI Model Configuration**
2. Select your provider from the dropdown
3. Enter your API key and model name
4. Click **Test Connection** to verify
5. Save the configuration

## How It Works

1. When a meeting transcript is ready for summarization, the system checks for a BYOM configuration in the organization settings
2. If a custom model is configured and active, LiteLLM routes the request to the specified provider
3. If no custom model is set, the default model (gpt-4o-mini) is used
4. API keys are encrypted at rest using AES-256

## Custom Prompts (Enterprise)

Enterprise plans can also customize the prompts used for:
- Summary generation
- Action item extraction
- Decision identification
- Follow-up extraction

Contact support to set up custom prompt templates.

## Security

- API keys are encrypted before storage using AES-256-GCM
- Keys are never exposed in API responses (masked as `sk-...****`)
- BYOM configurations are scoped to the organization level
- Only organization owners and admins can manage BYOM settings
- All LLM API calls are made server-side; keys never reach the client

## Limitations

- BYOM applies only to the summarization step
- Transcription always uses the built-in Faster-Whisper pipeline
- Speaker diarization always uses the built-in pyannote pipeline
- The LLM must support chat completion format (messages array)
- Maximum context window must be at least 16K tokens for reliable results
