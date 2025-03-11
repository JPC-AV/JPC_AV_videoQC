from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QAbstractItemView, QTextEdit, 
    QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QFont

import os
from ..gui.gui_theme_manager import ThemeManager, ThemeableMixin

from ..utils.config_manager import ConfigManager
from ..utils.config_setup import ChecksConfig

class ProcessingWindow(QMainWindow, ThemeableMixin):
    """Window to display processing status and progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Status")
        self.resize(600, 400)
        self.setWindowFlags(Qt.WindowType.Window)
        
        # Central widget and main_layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Status label with larger font
        self.file_status_label = QLabel("No file processing yet...")
        file_font = self.file_status_label.font()
        file_font.setPointSize(10)
        self.file_status_label.setFont(file_font)
        self.file_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.file_status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # This makes it into a "bouncing ball" progress bar
        main_layout.addWidget(self.progress_bar)

        # Create a horizontal layout for steps list and details text
        v_layout = QVBoxLayout()
        main_layout.addLayout(v_layout, 1)  # stretch factor of 1 allows for window to stretch
        
        # Steps list widget - shows steps that will be executed
        self.steps_list = QListWidget()
        self.steps_list.setMinimumHeight(150)
        self.steps_list.setAlternatingRowColors(True)
        v_layout.addWidget(self.steps_list)

        # Detailed status
        self.detailed_status = QLabel("")
        self.detailed_status.setWordWrap(True)
        v_layout.addWidget(self.detailed_status)

        # Detail progress bar
        self.detail_progress_bar = QProgressBar()
        self.detail_progress_bar.setTextVisible(True)
        self.detail_progress_bar.setMinimum(0)
        # self.detail_progress_bar.setMaximum(0)  
        self.percent_label = QLabel("0%")  # Corrected variable name from "perecent_label"
        self.percent_label.setAlignment(Qt.AlignmentFlag.AlignLeft) 
        v_layout.addWidget(self.percent_label)
        v_layout.addWidget(self.detail_progress_bar)

        # Details text
        self.details_text = QTextEdit()
        self.details_text.setMinimumHeight(300)
        self.details_text.setReadOnly(True)
        v_layout.addWidget(self.details_text, 1)  # stretch factor of 1

        # Add cancel button
        self.cancel_button = QPushButton("Cancel")
        main_layout.addWidget(self.cancel_button)

        # Load the configuration and populate steps
        self.config_mgr = ConfigManager()
        self.populate_steps_list()
        
        # Setup theme handling (only once)
        self.setup_theme_handling()

    def populate_steps_list(self):
        """Populate the steps list with enabled checks from config."""
        try:
            # Get checks config
            checks_config = self.config_mgr.get_config('checks', ChecksConfig)
            if not checks_config:
                self.update_status("Warning: Could not load checks configuration")
                return

            # Add steps based on configuration
            # First add outputs
            if checks_config.outputs.access_file == "yes":
                self._add_step_item("Generate Access File")
            if checks_config.outputs.report == "yes":
                self._add_step_item("Generate Report")
            
            # Add fixity
            if checks_config.fixity.check_fixity == "yes":
                self._add_step_item("Check Fixity")
            if checks_config.fixity.validate_stream_fixity == "yes":
                self._add_step_item("Validate Stream Fixity")
            if checks_config.fixity.embed_stream_fixity == "yes":
                self._add_step_item("Embed Stream Fixity")
            if checks_config.fixity.output_fixity == "yes":
                self._add_step_item("Output Fixity")
            
            # Add tools
            tools_config = checks_config.tools
            
            # Handle mediaconch specifically
            if tools_config.mediaconch.run_mediaconch == "yes":
                self._add_step_item("MediaConch Validation")
            
            # Handle other tools
            if tools_config.exiftool.run_tool == "yes":
                self._add_step_item("Exiftool")
            if tools_config.ffprobe.run_tool == "yes":
                self._add_step_item("Ffprobe")
            if tools_config.mediainfo.run_tool == "yes":
                self._add_step_item("Mediainfo")
            if tools_config.mediatrace.run_tool == "yes":
                self._add_step_item("Mediatrace")
            if tools_config.qctools.run_tool == "yes":
                self._add_step_item("Qctools")
            if tools_config.qct_parse.run_tool == "yes":
                self._add_step_item("Qct_parse")
            
        except Exception as e:
            self.update_status(f"Error loading steps: {str(e)}")
    
    def _add_step_item(self, step_name):
        """Add a step item to the list."""
        item = QListWidgetItem(f"⬜ {step_name}")
        self.steps_list.addItem(item)
    
    def mark_step_complete(self, step_name):
        """Mark a step as complete in the list."""
        # Find and update the item
        for i in range(self.steps_list.count()):
            item = self.steps_list.item(i)
            # Check if this item contains our step name
            if step_name.lower() in item.text().lower():
                item.setText(f"✅ {step_name}")
                item.setFont(QFont("Arial", weight=QFont.Weight.Bold))
                break

    def update_detailed_status(self, message):
        """Update the detailed status message."""
        self.detailed_status.setText(message)
        QApplication.processEvents()

    def update_status(self, message):
        """Update the main status message and append to details text."""
        self.details_text.append(message)
        # Scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # Check if this message indicates a step completion
        self._check_step_completion(message)

    def update_file_status(self, filename):
        """Update the file status label when processing a new file."""
        self.file_status_label.setText(f"Processing: {filename}")
        self.details_text.append(f"Started processing file: {filename}")
        # Scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _check_step_completion(self, message):
        """Check if the message indicates a step has been completed."""
        # Define message patterns that indicate step completion
        completion_indicators = {
            "fixity processing complete": "Check Fixity",
            "mediaconch validation complete": "MediaConch Validation",
            "metadata tools complete": "Metadata Tools",
            "outputs complete": "Generate Access File"
        }
        
        # Look for completion indicators in the message
        message_lower = message.lower()
        for indicator, step_name in completion_indicators.items():
            if indicator in message_lower:
                self.mark_step_complete(step_name)
                break

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()  # Bring window to front
        self.activateWindow()  # Activate the window

    def closeEvent(self, event):
        # Get a reference to the parent (MainWindow)
        parent = self.parent()
        
        # If parent exists and has a cancel_processing method AND processing is still active, call it
        if parent and hasattr(parent, 'cancel_processing') and parent.worker is not None:
            parent.cancel_processing()
        
        # Call the parent class's closeEvent to properly handle window closure
        super().closeEvent(event)

    def on_theme_changed(self, palette):
        """Handle theme changes"""
        # Apply palette to all components
        self.setPalette(palette)
        self.details_text.setPalette(palette)
        self.status_label.setPalette(palette)
        
        # Style the cancel button
        theme_manager = ThemeManager.instance()
        theme_manager.style_buttons(self)
        
        # Force repaint
        self.update()

    def update_detail_progress(self, percentage):
        """Update the detail progress bar and percentage label with the current percentage."""
        self.detail_progress_bar.setMaximum(100)
        self.detail_progress_bar.setValue(percentage)
        
        # Update the percentage label
        self.percent_label.setText(f"{percentage}%")
        
        # Force UI update
        QApplication.processEvents()


class DirectoryListWidget(QListWidget):
    """Custom list widget with drag and drop support for directories."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Critical settings for drag and drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.main_window = parent

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            
            for url in urls:
                path = url.toLocalFile()
                
                if os.path.isdir(path):
                    # Check for duplicates before adding
                    if path not in [self.item(i).text() for i in range(self.count())]:
                        self.addItem(path)
                        
                        # Update selected_directories if main_window is available
                        if hasattr(self.main_window, 'selected_directories'):
                            if path not in self.main_window.selected_directories:
                                self.main_window.selected_directories.append(path)
            
            event.acceptProposedAction()
