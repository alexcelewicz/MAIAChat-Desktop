#!/usr/bin/env python3
# test_high_speed_performance.py - Test high-speed token streaming performance

import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from worker import Worker
from ui.unified_response_panel import UnifiedResponsePanel

class MockConfigManager:
    """Mock config manager for testing."""
    def get(self, key, default=''):
        return default

class PerformanceTest(QObject):
    """Test class to simulate high-speed token streaming."""
    
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        
        # Create mock worker
        self.worker = Worker(
            prompt="Test prompt",
            general_instructions="Test instructions",
            agents=[{'agent_number': 1, 'provider': 'Google GenAI', 'model': 'gemini-2.5-flash-preview-05-20'}],
            knowledge_base_files=[],
            config_manager=MockConfigManager()
        )
        
        # Create UI panel
        self.response_panel = UnifiedResponsePanel()
        self.response_panel.show()
        
        # Connect signals
        self.worker.update_agents_discussion_signal.connect(
            self.response_panel.add_agent_discussion
        )
        
        # Performance tracking
        self.start_time = None
        self.token_count = 0
        self.update_count = 0

    def simulate_high_speed_streaming(self, tokens_per_second=100, duration=10):
        """Simulate high-speed token streaming."""
        print(f"Starting high-speed streaming test: {tokens_per_second} t/s for {duration} seconds")
        
        self.start_time = time.time()
        self.token_count = 0
        self.update_count = 0
        
        # Calculate timing
        tokens_per_update = max(1, tokens_per_second // 20)  # 20 updates per second
        update_interval = 1.0 / 20  # 50ms between updates
        
        end_time = self.start_time + duration
        
        while time.time() < end_time:
            # Generate mock tokens
            tokens = self._generate_mock_tokens(tokens_per_update)
            
            # Send update
            self.worker.update_agents_discussion_signal.emit(
                tokens, 1, "gemini-2.5-flash-preview-05-20", False
            )
            
            self.token_count += len(tokens)
            self.update_count += 1
            
            # Sleep to maintain target rate
            time.sleep(update_interval)
        
        # Calculate actual performance
        actual_duration = time.time() - self.start_time
        actual_tps = self.token_count / actual_duration
        actual_ups = self.update_count / actual_duration
        
        print(f"\nPerformance Results:")
        print(f"Target: {tokens_per_second} t/s")
        print(f"Actual: {actual_tps:.1f} t/s")
        print(f"Updates: {actual_ups:.1f} updates/sec")
        print(f"Total tokens: {self.token_count}")
        print(f"Total updates: {self.update_count}")
        print(f"Duration: {actual_duration:.2f} seconds")
        
        # Check if we're in high-speed mode
        if hasattr(self.worker, 'high_speed_mode'):
            print(f"High-speed mode: {self.worker.high_speed_mode}")
        
        return actual_tps >= tokens_per_second * 0.8  # 80% of target is acceptable

    def _generate_mock_tokens(self, count):
        """Generate mock token content."""
        words = [
            "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
            "artificial", "intelligence", "machine", "learning", "neural", "network",
            "programming", "software", "development", "algorithm", "data", "analysis"
        ]
        
        import random
        content = ""
        for _ in range(count):
            content += random.choice(words) + " "
        
        return content.strip()

    def run_tests(self):
        """Run a series of performance tests."""
        print("=== High-Speed Token Streaming Performance Tests ===\n")
        
        test_cases = [
            (50, 5),   # 50 t/s for 5 seconds
            (100, 5),  # 100 t/s for 5 seconds
            (200, 5),  # 200 t/s for 5 seconds
            (500, 3),  # 500 t/s for 3 seconds
        ]
        
        results = []
        
        for tps, duration in test_cases:
            print(f"\n--- Test: {tps} tokens/second for {duration} seconds ---")
            
            # Clear the panel
            self.response_panel.clear()
            
            # Run test
            success = self.simulate_high_speed_streaming(tps, duration)
            results.append((tps, success))
            
            # Brief pause between tests
            time.sleep(1)
        
        # Summary
        print(f"\n=== Test Summary ===")
        for tps, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{tps} t/s: {status}")
        
        # Overall result
        all_passed = all(success for _, success in results)
        print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        
        return all_passed

if __name__ == "__main__":
    test = PerformanceTest()
    success = test.run_tests()
    
    # Keep the app running for a moment to see the final state
    time.sleep(2)
    
    sys.exit(0 if success else 1) 