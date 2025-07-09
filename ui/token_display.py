"""
Token Display component.
This component displays token usage information.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class TokenDisplay(QWidget):
    """Widget for displaying token usage information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initialize the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Token usage label
        self.token_label = QLabel("Token Usage: Input+System: 0 | Output: 0 | Total: 0 | Cost: $0.0000 | Tokens/s: 0.0")
        self.token_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #424242;
                padding: 2px;
            }
        """)

        layout.addWidget(self.token_label)

    def update_token_display(self, input_system_tokens, output_tokens, total_tokens, cost, tokens_per_second, cost_is_estimated=False, tps_precise=True):
        """Update the token display with new information, including precision hints."""
        cost_prefix = "~" if cost_is_estimated else ""
        tps_prefix = "" if tps_precise else "~"

        # Update the label text
        self.token_label.setText(
            f"Token Usage: Input+System: {input_system_tokens} | Output: {output_tokens} | "
            f"Total: {total_tokens} | Cost: {cost_prefix}${cost:.4f} | "
            f"Tokens/s: {tps_prefix}{tokens_per_second:.1f}"
        )
        # Optionally, change style based on precision
        # style = "color: #888888;" if cost_is_estimated or not tps_precise else "color: #424242;"
        # self.token_label.setStyleSheet(f"QLabel {{ font-size: 12px; padding: 2px; {style} }}")

        # Make sure TokenManager calls this updated method, potentially passing precision flags
        # Example call in TokenManager:
        # self.main_window.chat_token_display.update_token_display(
        #     ...,
        #     cost=cost,
        #     tokens_per_second=tokens_per_second,
        #     cost_is_estimated=cost_is_estimated, # Pass flag
        #     tps_precise=tps_precise # Pass flag
        # )
