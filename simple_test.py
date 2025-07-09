#!/usr/bin/env python3
"""
Simple Calculator - Basic Test File for Multi-Agent Development

This program provides a simple command-line calculator with basic
arithmetic operations (addition, subtraction, multiplication, division).
It demonstrates proper input validation and error handling.
"""

def add(a, b):
    """Add two numbers and return the result."""
    return a + b

def subtract(a, b):
    """Subtract b from a and return the result."""
    return a - b

def multiply(a, b):
    """Multiply two numbers and return the result."""
    return a * b

def divide(a, b):
    """
    Divide a by b and return the result.
    
    Raises:
        ValueError: If division by zero is attempted
    """
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

def validate_number_input(prompt):
    """
    Validate user input to ensure it's a valid number.
    
    Parameters:
        prompt (str): The message to display to the user
        
    Returns:
        float: The validated number input
    """
    while True:
        try:
            value = float(input(prompt))
            return value
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def calculator():
    """Run the interactive calculator program."""
    print("Simple Calculator")
    print("Operations: add (+), subtract (-), multiply (*), divide (/)")
    print("Enter 'q' to quit")
    
    while True:
        # Get operation
        operation = input("\nEnter operation (+, -, *, /) or 'q' to quit: ")
        
        if operation.lower() == 'q':
            print("Calculator exiting. Goodbye!")
            break
            
        if operation not in ['+', '-', '*', '/'