You need to modify the Python Agents application to better handle agent timeouts and improve the robustness of multi-agent collaboration, especially when a preceding agent fails.

Here are the specific changes:

1.  **Modify `worker.py` - Function `_process_agents_sequentially`:**
    *   **Improve Error/Timeout Propagation to `agent_responses`:**
        When an agent's processing (within its loop iteration) results in a timeout (e.g., `queue.Empty` from `result_queue.get()`) or an exception is caught by the main `try...except Exception as e:` block for that agent:
        You must explicitly set `agent_responses[agent_number]` to a clear, structured error message *before* `continue`ing to the next agent or breaking the loop. This ensures the *next* agent receives this error as the "output" of the failed agent in its "PREVIOUS AGENT RESPONSES" context.

        **Locate the part where agent processing timeout is handled (likely after `result_queue.get(timeout=timeout_seconds)` raises `queue.Empty`) and the main `except Exception as e:` block for an agent's iteration.**

        Modify it to include something like this:

        ```python
        # Example for timeout handling:
        # (Inside the block where queue.Empty is caught, or equivalent timeout logic)
        failure_reason_str = f"Agent {agent_number} ({model}) processing timed out after {timeout_seconds} seconds."
        # ... (existing logging and signal emitting for timeout) ...
        
        structured_error_for_next_agent = (
            f"CRITICAL_ERROR_REPORT: Agent {agent_number} (Model: {model}) failed its task. "
            f"Reason: {failure_reason_str}. "
            "Instruction for next agent: You MUST acknowledge this failure. DO NOT attempt to use or synthesize this error report as content. "
            "Base your response on successful outputs from agents *prior* to this failed one, and the original user request. "
            "If this was a critical step, you may need to attempt the failed agent's task yourself if appropriate for your role, or state why the overall goal cannot be achieved."
        )
        agent_responses[agent_number] = structured_error_for_next_agent # <--- CRITICAL: Set this for the next agent
        # ... (then add to conversation_manager.add_message with a concise version of failure_reason_str, emit signals, etc.) ...

        # Example for general exception handling:
        # (Inside the main `except Exception as e:` block for an agent's iteration)
        failure_reason_str = f"Agent {agent_number} ({model}) encountered an error: {str(e)}"
        # ... (existing logging and signal emitting for the error) ...

        structured_error_for_next_agent = (
            f"CRITICAL_ERROR_REPORT: Agent {agent_number} (Model: {model}) failed its task. "
            f"Reason: {failure_reason_str}. "
            "Instruction for next agent: You MUST acknowledge this failure. DO NOT attempt to use or synthesize this error report as content. "
            "Base your response on successful outputs from agents *prior* to this failed one, and the original user request. "
            "If this was a critical step, you may need to attempt the failed agent's task yourself if appropriate for your role, or state why the overall goal cannot be achieved."
        )
        agent_responses[agent_number] = structured_error_for_next_agent # <--- CRITICAL: Set this for the next agent
        # ... (then add to conversation_manager.add_message with a concise version of failure_reason_str, emit signals, etc.) ...
        ```

2.  **Modify `worker.py` - API Call Methods (e.g., `call_openrouter_api`, `call_deepseek_api`):**
    *   **Standardize Returned Error Strings on Full Retry Failure:**
        When an API call exhausts all its retries and still fails (e.g., due to repeated timeouts or server errors), ensure the string *returned by the API call function itself* is structured to be easily identifiable as a hard failure.
        *   Search for the end of the retry loops in these functions.
        *   Modify the final error return statement. For example, in `call_openrouter_api`:
            ```python
            # Instead of just:
            # return f"Error: {final_error_msg}"
            # Use:
            return f"API_CALL_HARD_FAILURE: Provider={provider}, Model={model}. Reason: {final_error_msg}"
            ```
        *   The `_process_agents_sequentially` logic (modified in step 1) should then check if `result_value` (which holds this return string) starts with `API_CALL_HARD_FAILURE:` and then construct the more detailed `CRITICAL_ERROR_REPORT` for the next agent.

3.  **Modify `instruction_templates.py` - Function `get_agent_instructions`:**
    *   **For the Final Agent (where `agent_number == total_agents`):**
        *   Enhance its initial instructions. Add a prominent, critical directive:
            ```diff
            As the final agent, your task is to:
            1. Review all previous agent responses carefully.
            +   **CRITICAL DIRECTIVE FOR HANDLING FAILURES: If you encounter a previous agent's response that is a 'CRITICAL_ERROR_REPORT' (or contains clear indications of timeout/failure like '[Agent X processing timed out...]' or 'API_CALL_HARD_FAILURE:'):**
            +       a. **DO NOT** attempt to use, synthesize, or incorporate the error message itself as part of your answer.
            +       b. **Explicitly acknowledge** that a previous agent (e.g., "Agent X") failed to complete its task and briefly state the reason if provided in the error report.
            +       c. **Adapt your strategy:** Formulate your final answer based *only* on the successful, coherent outputs from agents *before* the failed one, and the original user request.
            +       d. If the failed agent was critical and its output is essential, and you cannot recover or complete the task based on prior information, then your final answer should state that the request could not be fully completed due to the specified agent failure, and explain (if possible) what information is missing or what step could not be performed.
            2. Synthesize the successful responses into a single, cohesive FINAL ANSWER.
            ...
            ```
    *   **For Middle Agents (in the `else` block for `agent_number` where `agent_number < total_agents` and `agent_number > 1`):**
        *   Add a similar critical directive:
            ```diff
            As agent {agent_number} of {total_agents}, your task is to:
            1. Review the previous agent responses carefully.
            +   **CRITICAL DIRECTIVE FOR HANDLING FAILURES: If the *immediately preceding* agent's response is a 'CRITICAL_ERROR_REPORT' (or contains clear indications of timeout/failure):**
            +       a. **Acknowledge the failure** of the preceding agent.
            +       b. **Attempt to perform the task of the failed preceding agent** to the best of your ability, in addition to your own assigned role of building upon *earlier successful* responses. Clearly state that you are taking over or attempting the failed step.
            +       c. If you cannot perform the failed agent's task (e.g., due to missing information that only it could generate), clearly state this limitation. Then, focus on your primary role of refining and building upon any successful outputs from agents *even earlier* in the chain.
            +       d. **Do not** incorporate the error message itself into your constructive output.
            2. Build upon the successful responses by:
            ...
            ```

These changes aim to make the agent chain more resilient. Failed agent outputs will be clearly marked, and subsequent agents will have explicit instructions on how to proceed, rather than trying to "make sense" of an error message as if it were valid content.

**Regarding the long delays:**
While the above fixes address error handling, the long processing times for complex tasks with large contexts using `mistralai/magistral-medium-2506` might persist. If delays are still an issue after these fixes, consider:
*   Informing the user that they can increase `AGENT_PROCESSING_TIMEOUT` and `API_CALL_TIMEOUT` in `config.json`.
*   Suggesting that the user try different, potentially faster models available through OpenRouter or other providers for computationally intensive tasks.
*   (Future Enhancement) Implementing more sophisticated context management strategies (e.g., summarizing older parts of the conversation) for very long interactions, though this is beyond the scope of the immediate fix.