# signal_manager.py
from PyQt6.QtCore import QObject, pyqtSignal

class SignalManager(QObject):
    # Define signals
    update_agents_discussion = pyqtSignal(str, int, str, bool)
    # update_final_answer = pyqtSignal(str)  # REMOVED: Final answer functionality
    update_terminal_console = pyqtSignal(str)
    update_conversation_history = pyqtSignal(list)
    update_conversation_id = pyqtSignal(str)
    discussion_completed = pyqtSignal()
    error = pyqtSignal(str)
    token_generation_started = pyqtSignal(float)
    token_generation_ended = pyqtSignal(float, int)