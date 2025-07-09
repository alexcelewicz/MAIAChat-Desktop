# Agent Context Window Management

## Overview

This feature addresses the critical issue where consecutive agents in multi-agent workflows would hit context window limits due to exponentially growing context as each agent receives all previous agent responses.

## Problem Description

When processing multiple agents sequentially (e.g., 5 agents), each subsequent agent receives:
- Original user query
- Full conversation history  
- All previous agent responses
- Instructions and system prompts
- RAG content, MCP context, search results

This causes the context to grow exponentially:
- Agent 1: ~5,000 tokens
- Agent 2: ~10,000 tokens (Agent 1 response + context)
- Agent 3: ~20,000 tokens (Agent 1 + Agent 2 responses + context)
- Agent 4: **OVERFLOW** - Exceeds 32,768 token limit

## Solution: Intelligent Context Management

### Key Features

1. **Automatic Context Window Detection**
   - Detects provider/model context limits
   - Calculates available space for agent responses
   - Reserves space for instructions and output

2. **Intelligent Truncation Strategy**
   - Recent agents get priority (more space allocation)
   - Older agents get summarized or truncated
   - Preserves most important information

3. **Configurable Behavior**
   - Can be enabled/disabled via configuration
   - Multiple truncation strategies available

### Configuration Options

#### Method 1: UI Settings (Recommended)
1. Open the application
2. Go to **Settings** tab
3. Click **General Settings** button
4. Find **Agent Context Management** section
5. Enable/disable context management with checkbox
6. Select strategy from dropdown:
   - `intelligent_truncation` (recommended)
   - `simple_truncation`
   - `summarization_only`
7. Click **OK** to save

#### Method 2: Manual Configuration
Add to `config.json`:

```json
{
    "AGENT_CONTEXT_MANAGEMENT": true,
    "AGENT_CONTEXT_STRATEGY": "intelligent_truncation"
}
```

**Options:**
- `AGENT_CONTEXT_MANAGEMENT`: `true`/`false` - Enable/disable the feature
- `AGENT_CONTEXT_STRATEGY`: Strategy selection:
  - `"intelligent_truncation"` - Smart paragraph-aware truncation with summarization
  - `"simple_truncation"` - Basic character-based truncation
  - `"summarization_only"` - Summarize older responses without truncation

### How It Works

#### 1. Context Space Allocation
- **60%** of total context window reserved for agent responses
- **40%** reserved for instructions, current message, and output

#### 2. Priority-Based Allocation
- **Most recent agent**: Up to 50% of available space
- **Second most recent**: Up to 30% of available space  
- **Older agents**: Up to 20% of available space (summarized)

#### 3. Truncation Strategies

**For Recent Agents (1-2 most recent):**
- Intelligent paragraph-based truncation
- Preserves complete sentences and paragraphs
- Adds truncation notice when content is cut

**For Older Agents (3+):**
- Extractive summarization
- Identifies key sentences with important indicators
- Creates concise summaries preserving main points

### Example Output

#### Without Context Management
```
=== PREVIOUS AGENT RESPONSES ===
Agent 1 Response:
[Full 2000+ token response...]

Agent 2 Response:  
[Full 3000+ token response...]

Agent 3 Response:
[Full 4000+ token response...]
```
**Result**: Context overflow, API error

#### With Context Management
```
=== PREVIOUS AGENT RESPONSES (CONTEXT MANAGED) ===
Agent 3 Response:
[Full recent response - 2000 tokens]

Agent 2 Response (truncated):
[Truncated response preserving key information - 1000 tokens]

Agent 1 Summary:
[Concise summary of main points - 300 tokens]

[Note: Context management applied to fit within token limits]
```
**Result**: Successful processing, no overflow

### Benefits

1. **Prevents Context Overflow**
   - Eliminates 400 errors from exceeding context limits
   - Ensures all agents can process successfully

2. **Preserves Important Information**
   - Recent responses get full space allocation
   - Older responses are intelligently summarized
   - Key information is preserved across the chain

3. **Maintains Agent Chain Quality**
   - Each agent still has access to previous work
   - Context builds progressively without overflow
   - Final responses incorporate all agent insights

4. **Configurable and Transparent**
   - Can be disabled if not needed
   - Clear logging when truncation occurs
   - Visible indicators in agent responses

### Technical Implementation

#### Key Methods

1. **`_format_agent_responses_with_context_management()`**
   - Main entry point for context management
   - Checks configuration and applies strategies

2. **`_apply_context_truncation_strategy()`**
   - Implements priority-based allocation
   - Handles truncation and summarization

3. **`_intelligent_truncate_response()`**
   - Paragraph and sentence-aware truncation
   - Preserves content structure

4. **`_create_response_summary()`**
   - Extractive summarization for older responses
   - Identifies and preserves key information

### Performance Impact

- **Minimal Processing Overhead**: Context management only activates when needed
- **Token Estimation**: Fast character-based token estimation
- **Memory Efficient**: Processes responses individually, not all at once

### Monitoring and Debugging

The system provides clear logging when context management is applied:

```
Agent 4: Context window management - truncating previous responses (15000 tokens > 12000 limit)
```

### Use Cases

**Ideal for:**
- Multi-agent workflows (3+ agents)
- Long-form content generation
- Complex analysis requiring multiple perspectives
- Research and synthesis tasks

**Not needed for:**
- Single agent workflows
- Short responses (under 1000 tokens each)
- Models with very large context windows (100k+ tokens)

### Future Enhancements

1. **Advanced Summarization**
   - Integration with LLM-based summarization
   - Semantic importance scoring

2. **Context Compression**
   - Advanced compression techniques
   - Lossless context reduction

3. **Dynamic Strategies**
   - Task-specific truncation strategies
   - User-defined priority rules

## Testing

Run the test suite to verify functionality:

```bash
python test_context_management.py
```

The test validates:
- Configuration options
- Context management enable/disable
- Truncation strategies
- Small response handling
- Large response processing
