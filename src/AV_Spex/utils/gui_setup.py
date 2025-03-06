from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QLabel, 
    QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, QComboBox, QTabWidget,
    QTextEdit, QAbstractItemView, QInputDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QSettings, QDir, QTimer
from PyQt6.QtGui import QPixmap, QPalette

import os
import sys
from dataclasses import asdict

from ..utils.setup_config import SpexConfig, ChecksConfig
from ..utils.config_manager import ConfigManager
from ..utils.log_setup import logger
from ..utils import edit_config

from ..processing.processing_mgmt import setup_mediaconch_policy
from ..processing.worker_thread import ProcessingWorker

from ..processing.avspex_processor import AVSpexProcessor
from ..utils.signals import ProcessingSignals

from ..utils.theme_manager import ThemeManager, ThemeableMixin

class ProcessingWindow(QMainWindow, ThemeableMixin):
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
        self.details_text.setMinimumHeight(100)
        layout.addWidget(self.details_text, 1) # stretch factor of 1

        # Add cancel button
        self.cancel_button = QPushButton("Cancel")
        layout.addWidget(self.cancel_button)

        # Center the window on screen
        self._center_on_screen()  # Changed to use the defined method
        
       # Setup theme handling
        self.setup_theme_handling()
        
        # Center the window on screen
        self._center_on_screen()
        
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
        # Get a reference to the parent (MainWindow)
        parent = self.parent()
        
        # If parent exists and has a cancel_processing method, call it
        if parent and hasattr(parent, 'cancel_processing'):
            parent.cancel_processing()
        
        # Call the parent class's closeEvent to properly handle window closure
        super().closeEvent(event)

    # Override the on_theme_changed method if needed
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


