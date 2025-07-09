# Token Limit Coordination Solution

## Overview

This solution addresses the issue where users want to set high token limits (e.g., 100k tokens) for agents, but the system was blocking or truncating content unnecessarily. The implementation ensures that user-specified token limits are respected when possible, while gracefully handling API limitations.

## Problem Statement

When running conversations with 5 agents, each producing thousands of tokens, users need assurance that:
1. If they set a max token limit of 100k, it should be the limit unless the API doesn't allow it
2. The app should not block or truncate content unnecessarily
3. The system should provide clear feedback about token limit adjustments

## Solution Components

### 1. Enhanced Model Settings (`model_settings.py`)

#### Updated Parameter Ranges
- **Increased max_tokens range**: From 16-32,000 to 16-100,000 tokens
- **Updated default settings**: Increased default max_tokens for all providers

#### New Token Limit Coordination Methods

##### `get_effective_max_tokens(user_requested_tokens=None)`
- Determines the effective max_tokens value considering user requests and API limits
- Returns the appropriate token limit based on:
  - User-specified limit (if provided)
  - API provider limits
  - Current model settings

##### `get_api_token_limits()`
- Returns known API limits for each provider
- Includes min, max, and recommended token limits
- Supports all major providers (OpenAI, Anthropic, Groq, Ollama, etc.)

##### `validate_and_adjust_max_tokens(user_requested_tokens=None)`
- Validates and adjusts max_tokens based on user request and API limits
- Returns detailed validation results including:
  - Original setting
  - User requested amount
  - API limit
  - Effective tokens
  - Whether adjustment was made
  - Reason for adjustment

### 2. Enhanced Worker Class (`worker.py`)

#### New Method: `_validate_and_adjust_token_limits(agent, agent_number)`
- Validates token limits for each agent before processing
- Logs token limit information and adjustments
- Returns validation results for use in API calls

#### Updated API Call Methods
- All API call methods now accept `effective_max_tokens` parameter
- Methods use the effective token limit instead of default settings
- Supports all providers: OpenAI, Anthropic, Groq, Ollama, etc.

#### Enhanced Agent Processing
- Token validation occurs before each agent processes
- Clear logging of token limits and adjustments
- Graceful handling of API limitations

### 3. Improved Conversation Management (`conversation_manager.py`)

#### Enhanced Validation Rules
- **Increased max content length**: From 50,000 to 500,000 characters
- **Added warning threshold**: 100,000 characters for monitoring
- **Content truncation**: Automatic truncation for extremely large content
- **Better error handling**: More informative error messages

## How It Works

### 1. Token Limit Flow

```
User sets max_tokens: 100,000
    ↓
System validates against API limits
    ↓
If API allows 100k → Use 100k
If API limit is 32k → Use 32k + Log warning
    ↓
Pass effective_max_tokens to API call
    ↓
API respects the limit
```

### 2. Validation Process

1. **User Request**: User specifies desired token limit
2. **API Check**: System checks provider's API limits
3. **Adjustment**: If needed, adjusts to API limit
4. **Logging**: Provides clear feedback about adjustments
5. **Execution**: Uses effective token limit for API calls

### 3. Error Handling

- **Graceful degradation**: Falls back to API limits when user limits exceed them
- **Clear messaging**: Users understand why limits were adjusted
- **No blocking**: System continues processing with adjusted limits

## API Provider Limits

| Provider | Min Tokens | Max Tokens | Recommended |
|----------|------------|------------|-------------|
| OpenAI   | 1          | 16,384     | 4,096       |
| Anthropic| 1          | 32,768     | 8,192       |
| Groq     | 1          | 16,384     | 4,000       |
| Ollama   | 1          | 32,768     | 4,096       |
| Google   | 1          | 32,768     | 8,192       |
| Grok     | 1          | 32,768     | 16,000      |
| DeepSeek | 1          | 32,768     | 4,096       |
| LM Studio| 1          | 32,768     | 8,000       |
| OpenRouter| 1         | 32,768     | 4,096       |

## Usage Examples

### Example 1: User requests 100k tokens for OpenAI
```python
# User sets max_tokens: 100000
# API limit: 16384
# Result: Uses 16384, logs warning
validation_result = {
    "user_requested": 100000,
    "api_limit": 16384,
    "effective_tokens": 16384,
    "was_adjusted": True,
    "adjustment_reason": "User requested 100,000 tokens exceeds API limit of 16,384"
}
```

### Example 2: User requests 20k tokens for Anthropic
```python
# User sets max_tokens: 20000
# API limit: 32768
# Result: Uses 20000 (within limits)
validation_result = {
    "user_requested": 20000,
    "api_limit": 32768,
    "effective_tokens": 20000,
    "was_adjusted": True,
    "adjustment_reason": "Updated from 8,192 to 20,000 tokens"
}
```

### Example 3: No user limit specified
```python
# No user limit
# Result: Uses default setting
effective_tokens = 16384  # Default for OpenAI
```

## Benefits

1. **User Control**: Users can specify high token limits when needed
2. **API Compliance**: System respects API limitations automatically
3. **Transparency**: Clear feedback about token limit adjustments
4. **No Blocking**: System doesn't unnecessarily truncate content
5. **Flexibility**: Works with all supported API providers
6. **Performance**: Efficient token limit validation and coordination

## Testing

The solution includes comprehensive testing:

```bash
python test_token_limits.py
```

Tests cover:
- Basic token limit validation
- Different provider limits
- User limits within API limits
- User limits exceeding API limits
- Default behavior when no user limit specified

## Future Enhancements

1. **Dynamic API Limits**: Automatically detect API limits at runtime
2. **Cost Optimization**: Suggest optimal token limits based on cost
3. **Provider-Specific Features**: Leverage provider-specific capabilities
4. **Token Usage Analytics**: Track actual token usage vs. limits
5. **Smart Defaults**: Suggest optimal limits based on conversation context

## Conclusion

This solution ensures that when users set high token limits (like 100k), the system respects those limits unless the API doesn't allow it. The implementation provides clear feedback, graceful handling of limitations, and ensures no unnecessary blocking or truncation of agent responses. 