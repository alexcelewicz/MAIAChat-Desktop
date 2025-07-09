# Ollama Thinking Feature Implementation

## Overview

This implementation adds support for Ollama's new thinking feature, which allows certain models to show their reasoning process before providing the final answer. This feature was introduced in Ollama's May 30, 2025 update.

## Supported Models

Based on the [Ollama blog post](https://ollama.com/blog/thinking), the following models currently support thinking:

### Ollama Models
- `deepseek-r1` (all variants: `:8b`, `:32b`, `:latest`)
- `qwen3` (all variants: `:4b`, `:7b`, `:14b`, `:32b`)

### DeepSeek Models
- `deepseek-reasoner` (DeepSeek R1 models)

## Features

### Individual Agent Control
- Each agent can have thinking enabled or disabled independently
- Thinking checkbox appears only for models that support it
- Settings are saved and loaded with agent profiles and JSON configurations

### Visual Distinction
When thinking is enabled, the UI shows:
1. **Thinking Phase**: Displayed in a light gray box with italic text indicating "Agent X is thinking..."
2. **Response Phase**: Regular agent response after thinking is complete

### API Integration
- Uses Ollama's `think: true` parameter when supported
- Handles both streaming and non-streaming modes
- Processes `thinking` and `response` fields separately

## Usage Instructions

### Enabling Thinking for an Agent

1. **Select a Thinking-Capable Model**: Choose a provider (Ollama or DeepSeek) and select a model that supports thinking
2. **Enable Thinking**: Check the "Enable Thinking (for supported models)" checkbox that appears
3. **Configure and Run**: Set up your agent instructions and run the conversation

### UI Behavior

- **Hidden by Default**: The thinking checkbox is only visible when a thinking-capable model is selected
- **Auto-Hide**: If you change to a non-thinking model, the checkbox disappears and thinking is automatically disabled
- **Profile Persistence**: Thinking settings are saved when you save profiles or JSON configurations

### Example Models to Try

For testing the thinking feature, try these model combinations:

**Ollama (Local)**:
```
Provider: Ollama
Model: deepseek-r1:8b
☑ Enable Thinking
```

**DeepSeek (API)**:
```
Provider: DeepSeek  
Model: deepseek-reasoner
☑ Enable Thinking
```

## Technical Implementation

### Code Changes

1. **Agent Configuration (`agent_config.py`)**:
   - Added `thinking_enabled` field to `AgentConfiguration` dataclass
   - Added thinking checkbox with visibility logic
   - Added model capability checking

2. **Worker Process (`worker.py`)**:
   - Modified `call_ollama_api()` to support `think` parameter
   - Added thinking content display with different styling
   - Handles both streaming and non-streaming thinking responses

3. **Profile Management (`profile_manager.py`)**:
   - Added `thinking_enabled` field to `AgentProfile` dataclass
   - Updated profile save/load functionality

4. **File Handling (`handlers/file_handler.py`)**:
   - Updated JSON save/load to include thinking settings
   - Added backward compatibility for existing configurations

### API Response Format

When thinking is enabled, Ollama returns responses in this format:

**Streaming**:
```json
{"thinking": "reasoning chunk..."}
{"thinking": "more reasoning..."}
{"response": "final answer chunk..."}
{"response": "more answer..."}
{"done": true}
```

**Non-Streaming**:
```json
{
  "thinking": "complete reasoning process...",
  "response": "final answer...",
  "done": true
}
```

## Configuration Examples

### Profile JSON with Thinking
```json
{
  "name": "Thinking Agent Team",
  "agents": [
    {
      "provider": "Ollama",
      "model": "deepseek-r1:8b",
      "instructions": "You are a careful reasoning agent...",
      "thinking_enabled": true
    },
    {
      "provider": "Ollama", 
      "model": "llama3.1:latest",
      "instructions": "You provide quick responses...",
      "thinking_enabled": false
    }
  ]
}
```

## Benefits

1. **Transparency**: See how the model arrives at its conclusions
2. **Quality**: Models often provide better answers when they can "think" first
3. **Debugging**: Understand if the model misunderstood the prompt
4. **Learning**: Observe reasoning patterns and improve prompts

## Limitations

1. **Model Support**: Only works with specific models that support thinking
2. **Performance**: Thinking mode may be slower due to additional processing
3. **Token Usage**: Thinking content uses additional tokens (though not typically charged)

## Future Enhancements

As Ollama adds more thinking-capable models, they can be easily added to the `THINKING_CAPABLE_MODELS` dictionary in `agent_config.py`.

## Troubleshooting

### Thinking Checkbox Not Visible
- Ensure you're using a supported model (deepseek-r1, qwen3 variants)
- Check that Ollama is updated to a version that supports thinking

### No Thinking Output
- Verify the model actually supports thinking
- Check Ollama logs for any errors
- Ensure `think: true` parameter is being sent to the API

### API Errors
- Update Ollama to the latest version
- Verify the model is properly downloaded and available 