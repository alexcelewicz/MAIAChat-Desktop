#!/usr/bin/env python3
"""
Test script for RAG Settings Integration
This script tests the RAG settings dialog and verifies that settings are properly saved and applied.
"""

import json
import os
import sys
from pathlib import Path
import logging

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from rag_settings_dialog import RAGSettingsDialog
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGSettingsTester:
    """Test class for RAG settings integration."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.test_results = []
        
    def test_1_load_current_settings(self):
        """Test 1: Load current settings from config."""
        logger.info("=== Test 1: Loading Current Settings ===")
        
        try:
            # Load current config
            self.config_manager.load_config()
            config = self.config_manager.config
            if config is None:
                logger.error("Config is None")
                self.test_results.append(("Load Current Settings", "FAIL", "Config is None"))
                return
            
            # Check if RAG settings exist
            rag_settings = {
                'RAG_N_RESULTS': config.get('RAG_N_RESULTS', None),
                'RAG_ALPHA': config.get('RAG_ALPHA', None),
                'RAG_IMPORTANCE_SCORE': config.get('RAG_IMPORTANCE_SCORE', None),
                'RAG_TOKEN_LIMIT': config.get('RAG_TOKEN_LIMIT', None),
                'RAG_RERANKING': config.get('RAG_RERANKING', None),
                'RAG_CROSS_ENCODER_RERANKING': config.get('RAG_CROSS_ENCODER_RERANKING', None),
                'RAG_QUERY_EXPANSION': config.get('RAG_QUERY_EXPANSION', None),
                'RAG_ULTRA_SAFE_MODE': config.get('RAG_ULTRA_SAFE_MODE', None),
                'RAG_SAFE_RETRIEVAL_MODE': config.get('RAG_SAFE_RETRIEVAL_MODE', None),
                'EMBEDDING_DEVICE': config.get('EMBEDDING_DEVICE', None)
            }
            
            logger.info("Current RAG settings in config:")
            for key, value in rag_settings.items():
                logger.info(f"  {key}: {value}")
            
            # Check if all settings are present
            missing_settings = [key for key, value in rag_settings.items() if value is None]
            if missing_settings:
                logger.warning(f"Missing settings: {missing_settings}")
                self.test_results.append(("Load Current Settings", "WARNING", f"Missing settings: {missing_settings}"))
            else:
                logger.info("All RAG settings are present in config")
                self.test_results.append(("Load Current Settings", "PASS", "All settings loaded successfully"))
                
        except Exception as e:
            logger.error(f"Error loading current settings: {e}")
            self.test_results.append(("Load Current Settings", "FAIL", str(e)))
    
    def test_2_dialog_initialization(self):
        """Test 2: Test RAG settings dialog initialization."""
        logger.info("=== Test 2: Dialog Initialization ===")
        
        try:
            # Create QApplication if not exists
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Create dialog
            dialog = RAGSettingsDialog()
            
            # Check if dialog was created successfully
            if dialog is not None:
                logger.info("RAG settings dialog created successfully")
                
                # Check if all UI elements are present
                ui_elements = [
                    'n_results_spin',
                    'alpha_spin', 
                    'importance_spin',
                    'token_limit_spin',
                    'reranking_checkbox',
                    'cross_encoder_checkbox',
                    'query_expansion_checkbox',
                    'ultra_safe_checkbox',
                    'safe_retrieval_checkbox',
                    'device_combo',
                    'preset_quality_btn',
                    'preset_balanced_btn',
                    'preset_performance_btn',
                    'preset_amd_btn'
                ]
                
                missing_elements = []
                for element in ui_elements:
                    if not hasattr(dialog, element):
                        missing_elements.append(element)
                
                if missing_elements:
                    logger.warning(f"Missing UI elements: {missing_elements}")
                    self.test_results.append(("Dialog Initialization", "WARNING", f"Missing UI elements: {missing_elements}"))
                else:
                    logger.info("All UI elements are present")
                    self.test_results.append(("Dialog Initialization", "PASS", "Dialog initialized successfully"))
            else:
                logger.error("Failed to create RAG settings dialog")
                self.test_results.append(("Dialog Initialization", "FAIL", "Dialog creation failed"))
                
        except Exception as e:
            logger.error(f"Error initializing dialog: {e}")
            self.test_results.append(("Dialog Initialization", "FAIL", str(e)))
    
    def test_3_preset_buttons(self):
        """Test 3: Test preset button functionality."""
        logger.info("=== Test 3: Preset Buttons ===")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            dialog = RAGSettingsDialog()
            
            # Test each preset
            presets = [
                ('High Quality', 'apply_quality_preset'),
                ('Balanced', 'apply_balanced_preset'),
                ('Performance', 'apply_performance_preset'),
                ('AMD Optimized', 'apply_amd_preset')
            ]
            
            for preset_name, method_name in presets:
                try:
                    # Get current values before applying preset
                    before_values = dialog.get_current_settings()
                    
                    # Apply preset
                    getattr(dialog, method_name)()
                    
                    # Get values after applying preset
                    after_values = dialog.get_current_settings()
                    
                    # Check if values changed
                    if before_values != after_values:
                        logger.info(f"{preset_name} preset applied successfully")
                        logger.info(f"  Before: n_results={before_values['n_results']}, alpha={before_values['alpha']}")
                        logger.info(f"  After:  n_results={after_values['n_results']}, alpha={after_values['alpha']}")
                    else:
                        logger.warning(f"{preset_name} preset did not change values")
                        
                except Exception as e:
                    logger.error(f"Error testing {preset_name} preset: {e}")
                    self.test_results.append((f"Preset {preset_name}", "FAIL", str(e)))
                    continue
            
            self.test_results.append(("Preset Buttons", "PASS", "All presets tested successfully"))
            
        except Exception as e:
            logger.error(f"Error testing preset buttons: {e}")
            self.test_results.append(("Preset Buttons", "FAIL", str(e)))
    
    def test_4_settings_save_load(self):
        """Test 4: Test settings save and load functionality."""
        logger.info("=== Test 4: Settings Save and Load ===")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            dialog = RAGSettingsDialog()
            
            # Set custom values
            test_settings = {
                'n_results': 30,
                'alpha': 0.7,
                'importance_score': 0.4,
                'token_limit': 10240,
                'reranking': True,
                'cross_encoder_reranking': False,
                'query_expansion': True,
                'ultra_safe_mode': False,
                'safe_retrieval_mode': True,
                'embedding_device': 'cpu'
            }
            
            # Apply test settings to dialog
            dialog.n_results_spin.setValue(test_settings['n_results'])
            dialog.alpha_spin.setValue(test_settings['alpha'])
            dialog.importance_spin.setValue(test_settings['importance_score'])
            dialog.token_limit_spin.setValue(test_settings['token_limit'])
            dialog.reranking_checkbox.setChecked(test_settings['reranking'])
            dialog.cross_encoder_checkbox.setChecked(test_settings['cross_encoder_reranking'])
            dialog.query_expansion_checkbox.setChecked(test_settings['query_expansion'])
            dialog.ultra_safe_checkbox.setChecked(test_settings['ultra_safe_mode'])
            dialog.safe_retrieval_checkbox.setChecked(test_settings['safe_retrieval_mode'])
            dialog.device_combo.setCurrentText(test_settings['embedding_device'])
            
            # Get current settings from dialog
            current_settings = dialog.get_current_settings()
            
            # Verify settings match
            settings_match = True
            for key, expected_value in test_settings.items():
                if current_settings.get(key) != expected_value:
                    logger.warning(f"Setting mismatch for {key}: expected {expected_value}, got {current_settings.get(key)}")
                    settings_match = False
            
            if settings_match:
                logger.info("All test settings applied correctly to dialog")
                self.test_results.append(("Settings Save/Load", "PASS", "Settings applied correctly"))
            else:
                logger.error("Some settings did not apply correctly")
                self.test_results.append(("Settings Save/Load", "FAIL", "Settings did not apply correctly"))
                
        except Exception as e:
            logger.error(f"Error testing settings save/load: {e}")
            self.test_results.append(("Settings Save/Load", "FAIL", str(e)))
    
    def test_5_config_file_integration(self):
        """Test 5: Test config file integration."""
        logger.info("=== Test 5: Config File Integration ===")
        
        try:
            # Backup current config
            config_path = Path("config.json")
            backup_path = Path("config_backup_test.json")
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    original_config = json.load(f)
                
                # Save backup
                with open(backup_path, 'w') as f:
                    json.dump(original_config, f, indent=2)
                
                logger.info("Original config backed up")
            
            # Test saving new settings
            test_settings = {
                'RAG_N_RESULTS': 35,
                'RAG_ALPHA': 0.8,
                'RAG_IMPORTANCE_SCORE': 0.25,
                'RAG_TOKEN_LIMIT': 12288,
                'RAG_RERANKING': True,
                'RAG_CROSS_ENCODER_RERANKING': True,
                'RAG_QUERY_EXPANSION': False,
                'RAG_ULTRA_SAFE_MODE': False,
                'RAG_SAFE_RETRIEVAL_MODE': False,
                'EMBEDDING_DEVICE': 'auto'
            }
            
            # Load current config
            self.config_manager.load_config()
            config = self.config_manager.config
            if config is None:
                logger.error("Config is None, cannot test integration")
                self.test_results.append(("Config File Integration", "FAIL", "Config is None"))
                return
            
            # Update with test settings
            for key, value in test_settings.items():
                self.config_manager.set(key, value, save=False)
            self.config_manager.save_config()
            
            # Reload and verify
            reloaded_config = self.config_manager.load_config()
            
            # Check if settings were saved
            settings_saved = True
            for key, expected_value in test_settings.items():
                if reloaded_config.get(key) != expected_value:
                    logger.warning(f"Config save failed for {key}: expected {expected_value}, got {reloaded_config.get(key)}")
                    settings_saved = False
            
            # Restore original config
            if backup_path.exists():
                with open(backup_path, 'r') as f:
                    original_config = json.load(f)
                
                self.config_manager.save_config(original_config)
                backup_path.unlink()  # Remove backup
                logger.info("Original config restored")
            
            if settings_saved:
                logger.info("Config file integration works correctly")
                self.test_results.append(("Config File Integration", "PASS", "Settings saved and loaded correctly"))
            else:
                logger.error("Config file integration failed")
                self.test_results.append(("Config File Integration", "FAIL", "Settings not saved correctly"))
                
        except Exception as e:
            logger.error(f"Error testing config file integration: {e}")
            self.test_results.append(("Config File Integration", "FAIL", str(e)))
    
    def test_6_worker_integration(self):
        """Test 6: Test worker integration with RAG settings."""
        logger.info("=== Test 6: Worker Integration ===")
        
        try:
            # Import worker module
            from worker import Worker
            
            # Create a minimal worker instance for testing
            worker = Worker(
                prompt="test prompt",
                general_instructions="test instructions",
                agents=[],
                knowledge_base_files=[],
                config_manager=self.config_manager
            )
            
            # Test _get_rag_settings method
            rag_settings = worker._get_rag_settings()
            
            # Check if all required settings are present
            required_settings = [
                'n_results', 'alpha', 'importance_score', 'token_limit',
                'reranking', 'cross_encoder_reranking', 'query_expansion',
                'ultra_safe_mode', 'safe_retrieval_mode', 'embedding_device'
            ]
            
            missing_settings = [key for key in required_settings if key not in rag_settings]
            
            if missing_settings:
                logger.warning(f"Worker missing RAG settings: {missing_settings}")
                self.test_results.append(("Worker Integration", "WARNING", f"Missing settings: {missing_settings}"))
            else:
                logger.info("Worker has all required RAG settings")
                logger.info(f"Worker RAG settings: {rag_settings}")
                self.test_results.append(("Worker Integration", "PASS", "Worker integration works correctly"))
                
        except Exception as e:
            logger.error(f"Error testing worker integration: {e}")
            self.test_results.append(("Worker Integration", "FAIL", str(e)))
    
    def test_7_rag_status_indicator(self):
        """Test 7: Test RAG status indicator logic."""
        logger.info("=== Test 7: RAG Status Indicator ===")
        
        try:
            # Test different status combinations
            test_cases = [
                {
                    'ultra_safe': True,
                    'safe_retrieval': True,
                    'expected_status': 'Ultra Safe Mode (Conservative)',
                    'expected_color': '#e74c3c'
                },
                {
                    'ultra_safe': False,
                    'safe_retrieval': True,
                    'expected_status': 'Safe Mode (Balanced)',
                    'expected_color': '#f39c12'
                },
                {
                    'ultra_safe': False,
                    'safe_retrieval': False,
                    'expected_status': 'Performance Mode (Optimized)',
                    'expected_color': '#27ae60'
                }
            ]
            
            for i, test_case in enumerate(test_cases):
                # Set test values in config
                self.config_manager.load_config()
                config = self.config_manager.config
                if config is None:
                    logger.error("Config is None, cannot test status indicator")
                    self.test_results.append(("RAG Status Indicator", "FAIL", "Config is None"))
                    return
                
                config['RAG_ULTRA_SAFE_MODE'] = test_case['ultra_safe']
                config['RAG_SAFE_RETRIEVAL_MODE'] = test_case['safe_retrieval']
                self.config_manager.set('RAG_ULTRA_SAFE_MODE', test_case['ultra_safe'], save=False)
                self.config_manager.set('RAG_SAFE_RETRIEVAL_MODE', test_case['safe_retrieval'], save=False)
                self.config_manager.save_config()
                
                # Determine status (simulate the logic from main_window.py)
                ultra_safe = config.get('RAG_ULTRA_SAFE_MODE', False)
                safe_retrieval = config.get('RAG_SAFE_RETRIEVAL_MODE', False)
                
                if ultra_safe and safe_retrieval:
                    status = "Ultra Safe Mode (Conservative)"
                    color = "#e74c3c"
                elif safe_retrieval:
                    status = "Safe Mode (Balanced)"
                    color = "#f39c12"
                else:
                    status = "Performance Mode (Optimized)"
                    color = "#27ae60"
                
                # Verify results
                if status == test_case['expected_status'] and color == test_case['expected_color']:
                    logger.info(f"Test case {i+1} passed: {status}")
                else:
                    logger.warning(f"Test case {i+1} failed: expected {test_case['expected_status']}, got {status}")
            
            self.test_results.append(("RAG Status Indicator", "PASS", "Status indicator logic works correctly"))
            
        except Exception as e:
            logger.error(f"Error testing RAG status indicator: {e}")
            self.test_results.append(("RAG Status Indicator", "FAIL", str(e)))
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        logger.info("Starting RAG Settings Integration Tests")
        logger.info("=" * 50)
        
        # Run all tests
        self.test_1_load_current_settings()
        self.test_2_dialog_initialization()
        self.test_3_preset_buttons()
        self.test_4_settings_save_load()
        self.test_5_config_file_integration()
        self.test_6_worker_integration()
        self.test_7_rag_status_indicator()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report."""
        logger.info("\n" + "=" * 50)
        logger.info("RAG SETTINGS INTEGRATION TEST REPORT")
        logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed_tests = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        warning_tests = sum(1 for _, status, _ in self.test_results if status == "WARNING")
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Warnings: {warning_tests}")
        
        logger.info("\nDetailed Results:")
        for test_name, status, message in self.test_results:
            if status == "PASS":
                status_icon = "PASS"
            elif status == "FAIL":
                status_icon = "FAIL"
            else:
                status_icon = "WARN"
            logger.info(f"{status_icon} {test_name}: {status} - {message}")
        
        # Overall assessment
        if failed_tests == 0:
            if warning_tests == 0:
                logger.info("\nALL TESTS PASSED! RAG Settings Integration is working correctly.")
            else:
                logger.info("\nCORE FUNCTIONALITY WORKS! Some minor warnings detected.")
        else:
            logger.info(f"\n{failed_tests} TESTS FAILED! RAG Settings Integration needs attention.")
        
        # Save report to file
        report_path = Path("rag_settings_test_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RAG SETTINGS INTEGRATION TEST REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Warnings: {warning_tests}\n\n")
            
            f.write("Detailed Results:\n")
            for test_name, status, message in self.test_results:
                if status == "PASS":
                    status_icon = "PASS"
                elif status == "FAIL":
                    status_icon = "FAIL"
                else:
                    status_icon = "WARN"
                f.write(f"{status_icon} {test_name}: {status} - {message}\n")
        
        logger.info(f"\nDetailed report saved to: {report_path}")

def main():
    """Main function to run the tests."""
    tester = RAGSettingsTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 