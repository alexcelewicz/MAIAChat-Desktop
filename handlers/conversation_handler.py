"""
Conversation Handler - Manages conversation-related functionality
"""
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem
from PyQt6.QtCore import Qt
from conversation_manager import ConversationManager
from pathlib import Path

class ConversationHandler:
    def __init__(self, main_window):
        self.main_window = main_window
        self.conversation_manager = ConversationManager()
        self.current_conversation_id = None
        self.conversation_history = []

        # Ensure conversation history directory exists
        Path("conversation_history").mkdir(exist_ok=True)

    def refresh_conversation_list(self):
        """Refresh the conversation list"""
        self.main_window.conversation_list.clear()
        conversations = self.conversation_manager.get_conversation_list()

        for conv in conversations:
            # Format the timestamp
            timestamp = conv["timestamp"]
            if "T" in timestamp:
                date_part, time_part = timestamp.split("T")
                time_part = time_part.split(".")[0]  # Remove milliseconds
                formatted_time = f"{date_part} {time_part}"
            else:
                formatted_time = timestamp

            # Format the item text
            item_text = f"{formatted_time} - {conv['message_count']} messages\n"
            item_text += f"Tokens: {conv['total_tokens']} | Cost: ${conv['estimated_cost']:.4f}\n"
            item_text += f"{conv['first_message']}"

            # Create the item and store the conversation ID
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, conv["id"])
            self.main_window.conversation_list.addItem(item)

    def load_selected_conversation(self):
        """Load the selected conversation"""
        selected_items = self.main_window.conversation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "No Selection", "Please select a conversation to load.")
            return

        conversation_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not conversation_id:
            return

        # Load the conversation
        if self.conversation_manager.load_conversation(conversation_id):
            # Switch to chat tab
            self.main_window.tab_widget.setCurrentIndex(0)

            # Clear current display
            self.main_window.ui.main_layout.get_unified_response_panel().clear()

            # Update conversation history for follow-up prompts
            self.conversation_history = []

            # Display the conversation
            messages = self.conversation_manager.current_conversation["messages"]

            # First, build the conversation history for the worker
            for msg in messages:
                self.conversation_history.append(f"{msg['role']}: {msg['content']}")

            # Then display all messages in the UI
            for msg in messages:
                if msg["role"] == "user":
                    # Display user message
                    self.main_window.ui.main_layout.get_unified_response_panel().unified_response.append(f"<b>User:</b> {msg['content']}")
                elif msg["role"] == "assistant":
                    # Display final answer
                    formatted_final = self.main_window.format_response.format_final_response(msg["content"])
                    self.main_window.ui.main_layout.get_unified_response_panel().add_final_answer(formatted_final)
                elif msg["role"].startswith("agent_"):
                    # Display agent message
                    agent_num = msg["role"].replace("agent_", "")
                    model = msg["metadata"].get("model", "Unknown") if "metadata" in msg else "Unknown"

                    # Format agent response
                    formatted_response = self.main_window.format_response.format_agent_response(
                        int(agent_num),
                        model,
                        msg["content"],
                        is_first_chunk=True
                    )
                    self.main_window.ui.main_layout.get_unified_response_panel().unified_response.append(formatted_response)

            # Store the current conversation ID for follow-up prompts
            self.current_conversation_id = conversation_id
            # Also update the main window's conversation ID
            self.main_window.current_conversation_id = conversation_id

            # Load token usage data if available and update current session
            if hasattr(self.main_window, 'token_counter') and self.main_window.token_counter:
                loaded_token_usage = self.conversation_manager.current_conversation.get("token_usage", {})
                if loaded_token_usage:
                    # Reset session first to clear previous data
                    self.main_window.token_counter.reset_session()
                    # Directly set the current session's conversation data
                    conv_session_data = {
                        "input_tokens": loaded_token_usage.get("input_tokens", 0),
                        "system_tokens": loaded_token_usage.get("system_tokens", 0),
                        "output_tokens": loaded_token_usage.get("output_tokens", 0),
                        "total_tokens": loaded_token_usage.get("total_tokens", 0),
                        "estimated_cost": loaded_token_usage.get("estimated_cost", 0.0),
                        "precise_input_tokens": loaded_token_usage.get("precise_input_tokens", 0),
                        "precise_system_tokens": loaded_token_usage.get("precise_system_tokens", 0),
                        "precise_output_tokens": loaded_token_usage.get("precise_output_tokens", 0),
                        "precise_total_tokens": loaded_token_usage.get("precise_total_tokens", 0),
                        "cost_is_estimated": loaded_token_usage.get("cost_is_estimated", False),
                        "exchanges": self.conversation_manager.current_conversation.get("exchanges", []) # Load all exchanges
                    }
                    self.main_window.token_counter.current_session["conversations"][conversation_id] = conv_session_data
                    # Recalculate session totals from this newly set conversation
                    self.main_window.token_counter._recalculate_session_totals(self.main_window.token_counter.current_session)
                    self.main_window.update_token_display()

            # Enable follow-up button
            self.main_window.follow_up_btn.setEnabled(True)

            # Show success message
            self.main_window.show_success_message(f"Loaded conversation from {conversation_id}")
        else:
            QMessageBox.warning(self.main_window, "Error", f"Failed to load conversation {conversation_id}")

    def delete_selected_conversation(self):
        """Delete the selected conversation"""
        selected_items = self.main_window.conversation_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main_window, "No Selection", "Please select a conversation to delete.")
            return

        conversation_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not conversation_id:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Deletion",
            f"Are you sure you want to delete this conversation?\n\n{selected_items[0].text()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete the conversation
            if self.conversation_manager.delete_conversation(conversation_id):
                # Refresh the list
                self.refresh_conversation_list()
                self.main_window.show_success_message(f"Deleted conversation {conversation_id}")
            else:
                QMessageBox.warning(self.main_window, "Error", f"Failed to delete conversation {conversation_id}")

    def delete_all_conversations(self):
        """Delete all conversations"""
        # Confirm deletion
        reply = QMessageBox.question(
            self.main_window,
            "Confirm Deletion",
            "Are you sure you want to delete ALL conversations?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Delete all conversations
            success_count, fail_count = self.conversation_manager.delete_all_conversations()

            # Refresh the list
            self.refresh_conversation_list()

            if fail_count == 0:
                self.main_window.show_success_message(f"Successfully deleted {success_count} conversations")
            else:
                QMessageBox.warning(
                    self.main_window,
                    "Partial Success",
                    f"Deleted {success_count} conversations, but failed to delete {fail_count} conversations."
                )

    def clear_conversation(self):
        """Clear the current conversation"""
        self.conversation_history = []
        self.main_window.ui.main_layout.get_unified_response_panel().clear()
        self.main_window.input_prompt.clear()
