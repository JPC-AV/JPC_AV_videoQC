from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, 
    QComboBox, QTabWidget, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QSettings, QDir, QTimer
from PyQt6.QtGui import QPixmap, QPalette

import os
import sys
from dataclasses import asdict

from ..gui.gui_processing_gui import ProcessingWindow, DirectoryListWidget
from ..gui.gui_checks_window import ChecksWindow
from ..gui.gui_theme_manager import ThemeManager, ThemeableMixin

from ..utils.config_setup import SpexConfig, ChecksConfig
from ..utils.config_manager import ConfigManager
from ..utils.log_setup import logger
from ..utils import config_edit

from ..processing.worker_thread import ProcessingWorker
from ..processing.avspex_processor import AVSpexProcessor
from ..gui.gui_signals import ProcessingSignals

class MainWindow(QMainWindow, ThemeableMixin):
    """Main application window with tabs for configuration and settings."""
    
    def __init__(self):
        super().__init__()
        self.signals = ProcessingSignals()
        self.worker = None
        self.processing_window = None

        # Initialize collections for theme-aware components
        self.spex_tab_group_boxes = []
        self.checks_tab_group_boxes = []

        # Connect all signals
        self.setup_signal_connections()
        
        # Setup UI
        self.setup_ui()
        
        # Setup theme handling
        self.setup_theme_handling()
    
    def on_theme_changed(self, palette):
        """Handle theme changes across the application."""
        # Apply palette to main window
        self.setPalette(palette)
        
        # Get the theme manager
        theme_manager = ThemeManager.instance()
        
        # Update the tabs
        if hasattr(self, 'tabs'):
            self.tabs.setStyleSheet(theme_manager.get_tab_style())
        
        # Update all groupboxes in both tabs
        for group_box in self.checks_tab_group_boxes + self.spex_tab_group_boxes:
            theme_manager.style_groupbox(group_box)
            # Style buttons inside the group box
            theme_manager.style_buttons(group_box)
        
        # Special styling for green button
        if hasattr(self, 'check_spex_button'):
            self.check_spex_button.setStyleSheet("""
                QPushButton {
                    font-weight: bold;
                    padding: 8px 16px;
                    font-size: 14px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        
        # Update child windows
        for child_name in ['config_widget', 'processing_window']:
            child = getattr(self, child_name, None)
            if child and hasattr(child, 'on_theme_changed'):
                child.on_theme_changed(palette)
        
        # Force repaint
        self.update()

    def closeEvent(self, event):
        # Clean up theme connections
        self.cleanup_theme_handling()
        
        # Clean up child windows
        for child_name in ['config_widget', 'processing_window']:
            child = getattr(self, child_name, None)
            if child and hasattr(child, 'cleanup_theme_handling'):
                child.cleanup_theme_handling()
        
        # Stop worker if running
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        
        # Call quit handling method
        self.on_quit_clicked()
        super().closeEvent(event)

    def setup_tabs(self):
        """Set up tab styling"""
        theme_manager = ThemeManager.instance()
        
        # Create new tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(theme_manager.get_tab_style())

        self.main_layout.addWidget(self.tabs)

        self.setup_checks_tab()
        self.setup_spex_tab()

    def setup_signal_connections(self):
        """Setup all signal connections"""
        # Processing window signals
        self.signals.started.connect(self.on_processing_started)
        self.signals.completed.connect(self.on_processing_completed)
        self.signals.error.connect(self.on_error)
        self.signals.status_update.connect(self.on_status_update)
        self.signals.cancelled.connect(self.on_processing_cancelled)
        
        # Tool-specific signals
        self.signals.tool_started.connect(self.on_tool_started)
        self.signals.tool_completed.connect(self.on_tool_completed)
        self.signals.fixity_progress.connect(self.on_fixity_progress)
        self.signals.mediaconch_progress.connect(self.on_mediaconch_progress)
        self.signals.metadata_progress.connect(self.on_metadata_progress)
        self.signals.output_progress.connect(self.on_output_progress)

    def call_process_directories(self):
        """Initialize and start the worker thread"""
        try:
            # Create and configure the worker
            self.worker = ProcessingWorker(self.source_directories, self.signals)
            
            # Connect worker-specific signals
            self.worker.started_processing.connect(self.on_processing_started)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.error.connect(self.on_error)
            self.worker.processing_time.connect(self.on_processing_time)
            
            # Start the worker thread
            self.worker.start()
            
        except Exception as e:
            self.signals.error.emit(str(e))

    def on_worker_finished(self):
        """Handle worker thread completion"""
        if self.processing_window:
            self.processing_window.close()
            self.processing_window = None
        self.check_spex_button.setEnabled(True)
        
        # Clean up the worker
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def on_processing_started(self, message):
        """Handle processing start"""
        if self.processing_window is None:
            self.processing_window = ProcessingWindow(self)
            self.processing_window.cancel_button.clicked.connect(self.cancel_processing)
        self.processing_window.update_status(message)
        self.processing_window.show()
        self.processing_window.raise_()
        self.check_spex_button.setEnabled(False)
        QApplication.processEvents()
        
    def on_processing_completed(self, message):
        """Handle processing complete"""
        if self.processing_window:
            self.processing_window.close()
            self.processing_window = None
        # Re-enable the Check Spex button
        self.check_spex_button.setEnabled(True)
        QMessageBox.information(self, "Complete", message)
    
    def on_processing_time(self, formatted_time):
        """Handle processing time message from worker"""
        QMessageBox.information(self, "Complete", f"Processing completed in {formatted_time}!")

    def on_error(self, error_message):
        """Handle errors"""
        if self.processing_window:
            self.processing_window.close()
            self.processing_window = None
        self.check_spex_button.setEnabled(True)
        QMessageBox.critical(self, "Error", error_message)
        
        # Clean up worker if it exists
        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker.deleteLater()
            self.worker = None

    def on_status_update(self, message):
        """Handle status updates"""
        if self.processing_window:
            self.processing_window.update_status(message)

    def cancel_processing(self):
        """Cancel ongoing processing"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.processing_window.update_status("Cancelling processing...")
            self.processing_window.cancel_button.setEnabled(False)

    def on_processing_cancelled(self):
        """Handle processing cancellation"""
        if self.processing_window:
            self.processing_window.close()
            self.processing_window = None
        self.check_spex_button.setEnabled(True)
        QMessageBox.information(self, "Cancelled", "Processing was cancelled.")

    def on_tool_started(self, tool_name):
        """Handle tool processing start"""
        if self.processing_window:
            self.processing_window.update_status(f"Starting {tool_name}")
        
    def on_tool_completed(self, message):
        """Handle tool processing completion"""
        if self.processing_window:
            self.processing_window.update_status(message)
            # Let UI update
            QApplication.processEvents()

    def on_fixity_progress(self, message):
        """Handle fixity progress updates"""
        if self.processing_window:
            self.processing_window.update_detailed_status(message)

    def on_mediaconch_progress(self, message):
        """Handle mediaconch progress updates"""
        if self.processing_window:
            self.processing_window.update_detailed_status(message)

    def on_metadata_progress(self, message):
        """Handle metadata progress updates"""
        if self.processing_window:
            self.processing_window.update_detailed_status(message)

    def on_output_progress(self, message):
        """Handle output progress updates"""
        if self.processing_window:
            self.processing_window.update_detailed_status(message)
        
    def setup_ui(self):
        """Set up the main UI components"""
        self.config_mgr = ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
        self.spex_config = self.config_mgr.get_config('spex', SpexConfig)

        self.setMinimumSize(600, 800)

        ## self.windowFlags() retrieves the current window flags
        ## Qt.WindowType.WindowMaximizeButtonHint enables the maximize button in the window's title bar.
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        
        # Initialize settings
        self.settings = QSettings('NMAAHC', 'AVSpex')
        self.selected_directories = []
        
        self.check_spex_clicked = False
        self.setWindowTitle("AV Spex")
        
        # Set up menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu("File")
        self.import_action = self.file_menu.addAction("Import Directory")
        self.import_action.triggered.connect(self.import_directories)
        # Quit action
        self.quit_action = self.file_menu.addAction("Quit")
        self.quit_action.triggered.connect(self.on_quit_clicked)

        self.setup_main_layout()
        
        self.logo_setup()

        self.setup_tabs()

    def logo_setup(self):
        """Set up the logo display"""
        if getattr(sys, 'frozen', False):
            QTimer.singleShot(0, self._delayed_logo_setup)
        else:
            self._load_logo()

    def _delayed_logo_setup(self):
        """Delayed logo setup for frozen applications"""
        self._load_logo()

    def _load_logo(self):
        """Load and display the logo"""
        logo_path = self.config_mgr.get_logo_path('Branding_avspex_noJPC_030725.png')
        image_layout = self.add_image_to_top(logo_path)
        self.main_layout.insertLayout(0, image_layout)  # Insert at index 0 (top)

    def setup_checks_tab(self):
        """Set up or update the Checks tab with theme-aware styling"""
        # Get the theme manager instance
        theme_manager = ThemeManager.instance()
        
        # If we're here, we're creating the tab from scratch or recreating it
        # Initialize or reset the group boxes collection
        self.checks_tab_group_boxes = []
    
        # Create the tab
        checks_tab = QWidget()
        checks_layout = QVBoxLayout(checks_tab)
        self.tabs.addTab(checks_tab, "Checks")

        # Scroll Area for Vertical Scrolling in "Checks" Tab
        main_scroll_area = QScrollArea(self)
        main_scroll_area.setWidgetResizable(True)
        main_widget = QWidget(self)
        main_scroll_area.setWidget(main_widget)

        # Vertical layout for the main content in "Checks"
        vertical_layout = QVBoxLayout(main_widget)

        # 1. Import directory section
        self.import_group = QGroupBox("Import")
        theme_manager.style_groupbox(self.import_group, "top center")
        self.checks_tab_group_boxes.append(self.import_group)
        
        import_layout = QVBoxLayout()

        # Import directory button
        import_directories_button = QPushButton("Import Directory...")
        import_directories_button.clicked.connect(self.import_directories)
        
        # Directory section
        directory_label = QLabel("Selected Directories:")
        directory_label.setStyleSheet("font-weight: bold;")
        self.directory_list = DirectoryListWidget(self)
        self.directory_list.setStyleSheet("""
            QListWidget {
                border: 1px solid gray;
                border-radius: 3px;
            }
        """)
        
        # Delete button
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_selected_directory)
        
        # Add widgets to layout
        import_layout.addWidget(import_directories_button)
        import_layout.addWidget(directory_label)
        import_layout.addWidget(self.directory_list)
        import_layout.addWidget(delete_button)
        
        self.import_group.setLayout(import_layout)
        vertical_layout.addWidget(self.import_group)
        
        # Style all buttons in the section
        theme_manager.style_buttons(self.import_group)

        # 2. Command Profile section
        self.profile_group = QGroupBox("Checks Profiles")
        theme_manager.style_groupbox(self.profile_group, "top center")
        self.checks_tab_group_boxes.append(self.profile_group)
        
        profile_layout = QVBoxLayout()
        
        command_profile_label = QLabel("Select a Checks profile:")
        command_profile_label.setStyleSheet("font-weight: bold;")
        command_profile_desc = QLabel("Choose from a preset Checks profile to apply a set of Checks to run on your Spex")
        
        self.command_profile_dropdown = QComboBox()
        self.command_profile_dropdown.addItem("Step 1")
        self.command_profile_dropdown.addItem("Step 2")
        self.command_profile_dropdown.addItem("All Off")
        
        # Set initial dropdown state
        if self.checks_config.tools.exiftool.run_tool == "yes":
            self.command_profile_dropdown.setCurrentText("Step 1")
        elif self.checks_config.tools.exiftool.run_tool == "no":
            self.command_profile_dropdown.setCurrentText("Step 2")

        self.command_profile_dropdown.currentIndexChanged.connect(self.on_profile_selected)

        # Add widgets to layout
        profile_layout.addWidget(command_profile_label)
        profile_layout.addWidget(command_profile_desc)
        profile_layout.addWidget(self.command_profile_dropdown)
        
        self.profile_group.setLayout(profile_layout)
        vertical_layout.addWidget(self.profile_group)

        # 3. Config section
        self.config_group = QGroupBox("Checks Options")
        theme_manager.style_groupbox(self.config_group, "top center")
        self.checks_tab_group_boxes.append(self.config_group)
        
        config_layout = QVBoxLayout()
        
        config_scroll_area = QScrollArea()
        config_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        self.config_widget = ChecksWindow(config_mgr=self.config_mgr)
        config_scroll_area.setWidgetResizable(True)
        config_scroll_area.setWidget(self.config_widget)

        # Set a minimum width for the config widget to ensure legibility
        config_scroll_area.setMinimumWidth(400)

        config_layout.addWidget(config_scroll_area)
        self.config_group.setLayout(config_layout)
        vertical_layout.addWidget(self.config_group)

        # Add scroll area to main layout
        checks_layout.addWidget(main_scroll_area)

        # Bottom button section
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        self.check_spex_button = QPushButton("Check Spex!")
        self.check_spex_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 8px 16px;
                font-size: 14px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.check_spex_button.clicked.connect(self.on_check_spex_clicked)
        bottom_row.addWidget(self.check_spex_button)
        checks_layout.addLayout(bottom_row)

    def setup_main_layout(self):
        """Set up the main window layout structure"""
        # Create and set central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create main vertical layout
        self.main_layout = QVBoxLayout(self.central_widget)

        # Set layout margins and spacing
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

    def setup_spex_tab(self):
        """Set up or update the Spex tab with theme-aware styling"""
        # Get the theme manager instance
        theme_manager = ThemeManager.instance()
        
        # If we're here, we're creating the tab from scratch or recreating it
        # Initialize or reset the group boxes collection
        self.spex_tab_group_boxes = []
        
        # Create the tab if it doesn't exist
        if not hasattr(self, 'spex_tab') or not self.spex_tab:
            spex_tab = QWidget()
            spex_layout = QVBoxLayout(spex_tab)
            self.tabs.addTab(spex_tab, "Spex")
            self.spex_tab = spex_tab
        else:
            spex_tab = self.spex_tab
            spex_layout = spex_tab.layout()
            # Clear existing layout if needed
            while spex_layout.count():
                item = spex_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Create scroll area for vertical scrolling
        main_scroll_area = QScrollArea(self)
        main_scroll_area.setWidgetResizable(True)
        main_widget = QWidget(self)
        main_scroll_area.setWidget(main_widget)
        vertical_layout = QVBoxLayout(main_widget)
        
        # 1. Filename section
        self.filename_group = QGroupBox("Filename Values")
        theme_manager.style_groupbox(self.filename_group, "top center")
        self.spex_tab_group_boxes.append(self.filename_group)
        
        filename_layout = QVBoxLayout()
        
        # Profile dropdown
        profile_label = QLabel("Expected filename profiles:")
        profile_label.setStyleSheet("font-weight: bold;")
        self.filename_profile_dropdown = QComboBox()
        self.filename_profile_dropdown.addItem("Bowser file names")
        self.filename_profile_dropdown.addItem("JPC file names")
        
        # Set initial state based on config
        if self.spex_config.filename_values.Collection == "JPC":
            self.filename_profile_dropdown.setCurrentText("JPC file names")
        elif self.spex_config.filename_values.Collection == "2012_79":
            self.filename_profile_dropdown.setCurrentText("Bowser file names")
        
        self.filename_profile_dropdown.currentIndexChanged.connect(self.on_filename_profile_changed)
        
        # Open section button
        open_button = QPushButton("Open Section")
        open_button.clicked.connect(
            lambda: self.open_new_window('Filename Values', asdict(self.spex_config.filename_values))
        )
        
        # Add widgets to layout
        filename_layout.addWidget(profile_label)
        filename_layout.addWidget(self.filename_profile_dropdown)
        filename_layout.addWidget(open_button)
        self.filename_group.setLayout(filename_layout)
        vertical_layout.addWidget(self.filename_group)
        
        # Style the button using theme manager
        theme_manager.style_buttons(self.filename_group)
        
        # 2. MediaInfo section
        self.mediainfo_group = QGroupBox("MediaInfo Values")
        theme_manager.style_groupbox(self.mediainfo_group, "top center")
        self.spex_tab_group_boxes.append(self.mediainfo_group)
        
        mediainfo_layout = QVBoxLayout()
        
        mediainfo_button = QPushButton("Open Section")
        mediainfo_button.clicked.connect(
            lambda: self.open_new_window('MediaInfo Values', self.spex_config.mediainfo_values)
        )
        
        mediainfo_layout.addWidget(mediainfo_button)
        self.mediainfo_group.setLayout(mediainfo_layout)
        vertical_layout.addWidget(self.mediainfo_group)
        
        # Style the button
        theme_manager.style_buttons(self.mediainfo_group)
        
        # 3. Exiftool section
        self.exiftool_group = QGroupBox("Exiftool Values")
        theme_manager.style_groupbox(self.exiftool_group, "top center")
        self.spex_tab_group_boxes.append(self.exiftool_group)
        
        exiftool_layout = QVBoxLayout()
        
        exiftool_button = QPushButton("Open Section")
        exiftool_button.clicked.connect(
            lambda: self.open_new_window('Exiftool Values', asdict(self.spex_config.exiftool_values))
        )
        
        exiftool_layout.addWidget(exiftool_button)
        self.exiftool_group.setLayout(exiftool_layout)
        vertical_layout.addWidget(self.exiftool_group)
        
        # Style the button
        theme_manager.style_buttons(self.exiftool_group)
        
        # 4. FFprobe section
        self.ffprobe_group = QGroupBox("FFprobe Values")
        theme_manager.style_groupbox(self.ffprobe_group, "top center")
        self.spex_tab_group_boxes.append(self.ffprobe_group)
        
        ffprobe_layout = QVBoxLayout()
        
        ffprobe_button = QPushButton("Open Section")
        ffprobe_button.clicked.connect(
            lambda: self.open_new_window('FFprobe Values', self.spex_config.ffmpeg_values)
        )
        
        ffprobe_layout.addWidget(ffprobe_button)
        self.ffprobe_group.setLayout(ffprobe_layout)
        vertical_layout.addWidget(self.ffprobe_group)
        
        # Style the button
        theme_manager.style_buttons(self.ffprobe_group)
        
        # 5. Mediatrace section
        self.mediatrace_group = QGroupBox("Mediatrace Values")
        theme_manager.style_groupbox(self.mediatrace_group, "top center")
        self.spex_tab_group_boxes.append(self.mediatrace_group)
        
        mediatrace_layout = QVBoxLayout()
        
        # Signalflow profile dropdown
        signalflow_label = QLabel("Expected Signalflow profiles:")
        signalflow_label.setStyleSheet("font-weight: bold;")
        self.signalflow_profile_dropdown = QComboBox()
        self.signalflow_profile_dropdown.addItem("JPC_AV_SVHS Signal Flow")
        self.signalflow_profile_dropdown.addItem("BVH3100 Signal Flow")
        
        # Set initial state based on config
        encoder_settings = self.spex_config.mediatrace_values.ENCODER_SETTINGS
        if isinstance(encoder_settings, dict):
            source_vtr = encoder_settings.get('Source_VTR', [])
        else:
            source_vtr = encoder_settings.Source_VTR
            
        if any("SVO5800" in vtr for vtr in source_vtr):
            self.signalflow_profile_dropdown.setCurrentText("JPC_AV_SVHS Signal Flow")
        elif any("Sony BVH3100" in vtr for vtr in source_vtr):
            self.signalflow_profile_dropdown.setCurrentText("BVH3100 Signal Flow")
            
        self.signalflow_profile_dropdown.currentIndexChanged.connect(self.on_signalflow_profile_changed)
        
        mediatrace_button = QPushButton("Open Section")
        mediatrace_button.clicked.connect(
            lambda: self.open_new_window('Mediatrace Values', asdict(self.spex_config.mediatrace_values))
        )
        
        mediatrace_layout.addWidget(signalflow_label)
        mediatrace_layout.addWidget(self.signalflow_profile_dropdown)
        mediatrace_layout.addWidget(mediatrace_button)
        self.mediatrace_group.setLayout(mediatrace_layout)
        vertical_layout.addWidget(self.mediatrace_group)
        
        # Style the button
        theme_manager.style_buttons(self.mediatrace_group)
        
        # 6. QCT section
        self.qct_group = QGroupBox("qct-parse Values")
        theme_manager.style_groupbox(self.qct_group, "top center")
        self.spex_tab_group_boxes.append(self.qct_group)
        
        qct_layout = QVBoxLayout()
        
        qct_button = QPushButton("Open Section")
        qct_button.clicked.connect(
            lambda: self.open_new_window('Expected qct-parse options', asdict(self.spex_config.qct_parse_values))
        )
        
        qct_layout.addWidget(qct_button)
        self.qct_group.setLayout(qct_layout)
        vertical_layout.addWidget(self.qct_group)
        
        # Style the button
        theme_manager.style_buttons(self.qct_group)
        
        # Add scroll area to main layout
        spex_layout.addWidget(main_scroll_area)
    
    def add_image_to_top(self, logo_path):
        """Add image to the top of the main layout."""
        image_layout = QHBoxLayout()
        
        label = QLabel()
        label.setMinimumHeight(100)
        
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                # Scale pixmap to window width while keeping aspect ratio
                scaled_pixmap = pixmap.scaledToWidth(self.width(), Qt.TransformationMode.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
            else:
                print(f"Failed to load image at path: {logo_path}")
        else:
            print(f"Invalid logo path: {logo_path}")
        
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(label)
        return image_layout

    def import_directories(self):
        """Import directories for processing."""
        # Get the last directory from settings
        last_directory = self.settings.value('last_directory', '')
        
        # Use native file dialog
        file_dialog = QFileDialog(self, "Select Directories")
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        # Set the starting directory to the parent of the last used directory
        if last_directory:
            dir_info = QDir(last_directory)
            if dir_info.cdUp():  # Move up to parent directory
                parent_dir = dir_info.absolutePath()
                file_dialog.setDirectory(parent_dir)
        
        # Try to enable multiple directory selection with the native dialog
        file_dialog.setOption(QFileDialog.Option.ReadOnly, False)

        if file_dialog.exec():
            directories = file_dialog.selectedFiles()  # Get selected directories
            
            # Save the last used directory
            if directories:
                self.settings.setValue('last_directory', directories[0])
                self.settings.sync()  # Ensure settings are saved
            
            for directory in directories:
                if directory not in self.selected_directories:
                    self.selected_directories.append(directory)
                    self.directory_list.addItem(directory)

    def update_selected_directories(self):
        """Update source_directories from the QListWidget."""
        self.source_directories = [self.directory_list.item(i).text() for i in range(self.directory_list.count())]

    def get_source_directories(self):
        """Return the selected directories if Check Spex was clicked."""
        return self.selected_directories if self.check_spex_clicked else None
    
    def delete_selected_directory(self):
        """Delete the selected directory from the list widget and the selected_directories list."""
        # Get the selected items
        selected_items = self.directory_list.selectedItems()
        
        if not selected_items:
            return  # No item selected, do nothing
        
        # Remove each selected item from both the QListWidget and selected_directories list
        for item in selected_items:
            # Remove from the selected_directories list
            directory = item.text()
            if directory in self.selected_directories:
                self.selected_directories.remove(directory)
            
            # Remove from the QListWidget
            self.directory_list.takeItem(self.directory_list.row(item))

    def on_check_spex_clicked(self):
        """Handle the Check Spex button click."""
        self.update_selected_directories()
        self.check_spex_clicked = True  # Mark that the button was clicked
        self.config_mgr.save_last_used_config('checks')
        self.config_mgr.save_last_used_config('spex')
        self.call_process_directories()

    def on_profile_selected(self, index):
        """Handle profile selection from dropdown."""
        selected_profile = self.command_profile_dropdown.currentText()
        if selected_profile == "Step 1":
            profile = config_edit.profile_step1
        elif selected_profile == "Step 2":
            profile = config_edit.profile_step2
        elif selected_profile == "All Off":
            profile = config_edit.profile_allOff
        try:
            # Call the backend function to apply the selected profile
            config_edit.apply_profile(profile)
            logger.debug(f"Profile '{selected_profile}' applied successfully.")
            self.config_mgr.save_last_used_config('checks')
        except ValueError as e:
            logger.critical(f"Error: {e}")

        self.config_widget.load_config_values()

    def on_filename_profile_changed(self, index):
        """Handle filename profile selection change."""
        selected_option = self.filename_profile_dropdown.itemText(index)
        updates = {}
        
        if selected_option == "JPC file names":
            updates = {
                "filename_values": {
                    "Collection": "JPC",
                    "MediaType": "AV",
                    "ObjectID": r"\d{5}",
                    "DigitalGeneration": None,
                    "FileExtension": "mkv"
                }
            }
        elif selected_option == "Bowser file names":
            updates = {
                "filename_values": {
                    "Collection": "2012_79",
                    "MediaType": "2",
                    "ObjectID": r"\d{3}_\d{1}[a-zA-Z]",
                    "DigitalGeneration": "PM",
                    "FileExtension": "mkv"
                }
            }
        
        self.config_mgr.update_config('spex', updates)
        self.config_mgr.save_last_used_config('spex')

    def on_signalflow_profile_changed(self, index):
        """Handle signal flow profile selection change."""
        selected_option = self.signalflow_profile_dropdown.itemText(index)
        logger.debug(f"Selected signal flow profile: {selected_option}")

        if selected_option == "JPC_AV_SVHS Signal Flow":
            sn_config_changes = config_edit.JPC_AV_SVHS
        elif selected_option == "BVH3100 Signal Flow":
            sn_config_changes = config_edit.BVH3100
        else:
            logger.error("Signal flow identifier not recognized, config not updated")
            return

        # Update FFmpeg settings
        self.config_mgr.update_config('spex', {
            'ffmpeg_values': {
                'format': {
                    'tags': {
                        'ENCODER_SETTINGS': sn_config_changes
                    }
                }
            }
        })

        # Update MediaTrace settings 
        self.config_mgr.update_config('spex', {
            'mediatrace_values': {
                'ENCODER_SETTINGS': sn_config_changes
            }
        })

    def open_new_window(self, title, nested_dict):
        """Open a new window to display configuration details."""
        # Convert any dataclass instances in mediainfo_values to dictionaries
        if title == 'MediaInfo Values':
            nested_dict = {
                'expected_general': nested_dict['expected_general'],
                'expected_video': nested_dict['expected_video'], 
                'expected_audio': nested_dict['expected_audio']
            }
        # Convert ffmpeg_values dataclass instances
        elif title == 'FFprobe Values':
            nested_dict = {
                'video_stream': nested_dict['video_stream'],
                'audio_stream': nested_dict['audio_stream'],
                'format': nested_dict['format']
            }

        content_text = self.dict_to_string(nested_dict)
    
        self.new_window = QWidget()
        self.new_window.setWindowTitle(title)
        self.new_window.setLayout(QVBoxLayout())
        
        scroll_area = QScrollArea(self.new_window)
        scroll_area.setWidgetResizable(True)
        
        content_widget = QTextEdit()
        content_widget.setPlainText(content_text)
        content_widget.setReadOnly(True)
        content_widget.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        
        # Remove the hardcoded background color and use system palette instead
        content_widget.setStyleSheet("padding: 5px;")
        
        # Explicitly set the text color to follow system palette
        palette = content_widget.palette()
        palette.setColor(QPalette.ColorRole.Base, palette.color(QPalette.ColorRole.Window))
        palette.setColor(QPalette.ColorRole.Text, palette.color(QPalette.ColorRole.WindowText))
        content_widget.setPalette(palette)
        
        scroll_area.setWidget(content_widget)
        
        self.new_window.layout().addWidget(scroll_area)
        self.new_window.resize(600, 400)
        self.new_window.show()

    def dict_to_string(self, content_dict, indent_level=0):
        """Convert a dictionary to a string representation for display.
        
        Handles nested dictionaries and lists with proper formatting and indentation.
        """
        content_lines = []
        indent = "  " * indent_level  # Two spaces per indent level

        for key, value in content_dict.items():
            if isinstance(value, dict):  # If the value is a nested dictionary
                content_lines.append(f"{indent}{key}:")
                # Recursively process the nested dictionary
                content_lines.append(self.dict_to_string(value, indent_level + 1))
            elif isinstance(value, list):  # If the value is a list
                content_lines.append(f"{indent}{key}:")
                # Add each list item on a new line with additional indentation
                for item in value:
                    content_lines.append(f"{indent}  - {item}")
            else:  # For all other types (e.g., strings, numbers)
                content_lines.append(f"{indent}{key}: {value}")

        return "\n".join(content_lines)
    
    def on_quit_clicked(self):
        """Handle the 'Quit' button click."""
        self.selected_directories = None  # Clear any selections
        self.check_spex_clicked = False  # Ensure the flag is reset
        self.config_mgr.save_last_used_config('checks')
        self.config_mgr.save_last_used_config('spex')
        self.close()  # Close the GUI