# instruction_templates.py

class DocumentFormatInstructions:
    """Simple formatting instructions for consistent output."""
    
    BASE_FORMAT = """
    FORMATTING GUIDELINES:
    
    1. Use clear, numbered sections for organization
    2. Use bullet points for lists
    3. Present technical specifications in simple tables
    4. Use consistent formatting throughout
    """


class MiscInstructions:
    """Miscellaneous instruction templates for specific features."""
    
    IMAGE_HANDLING = """
    - If the user provides an image, analyze its content carefully.
    - Describe the image in detail if relevant to the query.
    - Extract any text present in the image.
    - Relate the image content to the user's question and provide a comprehensive answer.
    """


class InstructionTemplates:
    """
    Provides instructions for a collaborative multi-agent system where agents
    build on each other's work to create a cohesive final response.
    """
    
    # Core instructions for all agents
    BASE = """
    You are an AI assistant.
    Focus on accurately addressing the user's request.
    Maintain a helpful and clear tone.

    When providing code, always enclose it in triple backticks and specify the language, like this:
    ```
    ```python
    # Your code here
    ```
    ```
    For explanations, lists, and other text, use standard markdown formatting.
    """

    # Knowledge base instructions
    KNOWLEDGE_BASE_FOCUS = """
    When utilizing the knowledge base:
    1. Prioritize information directly from the provided knowledge base content.
    2. If relevant, cite specific document names or sections you are referencing.
    3. If the knowledge base lacks information to fully answer, clearly state this limitation.
    """

    # Internet search instructions
    INTERNET_SEARCH = """
    When incorporating information from internet searches:
    1. Critically evaluate the credibility and reliability of your sources.
    2. Whenever possible, try to corroborate information across multiple reputable sources.
    3. Clearly indicate when information is derived from search results, and cite the source if appropriate.
    """

    CLEAN_OUTPUT_DIRECTIVE = """
    **CRITICAL: Your response must be clean and professional. Do NOT include any self-referential timestamps, internal thought process tags (like <think>...</think>), or discussion/final answer markers (like \"DiscussionHH:MM:SS\", \"Agent X HH:MM:SS\"). Avoid any phrases like \"As an AI model...\", \"I cannot...\", or disclaimers about your capabilities. Provide direct, concise, and complete answers without unnecessary preamble or meta-commentary.**
    """

    # MCP File Operations Instructions
    MCP_FILE_OPERATIONS = """
    ### Model Context Protocol (MCP) File Operations Guide

    When you need to perform file operations, use the MCP Local Files server with the correct syntax:

    **CORRECT SYNTAX FORMATS:**
    1. List directory contents:
       [MCP:Local Files:list_directory:.]
       [MCP:Local Files:list_directory:/path/to/directory]

    2. Read file contents:
       [MCP:Local Files:read_file:filename.py]
       [MCP:Local Files:read_file:/path/to/file.txt]

    3. Write content to file:
       [MCP:Local Files:write_file:filename.py:your_code_content_here]
       [MCP:Local Files:write_file:snake.py:import pygame\nimport random\n\nclass Game:\n    def __init__(self):\n        self.score = 0]

    4. Create directory:
       [MCP:Local Files:create_directory:new_folder]
       [MCP:Local Files:create_directory:/path/to/new_folder]

    **IMPORTANT NOTES:**
    - Always use colon (:) as separators between MCP components
    - For write_file operations, the content comes after the filename with a colon separator
    - Multi-line content should use \\n for line breaks within the MCP command
    - File paths can be relative (filename.py) or absolute (/full/path/to/file.py)
    - The system will handle syntax validation and encoding automatically
    - Files will be written completely even if they contain syntax errors

    **COMMON EXAMPLES:**
    Creating a simple Python script:
    [MCP:Local Files:write_file:hello.py:print("Hello, World!")\\nprint("MCP file operations work!")]

    Creating a game file:
    [MCP:Local Files:write_file:snake_game.py:import pygame\\n\\nclass SnakeGame:\\n    def __init__(self):\\n        self.width = 800\\n        self.height = 600]

    Reading configuration:
    [MCP:Local Files:read_file:config.json]

    **ERROR PREVENTION:**
    - Don't use parentheses like list_directory() - use colons
    - Don't wrap arguments in quotes within the MCP command
    - Don't use spaces around colons
    - Always include the file extension when writing files
    """

    @classmethod
    def get_agent_instructions(cls, agent_number: int, total_agents: int, internet_enabled: bool) -> str:
        """
        Returns appropriate instructions for an agent based on their position and total agents.
        Creates a collaborative workflow where agents build on each other's work.
        """
        instructions = []
        
        # Add base instructions for all agents
        instructions.append(cls.BASE)
        
        # Add knowledge base instructions
        instructions.append(cls.KNOWLEDGE_BASE_FOCUS)
        
        # Add internet search instructions if enabled
        if internet_enabled:
            instructions.append(cls.INTERNET_SEARCH)

        # Add role-specific instructions based on position and total agents
        if total_agents == 1:
            # Single agent handles everything
            role = """
            As the only agent, your task is to:
            1. Analyze the user's request thoroughly
            2. Provide a comprehensive and accurate response
            3. Ensure your response directly addresses the user's needs
            """
        else:
            # Multi-agent collaborative workflow
            if agent_number == 1:
                # First agent provides foundation
                role = """
                As the first agent, your task is to:
                1. Analyze the user's request thoroughly
                2. Provide an initial, high-quality response to the request
                3. Focus on laying a strong foundation for subsequent agents to build upon
                
                Remember that other agents will be building upon your response, so provide a solid starting point.
                """
            elif agent_number == total_agents:
                # Last agent creates the final response
                role = """
                As the final agent, your task is to:
                1. Review all previous agent responses carefully
                2. Synthesize these responses into a single, cohesive FINAL ANSWER
                3. Ensure the final answer fully addresses the original user request
                   - Incorporate the best elements from all previous responses
                   - Resolve any contradictions or inconsistencies
                   - Fill any remaining information gaps
                
                YOUR RESPONSE WILL BE PRESENTED AS THE FINAL ANSWER TO THE USER.
                """
            else:
                # Middle agents improve and expand
                role = f"""
                As agent {agent_number} of {total_agents}, your task is to:
                1. Review the previous agent responses carefully
                2. Build upon these responses by:
                   - Improving existing content and clarity
                   - Adding relevant missing information
                   - Correcting any inaccuracies or errors
                   - Expanding on valuable ideas or suggestions
                   
                Your work will be further refined by subsequent agents. Focus on making meaningful contributions.
                """
        
        instructions.append(f"\nYOUR SPECIFIC ROLE:\n{role}")
        
        # Add format instructions
        instructions.append(DocumentFormatInstructions.BASE_FORMAT)
        
        # Special instructions for processing previous agent outputs
        if agent_number > 1:
            previous_agent_instructions = """
            IMPORTANT - REVIEWING PREVIOUS AGENT RESPONSES:
            
            1. You will find outputs from previous agents under the 'PREVIOUS AGENT RESPONSES' section in your context.
            2. Carefully review these outputs to understand the work already done.
            3. Your primary goal is to build upon, refine, and improve previous work towards fulfilling the USER'S ORIGINAL REQUEST.
            4. Explicitly reference previous outputs when you are building upon or modifying them.
            5. When appropriate, quote specific parts of previous responses that you are addressing.
            6. **Critically assess if previous agents adequately addressed all aspects of the user's original request, or if they missed any important context from the knowledge base or search results. Incorporate these if relevant.**
            
            Example: "Agent X provided a good starting point on [topic]. To further address the user's need for [specific aspect from original request], I will add..."
            """
            instructions.append(previous_agent_instructions)
        
        # Ensure CLEAN_OUTPUT_DIRECTIVE is always appended at the end
        instructions.append(cls.CLEAN_OUTPUT_DIRECTIVE)
        
        # Combine all instructions into a single string
        return "\n\n".join(instructions)

    @classmethod
    def merge_with_json_instructions(cls, json_instructions: dict, agent_number: int,
                                    total_agents: int, internet_enabled: bool) -> str:
        """
        Merges JSON-loaded custom instructions with default templates.
        Preserves the original method signature for backward compatibility.
        """
        # Get default instructions
        default_instructions = cls.get_agent_instructions(agent_number, total_agents, internet_enabled)

        # If no JSON instructions, return defaults
        if not json_instructions:
            return default_instructions

        # Extract instructions from JSON
        general = json_instructions.get('general', '')
        role_specific = json_instructions.get('roles', {}).get(str(agent_number), '')
        custom = json_instructions.get('custom', {}).get(str(agent_number), '')

        # Build final instructions, prioritizing JSON content
        sections = []

        # Add JSON general instructions if present, otherwise use default base
        if general:
            sections.append(("GENERAL INSTRUCTIONS", general))
        else:
            sections.append(("BASE INSTRUCTIONS", cls.BASE))

        # Add dynamic role-specific instructions based on position
        if role_specific:
            sections.append(("ROLE INSTRUCTIONS", role_specific))
        else:
            # Get dynamic role based on agent position and total agents
            if total_agents == 1:
                role = """
                As the only agent, your task is to:
                1. Analyze the user's request thoroughly
                2. Provide a comprehensive and accurate response
                3. Ensure your response directly addresses the user's needs
                """
            elif agent_number == 1:
                role = """
                As the first agent, your task is to:
                1. Analyze the user's request thoroughly
                2. Provide an initial, high-quality response to the request
                3. Focus on laying a strong foundation for subsequent agents to build upon
                
                Remember that other agents will be building upon your response, so provide a solid starting point.
                """
            elif agent_number == total_agents:
                role = """
                As the final agent, your task is to:
                1. Review all previous agent responses carefully
                2. Synthesize these responses into a single, cohesive FINAL ANSWER
                3. Ensure the final answer fully addresses the original user request
                   - Incorporate the best elements from all previous responses
                   - Resolve any contradictions or inconsistencies
                   - Fill any remaining information gaps
                
                YOUR RESPONSE WILL BE PRESENTED AS THE FINAL ANSWER TO THE USER.
                """
            else:
                role = f"""
                As agent {agent_number} of {total_agents}, your task is to:
                1. Review the previous agent responses carefully
                2. Build upon these responses by:
                   - Improving existing content and clarity
                   - Adding relevant missing information
                   - Correcting any inaccuracies or errors
                   - Expanding on valuable ideas or suggestions
                   
                Your work will be further refined by subsequent agents. Focus on making meaningful contributions.
                """
            
            sections.append(("ROLE INSTRUCTIONS", role))

        # Add custom instructions if present
        if custom:
            sections.append(("CUSTOM INSTRUCTIONS", custom))

        # Add knowledge base instructions
        sections.append(("KNOWLEDGE BASE INSTRUCTIONS", cls.KNOWLEDGE_BASE_FOCUS))
        
        # Add internet search instructions if enabled
        if internet_enabled:
            sections.append(("SEARCH INSTRUCTIONS", cls.INTERNET_SEARCH))

        # Add formatting guidelines
        sections.append(("FORMATTING GUIDELINES", DocumentFormatInstructions.BASE_FORMAT))
        
        # Special instructions for processing previous agent outputs (for agents after the first)
        if agent_number > 1:
            previous_agent_instructions = """
            IMPORTANT - REVIEWING PREVIOUS AGENT RESPONSES:
            
            1. You will find outputs from previous agents under the 'PREVIOUS AGENT RESPONSES' section in your context.
            2. Carefully review these outputs to understand the work already done.
            3. Your primary goal is to build upon, refine, and improve previous work towards fulfilling the USER'S ORIGINAL REQUEST.
            4. Explicitly reference previous outputs when you are building upon or modifying them.
            5. When appropriate, quote specific parts of previous responses that you are addressing.
            6. **Critically assess if previous agents adequately addressed all aspects of the user's original request, or if they missed any important context from the knowledge base or search results. Incorporate these if relevant.**
            
            Example: "Agent X provided a good starting point on [topic]. To further address the user's need for [specific aspect from original request], I will add..."
            """
            sections.append(("PREVIOUS AGENT OUTPUTS", previous_agent_instructions))

        # Ensure CLEAN_OUTPUT_DIRECTIVE is always appended at the end
        sections.append(("CLEAN OUTPUT DIRECTIVE", cls.CLEAN_OUTPUT_DIRECTIVE))

        # Combine all sections
        return "\n\n".join(f"=== {title} ===\n{content}" for title, content in sections)

    def get_agent_instructions_template(self, agent_config, json_instructions=None):
        """
        Get agent instructions with MCP file operations guidance automatically included.
        
        Args:
            agent_config: Agent configuration dictionary
            json_instructions: Optional JSON instructions
            
        Returns:
            Complete instructions string with MCP guidance included
        """
        base_instructions = agent_config.get('instructions', '')
        
        # Always include MCP file operations guidance
        enhanced_instructions = base_instructions + "\n\n" + self.MCP_FILE_OPERATIONS
        
        # Add JSON instructions if provided
        if json_instructions:
            enhanced_instructions += f"\n\n### Additional JSON Instructions:\n{json_instructions}"
        
        return enhanced_instructions