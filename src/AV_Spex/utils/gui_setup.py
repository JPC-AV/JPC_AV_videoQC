from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QLabel, 
    QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, QToolButton, QComboBox, QTabWidget,
    QTextEdit, QListView, QTreeView, QAbstractItemView, QInputDialog, QMessageBox, QToolBar, QStatusBar, 
    QProgressBar
)
from PyQt6.QtCore import Qt, QUrl, QMimeData, QSettings, QDir, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QAction

import os
import sys
from dataclasses import dataclass, asdict, field

from ..utils.setup_config import SpexConfig, ChecksConfig
from ..utils.config_manager import ConfigManager
from ..utils.log_setup import logger
from ..utils import edit_config

from ..processing.processing_mgmt import setup_mediaconch_policy
from ..processing.worker_thread import ProcessingWorker

from ..processing.avspex_processor import AVSpexProcessor
from ..utils.signals import ProcessingSignals

class ProcessingWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Status")
        self.resize(500, 200)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label with larger font
        self.status_label = QLabel("Initializing...")
        font = self.status_label.font()
        font.setPointSize(12)
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # This makes it into a "bouncing ball" progress bar
        layout.addWidget(self.progress_bar)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(100)
        layout.addWidget(self.details_text)

        # Add cancel button
        self.cancel_button = QPushButton("Cancel")
        layout.addWidget(self.cancel_button)

        # Center the window on screen
        self._center_on_screen()  # Changed to use the defined method
        
        # Force window to update
        self.update()
        self.repaint()

        self.detailed_status = QLabel("")
        self.detailed_status.setWordWrap(True)
        layout.addWidget(self.detailed_status)

    def update_detailed_status(self, message):
        self.detailed_status.setText(message)
        QApplication.processEvents()

    def update_status(self, message):
        self.status_label.setText(message)
        self.details_text.append(message)
        # Scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _center_on_screen(self):
        """Centers the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()  # Bring window to front
        self.activateWindow()  # Activate the window

    def closeEvent(self, event):
        # logger.debug("ProcessingWindow close event triggered")  # Debug
        super().closeEvent(event)


class DirectoryListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Critical settings for drag and drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.main_window = parent

    def dragEnterEvent(self, event):
        #print("Drag Enter Event Triggered")
        if event.mimeData().hasUrls():
         #   print("URLs Detected in Drag Event")
            event.acceptProposedAction()
        else:
          #  print("No URLs in Drag Event")
            event.ignore()

    def dragMoveEvent(self, event):
        #print("Drag Move Event Triggered")
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


class ConfigWindow(QWidget):
    def __init__(self, config_mgr=None):
        super().__init__()
        self.config_mgr = config_mgr or ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        """Create fixed layout structure"""
        main_layout = QVBoxLayout(self)
        
        # Outputs Section
        outputs_group = QGroupBox("Outputs")
        outputs_layout = QVBoxLayout()
        self.access_file_cb = QCheckBox("access_file")
        self.report_cb = QCheckBox("report")
        self.qctools_ext_label = QLabel("qctools_ext")
        self.qctools_ext_input = QLineEdit()
        
        outputs_layout.addWidget(self.access_file_cb)
        outputs_layout.addWidget(self.report_cb)
        outputs_layout.addWidget(self.qctools_ext_label)
        outputs_layout.addWidget(self.qctools_ext_input)
        outputs_group.setLayout(outputs_layout)
        
        # Fixity Section
        fixity_group = QGroupBox("Fixity")
        fixity_layout = QVBoxLayout()
        self.output_fixity_cb = QCheckBox("Output fixity (to .txt and .md5 files)")
        self.check_fixity_cb = QCheckBox("Validate fixity")
        self.embed_stream_cb = QCheckBox("Embed Stream fixity")
        self.validate_stream_cb = QCheckBox("Validate Stream fixity")
        self.overwrite_stream_cb = QCheckBox("Overwrite Stream fixity")
        
        fixity_layout.addWidget(self.output_fixity_cb)
        fixity_layout.addWidget(self.check_fixity_cb)
        fixity_layout.addWidget(self.embed_stream_cb)
        fixity_layout.addWidget(self.validate_stream_cb)
        fixity_layout.addWidget(self.overwrite_stream_cb)
        fixity_group.setLayout(fixity_layout)
        
        # Tools Section
        tools_group = QGroupBox("Tools")
        tools_layout = QVBoxLayout()
        
        # Basic tools (exiftool, ffprobe, mediainfo, mediatrace, qctools)
        basic_tools = ['exiftool', 'ffprobe', 'mediainfo', 'mediatrace', 'qctools']
        self.tool_widgets = {}
        
        for tool in basic_tools:
            tool_group = QGroupBox(tool)
            tool_layout = QVBoxLayout()
            check_cb = QCheckBox("Check Tool")
            run_cb = QCheckBox("Run Tool")
            if tool == 'qctools':
                self.tool_widgets[tool] = {'run': run_cb}
                tool_layout.addWidget(run_cb)
            else:
                self.tool_widgets[tool] = {'check': check_cb, 'run': run_cb}
                tool_layout.addWidget(check_cb)
                tool_layout.addWidget(run_cb)
            tool_group.setLayout(tool_layout)
            tools_layout.addWidget(tool_group)
        
        # MediaConch
        mediaconch_group = QGroupBox("Mediaconch")
        mediaconch_layout = QVBoxLayout()
        self.run_mediaconch_cb = QCheckBox("Run Mediaconch")
        
        # Policy selection
        policy_container = QWidget()
        policy_layout = QVBoxLayout(policy_container)
        
        # Add current policy display
        current_policy_widget = QWidget()
        current_policy_layout = QHBoxLayout(current_policy_widget)
        current_policy_layout.setContentsMargins(0, 0, 0, 0)
        
        self.policy_label = QLabel("Current policy: ")
        self.current_policy_display = QLabel()
        self.current_policy_display.setStyleSheet("font-weight: bold;")
        
        current_policy_layout.addWidget(self.policy_label)
        current_policy_layout.addWidget(self.current_policy_display)
        current_policy_layout.addStretch()

        self.policy_combo = QComboBox()
        self.import_policy_btn = QPushButton("Import New MediaConch Policy")
        
        policy_layout.addWidget(current_policy_widget)
        policy_layout.addWidget(QLabel("Available policies:"))
        policy_layout.addWidget(self.policy_combo)
        policy_layout.addWidget(self.import_policy_btn)
        
        mediaconch_layout.addWidget(self.run_mediaconch_cb)
        mediaconch_layout.addWidget(policy_container)
        mediaconch_group.setLayout(mediaconch_layout)
        tools_layout.addWidget(mediaconch_group)
        
        # QCT Parse
        qct_group = QGroupBox("qct-parse")
        qct_layout = QVBoxLayout()

        self.run_qctparse_cb = QCheckBox("Run Tool")
        self.bars_detection_cb = QCheckBox("barsDetection")
        self.evaluate_bars_cb = QCheckBox("evaluateBars")
        self.thumb_export_cb = QCheckBox("thumbExport")
        
        # Content Filter combo
        content_filter_label = QLabel("contentFilter")
        self.content_filter_combo = QComboBox()
        self.content_filter_combo.addItem("Select options...")
        self.content_filter_combo.addItems(["allBlack", "static"])
        
        # Profile combo
        profile_label = QLabel("profile")
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Select options...")
        self.profile_combo.addItems(["default", "highTolerance", "midTolerance", "lowTolerance"])
        
        # Tagname
        tagname_label = QLabel("tagname")
        self.tagname_input = QLineEdit()
        self.tagname_input.setPlaceholderText("None")
        
        qct_layout.addWidget(self.run_qctparse_cb)
        qct_layout.addWidget(self.bars_detection_cb)
        qct_layout.addWidget(self.evaluate_bars_cb)
        qct_layout.addWidget(self.thumb_export_cb)
        qct_layout.addWidget(content_filter_label)
        qct_layout.addWidget(self.content_filter_combo)
        qct_layout.addWidget(profile_label)
        qct_layout.addWidget(self.profile_combo)
        qct_layout.addWidget(tagname_label)
        qct_layout.addWidget(self.tagname_input)
        
        qct_group.setLayout(qct_layout)
        tools_layout.addWidget(qct_group)
        
        tools_group.setLayout(tools_layout)
        
        # Add all sections to main layout
        main_layout.addWidget(outputs_group)
        main_layout.addWidget(fixity_group)
        main_layout.addWidget(tools_group)
        main_layout.addStretch()
        
        # Connect signals
        self.connect_signals()

    def connect_signals(self):
        """Connect all widget signals to their handlers"""
        # Outputs section
        self.access_file_cb.stateChanged.connect(
            lambda state: self.on_checkbox_changed(state, ['outputs', 'access_file'])
        )
        self.report_cb.stateChanged.connect(
            lambda state: self.on_checkbox_changed(state, ['outputs', 'report'])
        )
        self.qctools_ext_input.textChanged.connect(
            lambda text: self.on_text_changed(['outputs', 'qctools_ext'], text)
        )
        
        # Fixity section
        fixity_checkboxes = {
            self.check_fixity_cb: 'check_fixity',
            self.validate_stream_cb: 'validate_stream_fixity',
            self.embed_stream_cb: 'embed_stream_fixity',
            self.output_fixity_cb: 'output_fixity',
            self.overwrite_stream_cb: 'overwrite_stream_fixity'
        }
        
        for checkbox, field in fixity_checkboxes.items():
            checkbox.stateChanged.connect(
                lambda state, f=field: self.on_checkbox_changed(state, ['fixity', f])
            )
        
        # Tools section
        for tool, widgets in self.tool_widgets.items():
            if tool == 'qctools':
                widgets['run'].stateChanged.connect(
                lambda state, t=tool: self.on_checkbox_changed(state, ['tools', t, 'run_tool'])
            )
            else:
                widgets['check'].stateChanged.connect(
                    lambda state, t=tool: self.on_checkbox_changed(state, ['tools', t, 'check_tool'])
                )
                widgets['run'].stateChanged.connect(
                    lambda state, t=tool: self.on_checkbox_changed(state, ['tools', t, 'run_tool'])
                )
        
        # MediaConch
        mediaconch = self.checks_config.tools.mediaconch
        self.run_mediaconch_cb.setChecked(mediaconch.run_mediaconch.lower() == 'yes')
        
        self.run_mediaconch_cb.stateChanged.connect(
            lambda state: self.on_checkbox_changed(state, ['tools', 'mediaconch', 'run_mediaconch'])
        )
        self.policy_combo.currentTextChanged.connect(self.on_mediaconch_policy_changed)
        self.import_policy_btn.clicked.connect(self.open_policy_file_dialog)
                    
        # QCT Parse
        self.run_qctparse_cb.stateChanged.connect(
            lambda state: self.on_boolean_changed(state, ['tools', 'qct_parse', 'run_tool'])
        )
        self.bars_detection_cb.stateChanged.connect(
            lambda state: self.on_boolean_changed(state, ['tools', 'qct_parse', 'barsDetection'])
        )
        self.evaluate_bars_cb.stateChanged.connect(
            lambda state: self.on_boolean_changed(state, ['tools', 'qct_parse', 'evaluateBars'])
        )
        self.thumb_export_cb.stateChanged.connect(
            lambda state: self.on_boolean_changed(state, ['tools', 'qct_parse', 'thumbExport'])
        )
        self.content_filter_combo.currentTextChanged.connect(
            lambda text: self.on_qct_combo_changed(text, 'contentFilter')
        )
        self.profile_combo.currentTextChanged.connect(
            lambda text: self.on_qct_combo_changed(text, 'profile')
        )
        self.tagname_input.textChanged.connect(
            lambda text: self.on_tagname_changed(text)
        )

    def load_config_values(self):
        """Load current config values into UI elements"""
        # Set loading flag to True
        self.is_loading = True

        # Outputs
        self.access_file_cb.setChecked(self.checks_config.outputs.access_file.lower() == 'yes')
        self.report_cb.setChecked(self.checks_config.outputs.report.lower() == 'yes')
        self.qctools_ext_input.setText(self.checks_config.outputs.qctools_ext)
        
        # Fixity
        self.check_fixity_cb.setChecked(self.checks_config.fixity.check_fixity.lower() == 'yes')
        self.validate_stream_cb.setChecked(self.checks_config.fixity.validate_stream_fixity.lower() == 'yes')
        self.embed_stream_cb.setChecked(self.checks_config.fixity.embed_stream_fixity.lower() == 'yes')
        self.output_fixity_cb.setChecked(self.checks_config.fixity.output_fixity.lower() == 'yes')
        self.overwrite_stream_cb.setChecked(self.checks_config.fixity.overwrite_stream_fixity.lower() == 'yes')
        
        # Tools
        for tool, widgets in self.tool_widgets.items():
            tool_config = getattr(self.checks_config.tools, tool)
            if tool == 'qctools':
                widgets['run'].setChecked(tool_config.run_tool.lower() == 'yes')
            else:
                widgets['check'].setChecked(tool_config.check_tool.lower() == 'yes')
                widgets['run'].setChecked(tool_config.run_tool.lower() == 'yes')
        
        # MediaConch
        mediaconch = self.checks_config.tools.mediaconch
        self.run_mediaconch_cb.setChecked(mediaconch.run_mediaconch.lower() == 'yes')
        
        # Update current policy display
        self.update_current_policy_display(mediaconch.mediaconch_policy)
        
        # Load available policies
        policies_dir = os.path.join(self.config_mgr.project_root, 'config', 'mediaconch_policies')
        if os.path.exists(policies_dir):
            available_policies = [f for f in os.listdir(policies_dir) if f.endswith('.xml')]
            self.policy_combo.clear()
            self.policy_combo.addItems(available_policies)
            
            # Temporarily block signals while setting the current text
            self.policy_combo.blockSignals(True)
            if mediaconch.mediaconch_policy in available_policies:
                self.policy_combo.setCurrentText(mediaconch.mediaconch_policy)
            self.policy_combo.blockSignals(False)
        
        # QCT Parse
        qct = self.checks_config.tools.qct_parse
        self.bars_detection_cb.setChecked(qct.barsDetection)
        self.evaluate_bars_cb.setChecked(qct.evaluateBars)
        self.thumb_export_cb.setChecked(qct.thumbExport)
        
        if qct.contentFilter:
            self.content_filter_combo.setCurrentText(qct.contentFilter[0])
        if qct.profile:
            self.profile_combo.setCurrentText(qct.profile[0])
        if qct.tagname is not None:
            self.tagname_input.setText(qct.tagname)

        # Set loading flag back to False after everything is loaded
        self.is_loading = False

    def on_checkbox_changed(self, state, path):
        """Handle changes in yes/no checkboxes"""
        new_value = 'yes' if Qt.CheckState(state) == Qt.CheckState.Checked else 'no'
        
        if path[0] == "tools" and len(path) > 2:
            tool_name = path[1]
            field = path[2]
            updates = {'tools': {tool_name: {field: new_value}}}
        else:
            section = path[0]
            field = path[1]
            updates = {section: {field: new_value}}
            
        self.config_mgr.update_config('checks', updates)

    def on_boolean_changed(self, state, path):
        """Handle changes in boolean checkboxes"""
        new_value = Qt.CheckState(state) == Qt.CheckState.Checked
        
        if path[0] == "tools" and path[1] == "qct_parse":
            updates = {'tools': {'qct_parse': {path[2]: new_value}}}
            self.config_mgr.update_config('checks', updates)

    def on_text_changed(self, path, text):
        """Handle changes in text inputs"""
        updates = {path[0]: {path[1]: text}}
        self.config_mgr.update_config('checks', updates)

    def on_qct_combo_changed(self, text, field):
        """Handle changes in QCT Parse combo boxes"""
        value = [text] if text != "Select options..." else []
        updates = {'tools': {'qct_parse': {field: value}}}
        self.config_mgr.update_config('checks', updates)

    def on_tagname_changed(self, text):
        """Handle changes in tagname field"""
        updates = {'tools': {'qct_parse': {'tagname': text if text else None}}}
        self.config_mgr.update_config('checks', updates)

    def on_mediaconch_policy_changed(self, policy_name):
        """Handle selection of MediaConch policy"""
        if not self.is_loading and policy_name:
            self.config_mgr.update_config('checks', {
                'tools': {
                    'mediaconch': {
                        'mediaconch_policy': policy_name
                    }
                }
            })
            self.update_current_policy_display(policy_name)
            logger.info(f"Updated config to use policy file: {policy_name}")

    def update_current_policy_display(self, policy_name):
        """Update the display of the current policy"""
        if policy_name:
            self.current_policy_display.setText(policy_name)
        else:
            self.current_policy_display.setText("No policy selected")

    def open_policy_file_dialog(self):
        """Open file dialog for selecting MediaConch policy file"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("XML files (*.xml)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                policy_path = selected_files[0]
                # Call setup_mediaconch_policy with selected file
                new_policy_name = setup_mediaconch_policy(policy_path)
                if new_policy_name:
                    # Refresh the UI to show the new policy file
                    self.load_config_values()
                else:
                    # Show error message if policy setup failed
                    QMessageBox.critical(
                        self,
                        "Error",
                        "Failed to import MediaConch policy file. Check logs for details."
                    )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signals = ProcessingSignals()
        self.worker = None  # Initialize worker as None
        self.processing_window = None

        # Connect all signals
        self.setup_signal_connections()

        # Init processing window
        self.processing_window = None
        
        # Setup UI
        self.setup_ui()

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
            # logger.debug(f"Error starting worker thread: {str(e)}")
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

        # Slot methods
    def on_processing_started(self, message):
        """Handle processing start"""
        # logger.debug("Processing started with message:", message)
        if self.processing_window is None:
            self.processing_window = ProcessingWindow(self)
            self.processing_window.cancel_button.clicked.connect(self.cancel_processing)
        self.processing_window.update_status(message)
        self.processing_window.show()
        self.processing_window.raise_()
        self.check_spex_button.setEnabled(False)
        QApplication.processEvents()
        
    def on_processing_completed(self, message):
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
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.processing_window.update_status("Cancelling processing...")
            self.processing_window.cancel_button.setEnabled(False)

    def on_processing_cancelled(self):
        if self.processing_window:
            self.processing_window.close()
            self.processing_window = None
        self.check_spex_button.setEnabled(True)
        QMessageBox.information(self, "Cancelled", "Processing was cancelled.")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        super().closeEvent(event)

    def on_tool_started(self, tool_name):
        if self.processing_window:
            self.processing_window.update_status(f"Starting {tool_name}")
        
    def on_tool_completed(self, message):
        if self.processing_window:
            self.processing_window.update_status(message)
            # Let UI update
            QApplication.processEvents()

    def on_fixity_progress(self, message):
        if self.processing_window:
            self.processing_window.update_detailed_status(message)

    def on_mediaconch_progress(self, message):
        if self.processing_window:
            self.processing_window.update_detailed_status(message)

    def on_metadata_progress(self, message):
        if self.processing_window:
            self.processing_window.update_detailed_status(message)

    def on_output_progress(self, message):
        if self.processing_window:
            self.processing_window.update_detailed_status(message)
        
    def setup_ui(self):
        # Move all UI initialization here
        self.config_mgr = ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
        self.spex_config = self.config_mgr.get_config('spex', SpexConfig)
        # Get the screen geometry
        screen = QApplication.primaryScreen().geometry()
        # Set window height to screen height, but keep a reasonable width
        self.resize(800, screen.height())
        
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

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Get the absolute path of the script file
        script_path = os.path.dirname(os.path.abspath(__file__))
        # Determine the  path to the image file
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
        logo_dir = os.path.join(root_dir, 'logo_image_files')

        # Add images at the top of the GUI
        self.add_image_to_top(logo_dir)

        # Create a QTabWidget for tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # First tab: "checks"
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

        import_directories_button = QPushButton("Import Directory...")
        import_directories_button.clicked.connect(self.import_directories)
        vertical_layout.addWidget(import_directories_button)

        # Selected directories section
        directory_label = QLabel("Selected Directories:")
        self.directory_list = DirectoryListWidget(self)
        vertical_layout.addWidget(directory_label)
        vertical_layout.addWidget(self.directory_list)

        # Remove directory button
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_selected_directory)
        vertical_layout.addWidget(delete_button)

        # Directory storage
        self.selected_directories = []

        # Command Profile Dropdown section
        command_profile_label = QLabel("Command profiles:")
        self.command_profile_dropdown = QComboBox()
        self.command_profile_dropdown.addItem("step1")
        self.command_profile_dropdown.addItem("step2")
        self.command_profile_dropdown.addItem("allOff")
        # Set dropdown based on condition
        if self.checks_config.tools.exiftool.run_tool == "yes":
            self.command_profile_dropdown.setCurrentText("step1")
        elif self.checks_config.tools.exiftool.run_tool == "no":
            self.command_profile_dropdown.setCurrentText("step2")
        self.command_profile_dropdown.currentIndexChanged.connect(self.on_profile_selected)
        vertical_layout.addWidget(command_profile_label)
        vertical_layout.addWidget(self.command_profile_dropdown)

        # Checkboxes (ConfigWidget) section
        command_checks_label = QLabel("Command options:")
        config_scroll_area = QScrollArea()
        self.config_widget = ConfigWindow(config_mgr=self.config_mgr)
        config_scroll_area.setWidgetResizable(True)
        config_scroll_area.setWidget(self.config_widget)

        # Add checkboxes and label to the vertical layout
        vertical_layout.addWidget(command_checks_label)
        vertical_layout.addWidget(config_scroll_area)

        # Set a minimum width for the config widget to ensure legibility
        config_scroll_area.setMinimumWidth(400)

        # Add the vertical layout to the scroll area
        checks_layout.addWidget(main_scroll_area)

        # Bottom row with "Check Spex!" button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        self.check_spex_button = QPushButton("Check Spex!")
        self.check_spex_button.clicked.connect(self.on_check_spex_clicked)
        bottom_row.addWidget(self.check_spex_button)

        checks_layout.addLayout(bottom_row)

        # Second tab: "spex"
        spex_tab = QWidget()
        spex_layout = QVBoxLayout(spex_tab)
        spex_tab.setLayout(spex_layout)
        self.tabs.addTab(spex_tab, "Spex")

        # Create a label to display the section name
        filename_section_label = QLabel(f"<b>Filename Values</b>")
        spex_layout.addWidget(filename_section_label)

        # Add a dropdown menu for command profiles
        filenames_profile_label = QLabel("Expected filename profiles:")
        spex_layout.addWidget(filenames_profile_label)

        self.filename_profile_dropdown = QComboBox()
        self.filename_profile_dropdown.addItem("Bowser file names")
        self.filename_profile_dropdown.addItem("JPC file names")
        # Set dropdown based on condition
        if self.spex_config.filename_values.Collection == "JPC":
            self.filename_profile_dropdown.setCurrentText("JPC file names")
        elif self.spex_config.filename_values.Collection == "2012_79":
            self.filename_profile_dropdown.setCurrentText("Bowser file names")
        self.filename_profile_dropdown.currentIndexChanged.connect(self.on_filename_profile_changed)
        spex_layout.addWidget(self.filename_profile_dropdown)

        # Create a toggle button to open a new window
        filename_button = QPushButton("Open Section")
        filename_button.clicked.connect(lambda: self.open_new_window('Filename Values', asdict(self.spex_config.filename_values)))
        spex_layout.addWidget(filename_button)
        
        # Create a label to display the section name
        mediainfo_section_label = QLabel(f"<b>MediaInfo Values</b>")
        spex_layout.addWidget(mediainfo_section_label)
         # Create a toggle button to open a new window
        mediainfo_toggle_button = QPushButton("Open Section")
        mediainfo_toggle_button.clicked.connect(lambda: self.open_new_window('MediaInfo Values', self.spex_config.mediainfo_values))
        spex_layout.addWidget(mediainfo_toggle_button)

        # Create a label to display the section name
        exiftool_section_label = QLabel(f"<b>Exiftool Values</b>")
        spex_layout.addWidget(exiftool_section_label)
         # Create a toggle button to open a new window
        exiftool_toggle_button = QPushButton("Open Section")
        exiftool_toggle_button.clicked.connect(lambda: self.open_new_window('Exiftool Values', asdict(self.spex_config.exiftool_values)))
        spex_layout.addWidget(exiftool_toggle_button)

        # Create a label to display the section name
        ffprobe_section_label = QLabel(f"<b>FFprobe Values</b>")
        spex_layout.addWidget(ffprobe_section_label)
         # Create a toggle button to open a new window
        ffprobe_toggle_button = QPushButton("Open Section")
        ffprobe_toggle_button.clicked.connect(lambda: self.open_new_window('FFprobe Values', self.spex_config.ffmpeg_values))
        spex_layout.addWidget(ffprobe_toggle_button)

        # Create a label to display the section name
        mediatrace_section_label = QLabel(f"<b>Mediatrace Values</b>")
        spex_layout.addWidget(mediatrace_section_label)

        # Add a dropdown menu for command profiles
        signalflow_profile_label = QLabel("Expected Signalflow profiles:")
        spex_layout.addWidget(signalflow_profile_label)

        self.signalflow_profile_dropdown = QComboBox()
        self.signalflow_profile_dropdown.addItem("JPC_AV_SVHS Signal Flow")
        self.signalflow_profile_dropdown.addItem("BVH3100 Signal Flow")
        # Set dropdown based on condition
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
        spex_layout.addWidget(self.signalflow_profile_dropdown)

        # Create a toggle button to open a new window
        mediatrace_toggle_button = QPushButton("Open Section")
        mediatrace_toggle_button.clicked.connect(lambda: self.open_new_window('Mediatrace Values', asdict(self.spex_config.mediatrace_values)))
        spex_layout.addWidget(mediatrace_toggle_button)

        # Create a label to display the section name
        qct_section_label = QLabel(f"<b>qct-parse Values</b>")
        spex_layout.addWidget(qct_section_label)
        # Create a toggle button to open a new window
        qct_toggle_button = QPushButton("Open Section")
        qct_toggle_button.clicked.connect(lambda: self.open_new_window('Expected qct-parse options', asdict(self.spex_config.qct_parse_values)))
        spex_layout.addWidget(qct_toggle_button)


    def add_image_to_top(self, logo_dir):
        """Add image to the top of the main layout."""
        image_layout = QHBoxLayout()
        
        image_file = os.path.join(logo_dir, "JPCA_H_Branding_011025.png")
        pixmap = QPixmap(image_file)
        
        label = QLabel()
        label.setMinimumHeight(100)  # Set minimum height to prevent image from disappearing
        
        # Scale pixmap to window width while keeping aspect ratio
        scaled_pixmap = pixmap.scaledToWidth(self.width(), Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image_layout.addWidget(label)
        self.main_layout.addLayout(image_layout)


    def import_directories(self):
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

    def add_network_drive(self, file_dialog):
        """
        Open a dialog to add a network drive manually
        """
        network_dialog = QInputDialog(self)
        network_dialog.setWindowTitle("Add Network Drive")
        network_dialog.setLabelText("Enter network path (e.g., //servername/share):")
        network_dialog.setTextValue("//")
        
        if network_dialog.exec():
            network_path = network_dialog.textValue()
            
            # Basic validation of network path
            if network_path.startswith("//"):
                # Check if the network path exists and is accessible
                if os.path.exists(network_path):
                    file_dialog.setDirectory(network_path)
                else:
                    QMessageBox.warning(self, "Network Drive", 
                                        "Cannot access the specified network path. "
                                        "Please check the path and your network connection.")
            else:
                QMessageBox.warning(self, "Invalid Path", 
                                    "Please enter a valid network path starting with //")


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
        """Handle the Start button click."""
        # logger.debug("Check Spex button clicked")  # Debug line
        self.update_selected_directories()
        self.check_spex_clicked = True  # Mark that the button was clicked
        self.call_process_directories()


    def on_profile_selected(self, index):
        selected_profile = self.command_profile_dropdown.currentText()
        if selected_profile == "step1":
            profile = edit_config.profile_step1
        elif selected_profile == "step2":
            profile = edit_config.profile_step2
        elif selected_profile == "allOff":
            profile = edit_config.profile_allOff
        try:
            # Call the backend function to apply the selected profile
            edit_config.apply_profile(profile)
            logger.debug(f"Profile '{selected_profile}' applied successfully.")
            self.config_mgr.save_last_used_config('checks')
        except ValueError as e:
            logger.critical(f"Error: {e}")

        self.config_widget.load_config_values()


    def on_filename_profile_changed(self, index):
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
        # self.config_mgr.save_last_used_config('spex')


    def on_signalflow_profile_changed(self, index):
        selected_option = self.signalflow_profile_dropdown.itemText(index)
        logger.debug(f"Selected signal flow profile: {selected_option}")

        if selected_option == "JPC_AV_SVHS Signal Flow":
            sn_config_changes = edit_config.JPC_AV_SVHS
        elif selected_option == "BVH3100 Signal Flow":
            sn_config_changes = edit_config.BVH3100
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
        
        # Rest of the original method remains the same
        self.new_window = QWidget()
        self.new_window.setWindowTitle(title)
        self.new_window.setLayout(QVBoxLayout())
        
        scroll_area = QScrollArea(self.new_window)
        scroll_area.setWidgetResizable(True)
        
        content_widget = QTextEdit()
        content_widget.setPlainText(content_text)
        content_widget.setReadOnly(True)
        content_widget.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        content_widget.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
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
        
