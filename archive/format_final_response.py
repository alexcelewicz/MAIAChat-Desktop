"""
This file contains the updated format_final_response method for worker.py.
"""

def format_final_response(response):
    """Format the final response with consistent styling and better code formatting."""
    return f"""
    <div style='
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
        font-family: Arial, sans-serif;
    '>
        <h3 style='color: #2c3e50; margin-top: 0;'>Final Answer</h3>
        <div style='
            background-color: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        '>
            {response}
        </div>
    </div>
    """
