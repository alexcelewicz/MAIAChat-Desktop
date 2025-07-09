"""
Token Manager - Handles token counting and display
"""
from PyQt6.QtCore import QTimer
import logging # Add logging

# Import token counter
try:
    from token_counter import token_counter
except ImportError:
    token_counter = None
    logging.error("Failed to import token_counter.")

class TokenManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.token_counter = token_counter

        # Set up token update timer
        self.token_update_timer = QTimer()
        self.token_update_timer.timeout.connect(self.update_token_display)
        # Update slightly more frequently for better Tokens/s responsiveness
        self.token_update_timer.start(1000) # Update every 1 second

    def connect_to_worker(self, worker):
        """Connect to worker signals for token timing"""
        logging.debug(f"TokenManager.connect_to_worker called with worker: {worker}")
        if worker and self.token_counter:
            logging.debug("Worker and token_counter are valid")
            # Connect to worker signals for token timing
            if hasattr(worker, 'token_generation_started_signal'):
                logging.debug("Worker has token_generation_started_signal")
                try:
                    worker.token_generation_started_signal.connect(self.on_token_generation_started)
                    logging.debug("Successfully connected token_generation_started_signal")
                except Exception as e:
                    logging.error(f"Failed to connect token_generation_started_signal: {str(e)}")
            else:
                logging.debug("Worker does NOT have token_generation_started_signal")

            if hasattr(worker, 'token_generation_ended_signal'):
                logging.debug("Worker has token_generation_ended_signal")
                try:
                    worker.token_generation_ended_signal.connect(self.on_token_generation_ended)
                    logging.debug("Successfully connected token_generation_ended_signal")
                except Exception as e:
                    logging.error(f"Failed to connect token_generation_ended_signal: {str(e)}")
            else:
                logging.debug("Worker does NOT have token_generation_ended_signal")

    def on_token_generation_started(self, timestamp):
        """Handle token generation start signal"""
        if self.token_counter:
            logging.debug(f"Token generation started at {timestamp}")
            self.token_counter.start_generation_timer()

            # Verify that the generation_start_time was properly set
            if self.token_counter.generation_start_time is None:
                logging.error("token_counter.generation_start_time is still None after start_generation_timer")
                # Force set it if it's still None
                self.token_counter.generation_start_time = timestamp
                logging.debug(f"Forced generation_start_time to {timestamp}")
            else:
                logging.debug(f"Verified generation_start_time is set to {self.token_counter.generation_start_time}")

    def on_token_generation_ended(self, timestamp, total_output_tokens):
        """Handle token generation end signal"""
        if self.token_counter:
            logging.debug(f"Token generation ended at {timestamp} with {total_output_tokens} tokens")

            # We don't need to check if generation_start_time is set here
            # The end_generation_timer method will handle missing start time

            # Call end_generation_timer with the total tokens
            self.token_counter.end_generation_timer(total_output_tokens)

            # Update display immediately
            self.update_token_display()

    def update_token_display(self):
        """Update the token count display in the status bar, chat tab, and history tab"""
        if not self.token_counter:
            logging.warning("Token counter not available in TokenManager.")
            return

        try: # Add try-except block for safety during updates
            stats = self.token_counter.get_session_stats()
            input_system_tokens = stats["input_system_tokens"]
            output_tokens = stats["output_tokens"]
            total_tokens = stats["total_tokens"]
            cost = stats["estimated_cost"]
            cost_is_estimated = stats["cost_is_estimated"]

            # Get Tokens/s and its precision
            tokens_per_second = stats.get("tokens_per_second", 0.0)
            tps_precise = stats.get("tokens_per_second_precise", True)

            # --- Prepare display strings with precision indicators ---
            cost_prefix = "~" if cost_is_estimated else ""
            tps_prefix = "" if tps_precise else "~" # Use ~ for estimated Tokens/s

            # Format the token display text
            # Option 1: Simple display
            token_display_text = (
                f"Input+System: {input_system_tokens} | Output: {output_tokens} | "
                f"Total: {total_tokens} | Cost: {cost_prefix}${cost:.4f} | "
                f"Tokens/s: {tps_prefix}{tokens_per_second:.1f}"
            )
            # Option 2: More detailed display (example)
            # precise_total = stats["precise_total_tokens"]
            # total_diff = total_tokens - precise_total
            # total_display = f"{precise_total}" + (f" (+~{total_diff})" if total_diff > 0 else "")
            # token_display_text = (
            #     f"In+Sys: {stats['precise_input_tokens'] + stats['precise_system_tokens']} | "
            #     f"Out: {stats['precise_output_tokens']} | "
            #     f"Total: {total_display} | Cost: {cost_prefix}${cost:.4f} | "
            #     f"Tokens/s: {tps_prefix}{tokens_per_second:.1f}"
            # )
            # --- Choose Option 1 for simplicity for now ---


            # Update the status bar label
            if hasattr(self.main_window, 'token_count_label'):
                self.main_window.token_count_label.setText(f"Usage: {token_display_text}") # Add prefix

            # Update the chat token display (TokenDisplay widget)
            if hasattr(self.main_window, 'chat_token_display') and hasattr(self.main_window.chat_token_display, 'update_token_display'):
                 self.main_window.chat_token_display.update_token_display(
                     input_system_tokens=input_system_tokens,
                     output_tokens=output_tokens,
                     total_tokens=total_tokens,
                     cost=cost, # Pass raw cost
                     tokens_per_second=tokens_per_second, # Pass raw speed
                     cost_is_estimated=cost_is_estimated, # Pass cost precision flag
                     tps_precise=tps_precise # Pass tokens/s precision flag
                 )
            elif hasattr(self.main_window, 'chat_token_display'): # Fallback if it's just a QLabel
                 self.main_window.chat_token_display.setText(token_display_text)


            # Update the token stats text in the history tab
            if hasattr(self.main_window, 'token_stats_text'):
                cost_display = f"{cost_prefix}${cost:.4f}"
                precise_display = "(Precise)" if stats["session_token_count_precise"] else "(Includes Estimates)"

                stats_text = f"<h3>Current Session {precise_display}</h3>"
                stats_text += f"<p><b>Start Time:</b> {stats.get('start_time', 'N/A')}</p>"
                stats_text += f"<p><b>Input Tokens:</b> {stats['input_tokens']} (Precise: {stats['precise_input_tokens']})</p>"
                stats_text += f"<p><b>System Tokens:</b> {stats['system_tokens']} (Precise: {stats['precise_system_tokens']})</p>"
                # stats_text += f"<p><b>Input+System Tokens:</b> {input_system_tokens}</p>" # Redundant if showing components
                stats_text += f"<p><b>Output Tokens:</b> {stats['output_tokens']} (Precise: {stats['precise_output_tokens']})</p>"
                stats_text += f"<p><b>Total Tokens:</b> {total_tokens} (Precise: {stats['precise_total_tokens']})</p>"
                stats_text += f"<p><b>Estimated Cost:</b> {cost_display}</p>" # Show prefix here
                stats_text += f"<p><b>Last Tokens/s:</b> {tps_prefix}{tokens_per_second:.1f}</p>" # Show prefix here

                # Add conversation breakdown if available
                if 'conversation_count' in stats and stats['conversation_count'] > 0:
                    stats_text += f"<h3>Conversations: {stats['conversation_count']}</h3>"
                    # Optionally add per-conversation details here if needed

                # Add history information if available
                history = self.token_counter.history
                if history:
                    stats_text += f"<h3>Previous Sessions</h3>"
                    for i, session in enumerate(reversed(history[-5:])): # Show last 5 sessions
                         # Recalculate display values for history entry
                         hist_precise = (session["input_tokens"] == session["precise_input_tokens"] and
                                        session["system_tokens"] == session["precise_system_tokens"] and
                                        session["output_tokens"] == session["precise_output_tokens"])
                         hist_cost_est = session.get("cost_is_estimated", False)
                         hist_precise_disp = "(Precise)" if hist_precise else "(Includes Estimates)"
                         hist_cost_prefix = "~" if hist_cost_est else ""
                         hist_cost = session.get('estimated_cost', 0)
                         hist_total = session.get('total_tokens', 0)

                         stats_text += f"<p><b>Session {len(history)-i}:</b> {session.get('start_time', 'N/A')} {hist_precise_disp}</p>"
                         stats_text += f"<p style='margin-left: 10px;'>Total Tokens: {hist_total} | Cost: {hist_cost_prefix}${hist_cost:.4f}</p>"


                self.main_window.token_stats_text.setHtml(stats_text)

        except Exception as e:
            logging.error(f"Error updating token display: {e}", exc_info=True)


    def reset_token_counter(self):
        """Reset the token counter for a new session"""
        if self.token_counter:
            logging.info("Resetting token counter session.")
            self.token_counter.reset_session()
            self.update_token_display() # Update display immediately after reset
