# Todo List

## Current Tasks
- Create example profiles for agents with different number of agents from 1 to 5 with real world use cases
- Create at least two example profiles for each number of agents (e.g., two for single agent, two for two agents, etc.)
- Add a new button "Example Profiles" to load these example profiles
- Implement UI for model settings to allow adjusting parameters like temperature, top_k, top_p, max tokens, etc.
- Make model settings accessible from the UI for each provider

## Completed Tasks
- Initial implementation of multi-agent system
- Added conversation history management
- Implemented token counter
- Added support for multiple LLM providers
- Fixed crash when loading past conversations from history (added missing format_streaming_chunk to TextFormatter, verified working)
