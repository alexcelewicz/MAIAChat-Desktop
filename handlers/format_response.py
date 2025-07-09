"""
Format Response - Handles formatting of agent responses and final answers
"""

class FormatResponse:
    def __init__(self, main_window):
        self.main_window = main_window

    def format_agent_response(self, agent_number, model, content, is_first_chunk=False):
        """
        Format an agent's response for display in the unified response panel.
        Now supports incremental formatting for streaming responses.
        
        Args:
            agent_number: The agent number
            model: The model name
            content: The text content to format
            is_first_chunk: Whether this is the first chunk of a response
        
        Returns:
            Formatted HTML content ready for insertion
        """
        # If this is the first chunk, add the agent header
        if is_first_chunk:
            agent_header = self._create_agent_header(agent_number, model)
            # Format the content using TextFormatter
            formatted_content = self.text_formatter.format_text_content(content)
            return f"{agent_header}{formatted_content}"
        else:
            # For subsequent chunks, just format the content
            return self.text_formatter.format_text_content(content)

    def format_final_response(self, content):
        """Format the final response with styling"""
        import json

        # Check if content is JSON
        try:
            if content.strip().startswith('{') and content.strip().endswith('}'):
                # Try to parse as JSON
                json_data = json.loads(content)
                if 'response' in json_data:
                    # Extract the response field from JSON
                    content = json_data['response']
        except (json.JSONDecodeError, ValueError, TypeError):
            # Not valid JSON or doesn't have a response field, continue with original content
            pass

        # Check if content is already HTML formatted
        if content.strip().startswith('<div') or content.strip().startswith('<p') or content.strip().startswith('<span'):
            # Already formatted, just wrap it in our container
            formatted_content = content
        else:
            # Format the content
            formatted_content = self.main_window.text_formatter.format_text_content(content)

        # Wrap in a styled div with word-wrap property to ensure text wrapping
        # Use a simpler approach to avoid potential issues with multi-line strings
        return (
            '<div style="'
            'background-color: #FFFFFF; '
            'border: 1px solid #2196F3; '
            'border-radius: 8px; '
            'padding: 16px; '
            'margin: 16px 0; '
            'font-family: Arial, sans-serif; '
            'font-size: 14px; '
            'line-height: 1.6; '
            'color: #212121; '
            'word-wrap: break-word; '
            'overflow-wrap: break-word; '
            'white-space: normal; '
            'overflow-x: auto; '
            'max-width: 100%; '
            '">' +
            formatted_content +
            '</div>'
        )

    def _create_agent_header(self, agent_number, model):
        # Define colors for different agents
        agent_colors = [
            "#1976D2",  # Blue
            "#388E3C",  # Green
            "#D32F2F",  # Red
            "#7B1FA2",  # Purple
            "#F57C00",  # Orange
        ]

        # Get color for this agent (cycle through colors if more than 5 agents)
        color = agent_colors[(agent_number - 1) % len(agent_colors)]

        # Create header
        return f"<b style='color: {color};'>Agent {agent_number} ({model}):</b> "
