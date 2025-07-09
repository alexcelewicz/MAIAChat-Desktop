#!/usr/bin/env python3
"""
RAG Settings Dialog for Python Agents
This dialog allows users to configure RAG quality settings through the UI.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, 
    QDialogButtonBox, QGroupBox, QScrollArea, QWidget,
    QFrame, QSlider, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
import logging
from pathlib import Path
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class RAGSettingsDialog(QDialog):
    """Dialog for configuring RAG settings."""
    
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings are changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.initUI()
        self.load_current_settings()
        
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle("RAG Quality Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Create scroll area for better UX
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Add description
        description = QLabel(
            "Configure RAG (Retrieval-Augmented Generation) quality settings. "
            "These settings affect how detailed and comprehensive your RAG responses will be."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #b0d4f1;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                font-size: 13px;
                color: #2c3e50;
            }
        """)
        content_layout.addWidget(description)
        
        # Quality Settings Group
        quality_group = QGroupBox("Quality Settings")
        quality_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        quality_layout = QFormLayout(quality_group)
        
        # Number of Results
        self.n_results_spin = QSpinBox()
        self.n_results_spin.setRange(5, 50)
        self.n_results_spin.setValue(25)
        self.n_results_spin.setToolTip("Number of chunks to retrieve from knowledge base (higher = more comprehensive)")
        quality_layout.addRow("Number of Results:", self.n_results_spin)
        
        # Alpha Parameter
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.0, 1.0)
        self.alpha_spin.setSingleStep(0.1)
        self.alpha_spin.setValue(0.6)
        self.alpha_spin.setToolTip("Balance between semantic search (higher) and keyword search (lower)")
        quality_layout.addRow("Alpha (Semantic Balance):", self.alpha_spin)
        
        # Importance Score Threshold
        self.importance_spin = QDoubleSpinBox()
        self.importance_spin.setRange(0.0, 1.0)
        self.importance_spin.setSingleStep(0.1)
        self.importance_spin.setValue(0.3)
        self.importance_spin.setToolTip("Minimum importance score for chunks (lower = more results)")
        quality_layout.addRow("Importance Score Threshold:", self.importance_spin)
        
        # Token Limit
        self.token_limit_spin = QSpinBox()
        self.token_limit_spin.setRange(2048, 16384)
        self.token_limit_spin.setSingleStep(1024)
        self.token_limit_spin.setValue(8192)
        self.token_limit_spin.setToolTip("Maximum tokens for RAG content (higher = more context)")
        quality_layout.addRow("Token Limit:", self.token_limit_spin)
        
        content_layout.addWidget(quality_group)
        
        # Advanced Settings Group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_group.setStyleSheet(quality_group.styleSheet())
        advanced_layout = QFormLayout(advanced_group)
        
        # Reranking
        self.reranking_checkbox = QCheckBox("Enable Reranking")
        self.reranking_checkbox.setChecked(True)
        self.reranking_checkbox.setToolTip("Enable hybrid reranking for better result quality")
        advanced_layout.addRow("", self.reranking_checkbox)
        
        # Cross-encoder Reranking
        self.cross_encoder_checkbox = QCheckBox("Enable Cross-encoder Reranking")
        self.cross_encoder_checkbox.setChecked(True)
        self.cross_encoder_checkbox.setToolTip("Enable cross-encoder reranking (slower but more accurate)")
        advanced_layout.addRow("", self.cross_encoder_checkbox)
        
        # Query Expansion
        self.query_expansion_checkbox = QCheckBox("Enable Query Expansion")
        self.query_expansion_checkbox.setChecked(True)
        self.query_expansion_checkbox.setToolTip("Expand queries with synonyms and related terms")
        advanced_layout.addRow("", self.query_expansion_checkbox)
        
        content_layout.addWidget(advanced_group)
        
        # System Settings Group
        system_group = QGroupBox("System Settings")
        system_group.setStyleSheet(quality_group.styleSheet())
        system_layout = QFormLayout(system_group)
        
        # Safe Modes
        self.ultra_safe_checkbox = QCheckBox("Ultra Safe Mode")
        self.ultra_safe_checkbox.setToolTip("Enable ultra safe mode for maximum stability (may reduce quality)")
        system_layout.addRow("", self.ultra_safe_checkbox)
        
        self.safe_retrieval_checkbox = QCheckBox("Safe Retrieval Mode")
        self.safe_retrieval_checkbox.setToolTip("Enable safe retrieval mode (reduces results for stability)")
        system_layout.addRow("", self.safe_retrieval_checkbox)
        
        # Embedding Device
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "auto", "cuda", "mps"])
        self.device_combo.setToolTip("Device for embedding computation (auto = auto-detect)")
        system_layout.addRow("Embedding Device:", self.device_combo)
        
        content_layout.addWidget(system_group)
        
        # Preset Buttons
        preset_group = QGroupBox("Quick Presets")
        preset_group.setStyleSheet(quality_group.styleSheet())
        preset_layout = QHBoxLayout(preset_group)
        
        # Preset buttons
        self.preset_quality_btn = QPushButton("High Quality")
        self.preset_quality_btn.setToolTip("Optimize for maximum response quality")
        self.preset_quality_btn.clicked.connect(self.apply_quality_preset)
        
        self.preset_balanced_btn = QPushButton("Balanced")
        self.preset_balanced_btn.setToolTip("Balance between quality and performance")
        self.preset_balanced_btn.clicked.connect(self.apply_balanced_preset)
        
        self.preset_performance_btn = QPushButton("Performance")
        self.preset_performance_btn.setToolTip("Optimize for speed and stability")
        self.preset_performance_btn.clicked.connect(self.apply_performance_preset)
        
        self.preset_amd_btn = QPushButton("AMD Optimized")
        self.preset_amd_btn.setToolTip("Optimize for AMD Ryzen systems")
        self.preset_amd_btn.clicked.connect(self.apply_amd_preset)
        
        preset_layout.addWidget(self.preset_quality_btn)
        preset_layout.addWidget(self.preset_balanced_btn)
        preset_layout.addWidget(self.preset_performance_btn)
        preset_layout.addWidget(self.preset_amd_btn)
        
        content_layout.addWidget(preset_group)
        
        # Current Settings Display
        current_group = QGroupBox("Current Settings")
        current_group.setStyleSheet(quality_group.styleSheet())
        current_layout = QVBoxLayout(current_group)
        
        self.current_settings_text = QTextEdit()
        self.current_settings_text.setMaximumHeight(100)
        self.current_settings_text.setReadOnly(True)
        self.current_settings_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        current_layout.addWidget(self.current_settings_text)
        
        content_layout.addWidget(current_group)
        
        # Add content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Reset
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset_to_defaults)
        
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
        
        # Connect signals for real-time updates
        self.connect_signals()
        
    def connect_signals(self):
        """Connect signals for real-time updates."""
        self.n_results_spin.valueChanged.connect(self.update_current_settings_display)
        self.alpha_spin.valueChanged.connect(self.update_current_settings_display)
        self.importance_spin.valueChanged.connect(self.update_current_settings_display)
        self.token_limit_spin.valueChanged.connect(self.update_current_settings_display)
        self.reranking_checkbox.toggled.connect(self.update_current_settings_display)
        self.cross_encoder_checkbox.toggled.connect(self.update_current_settings_display)
        self.query_expansion_checkbox.toggled.connect(self.update_current_settings_display)
        self.ultra_safe_checkbox.toggled.connect(self.update_current_settings_display)
        self.safe_retrieval_checkbox.toggled.connect(self.update_current_settings_display)
        self.device_combo.currentTextChanged.connect(self.update_current_settings_display)
        
    def load_current_settings(self):
        """Load current settings from config."""
        try:
            # Load from config.json
            config_path = Path("config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                # Load all settings if present, else use defaults
                self.n_results_spin.setValue(config.get('RAG_N_RESULTS', 25))
                self.alpha_spin.setValue(config.get('RAG_ALPHA', 0.6))
                self.importance_spin.setValue(config.get('RAG_IMPORTANCE_SCORE', 0.3))
                self.token_limit_spin.setValue(config.get('RAG_TOKEN_LIMIT', 8192))
                self.reranking_checkbox.setChecked(config.get('RAG_RERANKING', True))
                self.cross_encoder_checkbox.setChecked(config.get('RAG_CROSS_ENCODER_RERANKING', True))
                self.query_expansion_checkbox.setChecked(config.get('RAG_QUERY_EXPANSION', True))
                self.ultra_safe_checkbox.setChecked(config.get('RAG_ULTRA_SAFE_MODE', False))
                self.safe_retrieval_checkbox.setChecked(config.get('RAG_SAFE_RETRIEVAL_MODE', False))
                device = config.get('EMBEDDING_DEVICE', 'cpu')
                index = self.device_combo.findText(device)
                if index >= 0:
                    self.device_combo.setCurrentIndex(index)
            else:
                # Defaults if config does not exist
                self.n_results_spin.setValue(25)
                self.alpha_spin.setValue(0.6)
                self.importance_spin.setValue(0.3)
                self.token_limit_spin.setValue(8192)
                self.reranking_checkbox.setChecked(True)
                self.cross_encoder_checkbox.setChecked(True)
                self.query_expansion_checkbox.setChecked(True)
                self.ultra_safe_checkbox.setChecked(False)
                self.safe_retrieval_checkbox.setChecked(False)
                self.device_combo.setCurrentText("cpu")
            self.update_current_settings_display()
        except Exception as e:
            logger.error(f"Error loading current settings: {e}")
    
    def update_current_settings_display(self):
        """Update the current settings display."""
        settings = self.get_current_settings()
        display_text = f"""Quality Settings:
• Number of Results: {settings['n_results']}
• Alpha (Semantic Balance): {settings['alpha']}
• Importance Score Threshold: {settings['importance_score']}
• Token Limit: {settings['token_limit']}

Advanced Settings:
• Reranking: {'✓' if settings['reranking'] else '✗'}
• Cross-encoder Reranking: {'✓' if settings['cross_encoder_reranking'] else '✗'}
• Query Expansion: {'✓' if settings['query_expansion'] else '✗'}

System Settings:
• Ultra Safe Mode: {'✓' if settings['ultra_safe_mode'] else '✗'}
• Safe Retrieval Mode: {'✓' if settings['safe_retrieval_mode'] else '✗'}
• Embedding Device: {settings['embedding_device']}"""
        
        self.current_settings_text.setPlainText(display_text)
    
    def get_current_settings(self):
        """Get current settings from UI."""
        return {
            'n_results': self.n_results_spin.value(),
            'alpha': self.alpha_spin.value(),
            'importance_score': self.importance_spin.value(),
            'token_limit': self.token_limit_spin.value(),
            'reranking': self.reranking_checkbox.isChecked(),
            'cross_encoder_reranking': self.cross_encoder_checkbox.isChecked(),
            'query_expansion': self.query_expansion_checkbox.isChecked(),
            'ultra_safe_mode': self.ultra_safe_checkbox.isChecked(),
            'safe_retrieval_mode': self.safe_retrieval_checkbox.isChecked(),
            'embedding_device': self.device_combo.currentText()
        }
    
    def apply_quality_preset(self):
        """Apply high quality preset."""
        self.n_results_spin.setValue(30)
        self.alpha_spin.setValue(0.7)
        self.importance_spin.setValue(0.2)
        self.token_limit_spin.setValue(12288)
        self.reranking_checkbox.setChecked(True)
        self.cross_encoder_checkbox.setChecked(True)
        self.query_expansion_checkbox.setChecked(True)
        self.ultra_safe_checkbox.setChecked(False)
        self.safe_retrieval_checkbox.setChecked(False)
        self.device_combo.setCurrentText("auto")
    
    def apply_balanced_preset(self):
        """Apply balanced preset."""
        self.n_results_spin.setValue(25)
        self.alpha_spin.setValue(0.6)
        self.importance_spin.setValue(0.3)
        self.token_limit_spin.setValue(8192)
        self.reranking_checkbox.setChecked(True)
        self.cross_encoder_checkbox.setChecked(True)
        self.query_expansion_checkbox.setChecked(True)
        self.ultra_safe_checkbox.setChecked(False)
        self.safe_retrieval_checkbox.setChecked(False)
        self.device_combo.setCurrentText("auto")
    
    def apply_performance_preset(self):
        """Apply performance preset."""
        self.n_results_spin.setValue(15)
        self.alpha_spin.setValue(0.5)
        self.importance_spin.setValue(0.5)
        self.token_limit_spin.setValue(4096)
        self.reranking_checkbox.setChecked(False)
        self.cross_encoder_checkbox.setChecked(False)
        self.query_expansion_checkbox.setChecked(False)
        self.ultra_safe_checkbox.setChecked(True)
        self.safe_retrieval_checkbox.setChecked(True)
        self.device_combo.setCurrentText("cpu")
    
    def apply_amd_preset(self):
        """Apply AMD optimized preset."""
        self.n_results_spin.setValue(20)
        self.alpha_spin.setValue(0.6)
        self.importance_spin.setValue(0.3)
        self.token_limit_spin.setValue(8192)
        self.reranking_checkbox.setChecked(True)
        self.cross_encoder_checkbox.setChecked(False)  # Disable for better performance
        self.query_expansion_checkbox.setChecked(True)
        self.ultra_safe_checkbox.setChecked(True)  # Enable for stability
        self.safe_retrieval_checkbox.setChecked(True)  # Enable for stability
        self.device_combo.setCurrentText("cpu")  # Best for AMD integrated graphics
    
    def reset_to_defaults(self):
        """Reset to default settings."""
        self.apply_balanced_preset()
    
    def accept(self):
        """Save settings when OK is clicked."""
        try:
            settings = self.get_current_settings()
            # Save all settings to config.json
            config_path = Path("config.json")
            config = {}
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            # Save all RAG settings
            config['RAG_N_RESULTS'] = settings['n_results']
            config['RAG_ALPHA'] = settings['alpha']
            config['RAG_IMPORTANCE_SCORE'] = settings['importance_score']
            config['RAG_TOKEN_LIMIT'] = settings['token_limit']
            config['RAG_RERANKING'] = settings['reranking']
            config['RAG_CROSS_ENCODER_RERANKING'] = settings['cross_encoder_reranking']
            config['RAG_QUERY_EXPANSION'] = settings['query_expansion']
            config['RAG_ULTRA_SAFE_MODE'] = settings['ultra_safe_mode']
            config['RAG_SAFE_RETRIEVAL_MODE'] = settings['safe_retrieval_mode']
            config['EMBEDDING_DEVICE'] = settings['embedding_device']
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            # Emit signal with all settings
            self.settings_changed.emit(settings)
            super().accept()
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}") 