class ConfigWindow(QWidget, ThemeableMixin):
    def __init__(self, config_mgr=None):
        super().__init__()
        self.config_mgr = config_mgr or ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)

        # Setup theme handling
        self.setup_theme_handling()
        
        # Track theme-aware components
        self.themed_group_boxes = {}
        
        # Setup UI and load config
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        """Create fixed layout structure"""
        main_layout = QVBoxLayout(self)

        self.setup_outputs_section(main_layout)
        self.setup_fixity_section(main_layout)
        self.setup_tools_section(main_layout)
        self.connect_signals()
        
    # Outputs Section
    def setup_outputs_section(self, main_layout, update_existing=False):
        """Set up the outputs section with palette-aware styling"""
        theme_manager = ThemeManager()
        
        # Creating a new outputs group
        self.outputs_group = QGroupBox("Outputs")
        theme_manager.style_groupbox(self.outputs_group, "top left")
        self.themed_group_boxes['outputs'] = self.outputs_group

        outputs_layout = QVBoxLayout()
        
        # Create widgets with descriptions on second line
        self.access_file_cb = QCheckBox("Access File")
        self.access_file_cb.setStyleSheet("font-weight: bold;")
        access_file_desc = QLabel("Creates a h264 access file of the input .mkv file")
        access_file_desc.setIndent(20)  # Indented to align with checkbox text
        
        self.report_cb = QCheckBox("HTML Report")
        self.report_cb.setStyleSheet("font-weight: bold;")
        report_desc = QLabel("Creates a .html report containing the results of Spex Checks")
        report_desc.setIndent(20)
        
        self.qctools_ext_label = QLabel("QCTools File Extension")
        self.qctools_ext_label.setStyleSheet("font-weight: bold;")
        qctools_ext_desc = QLabel("Set the extension for QCTools output")
        self.qctools_ext_input = QLineEdit()

        # Create a horizontal layout for the QCTools extension input
        qctools_ext_layout = QHBoxLayout()
        qctools_ext_layout.addWidget(self.qctools_ext_label)
        qctools_ext_layout.addWidget(self.qctools_ext_input)
        
        # Add to layout
        outputs_layout.addWidget(self.access_file_cb)
        outputs_layout.addWidget(access_file_desc)
        outputs_layout.addWidget(self.report_cb)
        outputs_layout.addWidget(report_desc)

        # Create a vertical layout just for the QCTools section
        qctools_section = QVBoxLayout()
        qctools_section.addLayout(qctools_ext_layout)
        qctools_ext_desc.setIndent(150)
        qctools_section.addWidget(qctools_ext_desc)
        # Add the QCTools section to the main outputs layout
        outputs_layout.addLayout(qctools_section)
        
        self.outputs_group.setLayout(outputs_layout)
        main_layout.addWidget(self.outputs_group)
    
    # Fixity Section
    def setup_fixity_section(self, main_layout):
        """Set up the fixity section with palette-aware styling"""
        theme_manager = ThemeManager()
        
        # Creating a new fixity group
        self.fixity_group = QGroupBox("Fixity")
        theme_manager.style_groupbox(self.fixity_group, "top left")
        self.themed_group_boxes['fixity'] = self.fixity_group
        
        fixity_layout = QVBoxLayout()
        
        # Create checkboxes with descriptions on second line
        self.output_fixity_cb = QCheckBox("Output fixity")
        self.output_fixity_cb.setStyleSheet("font-weight: bold;")
        output_fixity_desc = QLabel("Generate whole file md5 checksum of .mkv files to .txt and .md5")
        output_fixity_desc.setIndent(20)
        
        self.check_fixity_cb = QCheckBox("Validate fixity")
        self.check_fixity_cb.setStyleSheet("font-weight: bold;")
        check_fixity_desc = QLabel("Validates fixity of .mkv files against a checksum file in the directory")
        check_fixity_desc.setIndent(20)
        
        self.embed_stream_cb = QCheckBox("Embed Stream fixity")
        self.embed_stream_cb.setStyleSheet("font-weight: bold;")
        embed_stream_desc = QLabel("Embeds video and audio stream checksums into .mkv tags")
        embed_stream_desc.setIndent(20)
        
        self.overwrite_stream_cb = QCheckBox("Overwrite Stream fixity")
        self.overwrite_stream_cb.setStyleSheet("font-weight: bold;")
        overwrite_stream_desc = QLabel("Embed stream checksums regardless if existing ones are found")
        overwrite_stream_desc.setIndent(20)
        
        self.validate_stream_cb = QCheckBox("Validate Stream fixity")
        self.validate_stream_cb.setStyleSheet("font-weight: bold;")
        validate_stream_desc = QLabel("Validates any embedded stream fixity, will not run if there is no embedded steam fixity")
        validate_stream_desc.setIndent(20)
        
        # Add to layout
        fixity_layout.addWidget(self.output_fixity_cb)
        fixity_layout.addWidget(output_fixity_desc)
        fixity_layout.addWidget(self.check_fixity_cb)
        fixity_layout.addWidget(check_fixity_desc)
        fixity_layout.addWidget(self.embed_stream_cb)
        fixity_layout.addWidget(embed_stream_desc)
        fixity_layout.addWidget(self.overwrite_stream_cb)
        fixity_layout.addWidget(overwrite_stream_desc)
        fixity_layout.addWidget(self.validate_stream_cb)
        fixity_layout.addWidget(validate_stream_desc)
        
        self.fixity_group.setLayout(fixity_layout)
        main_layout.addWidget(self.fixity_group)
        
    # Tools Section
    def setup_tools_section(self, main_layout, update_existing=False):
        """Set up the tools section with palette-aware styling"""
        theme_manager = ThemeManager()
    
        # Main Tools group box with centered title
        self.tools_group = QGroupBox("Tools")
        theme_manager.style_groupbox(self.tools_group, "top center")
        self.themed_group_boxes['tools'] = self.tools_group

        tools_layout = QVBoxLayout()
        
        # Dictionary to store references to all tool group boxes
        self.tool_group_boxes = {}
        
        # Setup basic tools
        basic_tools = ['exiftool', 'ffprobe', 'mediainfo', 'mediatrace', 'qctools']
        self.tool_widgets = {}
        
        # Individual tool group boxes with left-aligned titles
        for tool in basic_tools:
            # Create new group box for this tool
            tool_group = QGroupBox(tool)
            theme_manager.style_groupbox(tool_group, "top left")
            tool_layout = QVBoxLayout()
            
            # Store reference to this group box
            self.tool_group_boxes[tool] = tool_group
            self.themed_group_boxes[f'tool_{tool}'] = tool_group
            
            if tool.lower() == 'qctools':
                run_cb = QCheckBox("Run Tool")
                run_cb.setStyleSheet("font-weight: bold;")
                run_desc = QLabel("Run QCTools on input video file")
                run_desc.setIndent(20)
                
                self.tool_widgets[tool] = {'run': run_cb}
                tool_layout.addWidget(run_cb)
                tool_layout.addWidget(run_desc)
            else:
                check_cb = QCheckBox("Check Tool")
                check_cb.setStyleSheet("font-weight: bold;")
                check_desc = QLabel("Check the output of the tool against expected Spex")
                check_desc.setIndent(20)
                
                run_cb = QCheckBox("Run Tool")
                run_cb.setStyleSheet("font-weight: bold;")
                run_desc = QLabel(f"Run the tool on the input video")
                run_desc.setIndent(20)
                
                self.tool_widgets[tool] = {'check': check_cb, 'run': run_cb}
                tool_layout.addWidget(check_cb)
                tool_layout.addWidget(check_desc)
                tool_layout.addWidget(run_cb)
                tool_layout.addWidget(run_desc)
            
            tool_group.setLayout(tool_layout)
            tools_layout.addWidget(tool_group)

        # MediaConch section
        self.mediaconch_group = QGroupBox("Mediaconch")
        theme_manager.style_groupbox(self.mediaconch_group, "top left")
        self.themed_group_boxes['mediaconch'] = self.mediaconch_group

        mediaconch_layout = QVBoxLayout()

        self.run_mediaconch_cb = QCheckBox("Run Mediaconch")
        self.run_mediaconch_cb.setStyleSheet("font-weight: bold;")
        run_mediaconch_desc = QLabel("Run MediaConch validation on input files")
        run_mediaconch_desc.setIndent(20)

        # Policy selection
        policy_container = QWidget()
        policy_layout = QVBoxLayout(policy_container)

        # Current policy display
        current_policy_widget = QWidget()
        current_policy_layout = QHBoxLayout(current_policy_widget)
        current_policy_layout.setContentsMargins(0, 0, 0, 0)

        self.policy_label = QLabel("Current policy:")
        self.policy_label.setStyleSheet("font-weight: bold;")
        self.current_policy_display = QLabel()
        self.current_policy_display.setStyleSheet("font-weight: bold;")

        current_policy_layout.addWidget(self.policy_label)
        current_policy_layout.addWidget(self.current_policy_display)
        current_policy_layout.addStretch()

        self.policy_combo = QComboBox()
        policies_label = QLabel("Available policies:")
        policies_label.setStyleSheet("font-weight: bold;")
        self.import_policy_btn = QPushButton("Import New MediaConch Policy")
        import_policy_desc = QLabel("Import a custom policy file for MediaConch validation")

        policy_layout.addWidget(current_policy_widget)
        policy_layout.addWidget(policies_label)
        policy_layout.addWidget(self.policy_combo)
        policy_layout.addWidget(self.import_policy_btn)
        policy_layout.addWidget(import_policy_desc)

        mediaconch_layout.addWidget(self.run_mediaconch_cb)
        mediaconch_layout.addWidget(run_mediaconch_desc)
        mediaconch_layout.addWidget(policy_container)
        self.mediaconch_group.setLayout(mediaconch_layout)
        tools_layout.addWidget(self.mediaconch_group)

        # QCT Parse section
        self.qct_group = QGroupBox("qct-parse")
        theme_manager.style_groupbox(self.qct_group, "top left")
        self.themed_group_boxes['qct'] = self.qct_group

        qct_layout = QVBoxLayout()

        # Checkboxes with descriptions on second line
        self.run_qctparse_cb = QCheckBox("Run Tool")
        self.run_qctparse_cb.setStyleSheet("font-weight: bold;")
        run_qctparse_desc = QLabel("Run qct-parse tool on input video file")
        run_qctparse_desc.setIndent(20)

        self.bars_detection_cb = QCheckBox("Detect Color Bars")
        self.bars_detection_cb.setStyleSheet("font-weight: bold;")
        bars_detection_desc = QLabel("Detect color bars in the video content")
        bars_detection_desc.setIndent(20)

        self.evaluate_bars_cb = QCheckBox("Evaluate Color Bars")
        self.evaluate_bars_cb.setStyleSheet("font-weight: bold;")
        evaluate_bars_desc = QLabel("Compare content to color bars for validation")
        evaluate_bars_desc.setIndent(20)

        self.thumb_export_cb = QCheckBox("Thumbnail Export")
        self.thumb_export_cb.setStyleSheet("font-weight: bold;")
        thumb_export_desc = QLabel("Export thumbnails of failed frames for review")
        thumb_export_desc.setIndent(20)

        # Content Filter
        content_filter_label = QLabel("Content Detection")
        content_filter_label.setStyleSheet("font-weight: bold;")
        content_filter_desc = QLabel("Select type of content to detect in the video")
        self.content_filter_combo = QComboBox()
        self.content_filter_combo.addItem("Select options...", None)  # Store None as data

        # Create a mapping of display text to actual values
        content_filter_options = {
            "All Black Detection": "allBlack",
            "Static Content Detection": "static"
        }

        # Add items with display text and corresponding data value
        for display_text, value in content_filter_options.items():
            self.content_filter_combo.addItem(display_text, value)
                
        # Profile
        profile_label = QLabel("Profile")
        profile_label.setStyleSheet("font-weight: bold;")
        profile_desc = QLabel("Select tolerance profile for content analysis")
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Select options...", None)  # Store None as data

        # Create a mapping of display text to actual values
        profile_options = {
            "Default Profile": "default",
            "High Tolerance": "highTolerance",
            "Medium Tolerance": "midTolerance",
            "Low Tolerance": "lowTolerance"
        }

        # Add items with display text and corresponding data value
        for display_text, value in profile_options.items():
            self.profile_combo.addItem(display_text, value)

        # Add all widgets to the qct layout
        qct_layout.addWidget(self.run_qctparse_cb)
        qct_layout.addWidget(run_qctparse_desc)
        qct_layout.addWidget(self.bars_detection_cb)
        qct_layout.addWidget(bars_detection_desc)
        qct_layout.addWidget(self.evaluate_bars_cb)
        qct_layout.addWidget(evaluate_bars_desc)
        qct_layout.addWidget(self.thumb_export_cb)
        qct_layout.addWidget(thumb_export_desc)
        qct_layout.addWidget(content_filter_label)
        qct_layout.addWidget(content_filter_desc)
        qct_layout.addWidget(self.content_filter_combo)
        qct_layout.addWidget(profile_label)
        qct_layout.addWidget(profile_desc)
        qct_layout.addWidget(self.profile_combo)

        self.qct_group.setLayout(qct_layout)
        tools_layout.addWidget(self.qct_group)
        
        # Tagname
        tagname_label = QLabel("Tag Name")
        tagname_label.setStyleSheet("font-weight: bold;")
        tagname_desc = QLabel("Input ad hoc tags using this format: YMIN, lt, 100 (tag name, lt or gt, number value)")
        self.tagname_input = QLineEdit()
        self.tagname_input.setPlaceholderText("None")
        qct_layout.addWidget(tagname_label)
        qct_layout.addWidget(tagname_desc)
        qct_layout.addWidget(self.tagname_input)
        
        self.tools_group.setLayout(tools_layout)
        main_layout.addWidget(self.tools_group)

        # Style all buttons
        theme_manager.style_buttons(self)

    def on_theme_changed(self, palette):
        """Handle theme changes for ConfigWindow"""
        # Apply the palette directly
        self.setPalette(palette)
        
        # Get the theme manager
        theme_manager = ThemeManager.instance()
        
        # Update all tracked group boxes
        for key, group_box in self.themed_group_boxes.items():
            # Main tools group has center-aligned title
            if key == 'tools':
                theme_manager.style_groupbox(group_box, "top center")
            else:
                theme_manager.style_groupbox(group_box, "top left")
        
        # Style all buttons
        theme_manager.style_buttons(self)
        
        # Force repaint
        self.update()

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
            lambda state: self.on_checkbox_changed(state, ['tools', 'qct_parse', 'run_tool'])
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
        self.content_filter_combo.currentIndexChanged.connect(
            lambda index: self.on_qct_combo_changed(self.content_filter_combo.itemData(index), 'contentFilter')
        )
        self.profile_combo.currentIndexChanged.connect(
            lambda index: self.on_qct_combo_changed(self.profile_combo.itemData(index), 'profile')
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
        available_policies = self.config_mgr.get_available_policies()
        self.policy_combo.clear()
        self.policy_combo.addItems(available_policies)
        
        # Temporarily block signals while setting the current text
        self.policy_combo.blockSignals(True)
        mediaconch = self.checks_config.tools.mediaconch
        if mediaconch.mediaconch_policy in available_policies:
            self.policy_combo.setCurrentText(mediaconch.mediaconch_policy)
        self.policy_combo.blockSignals(False)
        
        # QCT Parse
        qct = self.checks_config.tools.qct_parse
        self.run_qctparse_cb.setChecked(qct.run_tool.lower() == 'yes')
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

    def on_qct_combo_changed(self, value, field):
        """Handle changes in QCT Parse combo boxes"""
        values = [value] if value is not None else []
        updates = {'tools': {'qct_parse': {field: values}}}
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


class MainWindow(QMainWindow, ThemeableMixin):
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

    # When setting up tabs or other UI components
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
        # Clean up child windows with theme connections
        for child_window in ['config_widget', 'processing_window']:
            if hasattr(self, child_window) and getattr(self, child_window):
                child = getattr(self, child_window)
                if hasattr(child, 'cleanup_theme_handling'):
                    child.cleanup_theme_handling()
        
        # Existing code
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        
        # Call our quit handling method
        self.on_quit_clicked()
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
        self.config_mgr = ConfigManager()
        self.checks_config = self.config_mgr.get_config('checks', ChecksConfig)
        self.spex_config = self.config_mgr.get_config('spex', SpexConfig)

        self.resize(800, 900)
        
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
        if getattr(sys, 'frozen', False):
            QTimer.singleShot(0, self._delayed_logo_setup)
        else:
            self._load_logo()

    def _delayed_logo_setup(self):
        self._load_logo()

    def _load_logo(self):
        logo_path = self.config_mgr.get_logo_path('JPCA_H_Branding_011025.png')
        image_layout = self.add_image_to_top(logo_path)
        self.main_layout.insertLayout(0, image_layout)  # Insert at index 0 (top)


    # First tab: "checks"
    def setup_checks_tab(self, update_existing=False):
        """Set up or update the Checks tab with theme-aware styling"""
        # Get the theme manager instance
        theme_manager = ThemeManager()

        # Skip creation if we're just updating themes
        if update_existing:
            return
        
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
        self.config_widget = ConfigWindow(config_mgr=self.config_mgr)
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

    # Main layout
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

    # Second tab: "spex"
    def setup_spex_tab(self, update_existing=False):
        """Set up or update the Spex tab with theme-aware styling"""
        # Get the theme manager instance
        theme_manager = ThemeManager()
        
        # Skip creation if we're just updating themes
        if update_existing:
            return
        
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
        theme_manager.style_groupbox(self.filename_group)
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
        theme_manager.style_groupbox(self.mediainfo_group)
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
        theme_manager.style_groupbox(self.exiftool_group)
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
        theme_manager.style_groupbox(self.ffprobe_group)
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
        theme_manager.style_groupbox(self.mediatrace_group)
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
        theme_manager.style_groupbox(self.qct_group)
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
        """Handle the Start button click."""
        # logger.debug("Check Spex button clicked")  # Debug line
        self.update_selected_directories()
        self.check_spex_clicked = True  # Mark that the button was clicked
        self.config_mgr.save_last_used_config('checks')
        self.config_mgr.save_last_used_config('spex')
        self.call_process_directories()


    def on_profile_selected(self, index):
        selected_profile = self.command_profile_dropdown.currentText()
        if selected_profile == "Step 1":
            profile = edit_config.profile_step1
        elif selected_profile == "Step 2":
            profile = edit_config.profile_step2
        elif selected_profile == "All Off":
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
        self.config_mgr.save_last_used_config('spex')


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
