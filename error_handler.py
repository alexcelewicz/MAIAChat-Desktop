# error_handler.py
from PyQt6.QtWidgets import QMessageBox
from dataclasses import dataclass
from typing import Optional

@dataclass
class ErrorInfo:
    title: str
    user_message: str
    log_message: str
    suggestion: str = ""

ERROR_CODES = {
    "API_KEY_MISSING": ErrorInfo(
        title="API Key Missing",
        user_message="The API key for '{context}' is missing.",
        log_message="API key not found for {context}.",
        suggestion="Please add the required key in the Settings > API Settings tab."
    ),
    "CONNECTION_FAILED": ErrorInfo(
        title="Connection Failed",
        user_message="Could not connect to the service at '{context}'.",
        log_message="Connection failed for {context}.",
        suggestion="Please check your internet connection and ensure the service/server is running and the URL is correct in General Settings."
    ),
    "FILE_PERMISSION_ERROR": ErrorInfo(
        title="File Permission Error",
        user_message="Cannot access file '{context}' due to permission restrictions.",
        log_message="File permission error for {context}.",
        suggestion="Please check file permissions or try running the application as administrator."
    ),
    "RAG_PROCESSING_FAILED": ErrorInfo(
        title="Document Processing Failed",
        user_message="Failed to process document '{context}'.",
        log_message="RAG processing failed for {context}.",
        suggestion="Please check if the file is corrupted or in an unsupported format. Try converting to a different format."
    ),
    "EMBEDDING_GENERATION_FAILED": ErrorInfo(
        title="Embedding Generation Failed",
        user_message="Could not generate embeddings for '{context}'.",
        log_message="Embedding generation failed for {context}.",
        suggestion="Please check your embedding model configuration and API connectivity in Settings."
    ),
    "MODEL_LOADING_FAILED": ErrorInfo(
        title="Model Loading Failed",
        user_message="Failed to load model '{context}'.",
        log_message="Model loading failed for {context}.",
        suggestion="Please check if the model is available and your configuration is correct in Model Settings."
    ),
    "KNOWLEDGE_BASE_ERROR": ErrorInfo(
        title="Knowledge Base Error",
        user_message="Error accessing knowledge base: '{context}'.",
        log_message="Knowledge base error: {context}.",
        suggestion="Please check if the knowledge base directory is accessible and has sufficient disk space."
    ),
    "CONFIGURATION_ERROR": ErrorInfo(
        title="Configuration Error",
        user_message="Configuration error: '{context}'.",
        log_message="Configuration error: {context}.",
        suggestion="Please check your configuration files and reset to defaults if necessary."
    ),
    "NETWORK_TIMEOUT": ErrorInfo(
        title="Network Timeout",
        user_message="Request to '{context}' timed out.",
        log_message="Network timeout for {context}.",
        suggestion="Please check your internet connection and try again. You may also increase timeout settings."
    ),
    "INVALID_INPUT": ErrorInfo(
        title="Invalid Input",
        user_message="Invalid input provided: '{context}'.",
        log_message="Invalid input: {context}.",
        suggestion="Please check your input and ensure it meets the required format."
    )
}

def show_error_message(parent, error_code: str, context: Optional[str] = None, details: Optional[str] = None):
    """
    Show a user-friendly error dialog with actionable suggestions.
    
    Args:
        parent: Parent widget for the dialog
        error_code: Error code from ERROR_CODES
        context: Context information to insert into the error message
        details: Additional technical details to show
    """
    error_info = ERROR_CODES.get(error_code)
    if not error_info:
        # Fallback for unknown error codes
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Unknown Error")
        msg_box.setText(f"An unknown error occurred: {error_code}")
        if context:
            msg_box.setInformativeText(f"Context: {context}")
        if details:
            msg_box.setDetailedText(details)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        return

    # Format the user message with context
    user_msg = error_info.user_message.format(context=context) if context else error_info.user_message
    
    # Create the message box
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(error_info.title)
    msg_box.setText(user_msg)
    
    # Add suggestion as informative text
    if error_info.suggestion:
        msg_box.setInformativeText(error_info.suggestion)
    
    # Add technical details if provided
    if details:
        msg_box.setDetailedText(f"Technical Details:\n{details}")
    
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()

def show_warning_message(parent, title: str, message: str, suggestion: Optional[str] = None):
    """
    Show a warning dialog with optional suggestion.
    
    Args:
        parent: Parent widget for the dialog
        title: Warning title
        message: Warning message
        suggestion: Optional suggestion for the user
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if suggestion:
        msg_box.setInformativeText(suggestion)
    
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()

def show_info_message(parent, title: str, message: str, details: Optional[str] = None):
    """
    Show an information dialog.
    
    Args:
        parent: Parent widget for the dialog
        title: Information title
        message: Information message
        details: Optional additional details
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    if details:
        msg_box.setInformativeText(details)
    
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    msg_box.exec()

def get_error_log_message(error_code: str, context: Optional[str] = None) -> str:
    """
    Get the formatted log message for an error code.
    
    Args:
        error_code: Error code from ERROR_CODES
        context: Context information to insert into the log message
        
    Returns:
        Formatted log message
    """
    error_info = ERROR_CODES.get(error_code)
    if not error_info:
        return f"Unknown error: {error_code}"
    
    return error_info.log_message.format(context=context) if context else error_info.log_message 