from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QLabel, 
    QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, QToolButton, QComboBox, QTabWidget,
    QTextEdit, QListView, QTreeView, QAbstractItemView, QInputDialog, QMessageBox, QToolBar
)
from PyQt6.QtCore import Qt, QUrl, QMimeData, QSettings, QDir
from PyQt6.QtGui import QPixmap, QAction

import os
import sys

from ..utils.find_config import config_path, command_config, yaml
from ..utils.log_setup import logger
from ..utils import yaml_profiles


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
    def __init__(self, command_config_dict, command_config):
        super().__init__()
        self.command_config_dict = command_config_dict
        self.command_config = command_config

        # Create the main layout only once
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)  # Assign layout at initialization

        # Populate the UI
        self.init_ui()

    def init_ui(self):
        # Populate the layout with widgets based on the config dictionary
        for section, items in self.command_config_dict.items():
            section_box = self.create_section(section, items)
            self.main_layout.addWidget(section_box)

        # Add spacer to use any remaining space
        self.main_layout.addStretch()

    def create_section(self, section_name, items):
        # Create a QGroupBox for each section
        group_box = QGroupBox(section_name)
        layout = QVBoxLayout()

        for key, value in items.items():
            if isinstance(value, dict):  # Nested dictionary
                sub_section = self.create_section(key, value)
                layout.addWidget(sub_section)
            elif isinstance(value, str):
                if value in ("yes", "no"):  # Checkbox for yes/no values
                    if key == "output_fixity":
                        checkbox = QCheckBox(f"{key} (to .txt and .md5 files)")
                    else:
                        checkbox = QCheckBox(key)
                    checkbox.setChecked(value == "yes")
                    checkbox.stateChanged.connect(
                        lambda state, name=key: self.on_checkbox_changed(state, name)
                    )
                    layout.addWidget(checkbox)
                else:  # QLineEdit for text fields
                    label = QLabel(key)
                    text_field = QLineEdit(value)
                    layout.addWidget(label)
                    layout.addWidget(text_field)
            elif isinstance(value, bool):  # Checkbox for True/False values
                checkbox = QCheckBox(key)
                checkbox.setChecked(value)
                checkbox.stateChanged.connect(
                    lambda state, name=key: self.on_checkbox_changed(state, name)
                )
                layout.addWidget(checkbox)

        group_box.setLayout(layout)
        return group_box

    def refresh_checkboxes(self, updated_config_dict):
        """Clear and repopulate the widgets based on the updated config."""
        self.command_config_dict = updated_config_dict

        # Remove all widgets from the main layout
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                child.layout().deleteLater()

        # Rebuild the UI
        self.init_ui()

    def on_checkbox_changed(self, value, command_name):
        """Handle changes in checkbox state."""
        # Convert the state to a Qt CheckState
        state = Qt.CheckState(value)
        
        if state == Qt.CheckState.Checked:
            logger.debug(f"Checkbox '{command_name}' is Checked.")
            # Call the backend function for 'on' state
            yaml_profiles.checkbox_on(self.command_config, command_name, 'on')
        elif state == Qt.CheckState.Unchecked:
            logger.debug(f"Checkbox '{command_name}' is Unchecked.")
            # Call the backend function for 'off' state
            yaml_profiles.checkbox_on(self.command_config, command_name, 'off')


class MainWindow(QMainWindow):
    def __init__(self, command_config, command_config_dict, config_path):
        super().__init__()
        
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
        self.add_images_to_top(logo_dir)

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
        # Set dropdown based on condition
        if command_config_dict["tools"]["exiftool"]["run_exiftool"] == "yes":
            self.command_profile_dropdown.setCurrentText("step1")
        elif command_config_dict["tools"]["exiftool"]["run_exiftool"] == "no":
            self.command_profile_dropdown.setCurrentText("step2")
        self.command_profile_dropdown.currentIndexChanged.connect(self.on_profile_selected)
        vertical_layout.addWidget(command_profile_label)
        vertical_layout.addWidget(self.command_profile_dropdown)

        # Checkboxes (ConfigWidget) section
        command_checks_label = QLabel("Command options:")
        config_scroll_area = QScrollArea()
        self.config_widget = ConfigWindow(command_config_dict, command_config)
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
        check_spex_button = QPushButton("Check Spex!")
        check_spex_button.clicked.connect(self.on_check_spex_clicked)
        bottom_row.addWidget(check_spex_button)

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
        if config_path.config_dict["filename_values"]["Collection"] == "JPC":
            self.filename_profile_dropdown.setCurrentText("JPC file names")
        elif config_path.config_dict["filename_values"]["Collection"] == "2012_79":
            self.filename_profile_dropdown.setCurrentText("Bowser file names")
        self.filename_profile_dropdown.currentIndexChanged.connect(self.on_filename_profile_changed)
        spex_layout.addWidget(self.filename_profile_dropdown)

        # Create a toggle button to open a new window
        filename_button = QPushButton("Open Section")
        filename_button.clicked.connect(lambda: self.open_new_window('Filename Values', config_path.config_dict['filename_values']))
        spex_layout.addWidget(filename_button)
        
        # Create a label to display the section name
        mediainfo_section_label = QLabel(f"<b>MediaInfo Values</b>")
        spex_layout.addWidget(mediainfo_section_label)
         # Create a toggle button to open a new window
        mediainfo_toggle_button = QPushButton("Open Section")
        mediainfo_toggle_button.clicked.connect(lambda: self.open_new_window('MediaInfo Values', config_path.config_dict['mediainfo_values']))
        spex_layout.addWidget(mediainfo_toggle_button)

        # Create a label to display the section name
        exiftool_section_label = QLabel(f"<b>Exiftool Values</b>")
        spex_layout.addWidget(exiftool_section_label)
         # Create a toggle button to open a new window
        exiftool_toggle_button = QPushButton("Open Section")
        exiftool_toggle_button.clicked.connect(lambda: self.open_new_window('Exiftool Values', config_path.config_dict['exiftool_values']))
        spex_layout.addWidget(exiftool_toggle_button)

        # Create a label to display the section name
        ffprobe_section_label = QLabel(f"<b>FFprobe Values</b>")
        spex_layout.addWidget(ffprobe_section_label)
         # Create a toggle button to open a new window
        ffprobe_toggle_button = QPushButton("Open Section")
        ffprobe_toggle_button.clicked.connect(lambda: self.open_new_window('FFprobe Values', config_path.config_dict['ffmpeg_values']))
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
        if "SVO5800" in config_path.config_dict["mediatrace"]["ENCODER_SETTINGS"]["Source VTR"]:
            self.signalflow_profile_dropdown.setCurrentText("JPC_AV_SVHS Signal Flow")
        elif "Sony BVH3100" in config_path.config_dict["mediatrace"]["ENCODER_SETTINGS"]["Source VTR"]:
            self.signalflow_profile_dropdown.setCurrentText("BVH3100 Signal Flow")
        self.signalflow_profile_dropdown.currentIndexChanged.connect(self.on_signalflow_profile_changed)
        spex_layout.addWidget(self.signalflow_profile_dropdown)

        # Create a toggle button to open a new window
        mediatrace_toggle_button = QPushButton("Open Section")
        mediatrace_toggle_button.clicked.connect(lambda: self.open_new_window('Mediatrace Values', config_path.config_dict['mediatrace']))
        spex_layout.addWidget(mediatrace_toggle_button)

        # Create a label to display the section name
        qct_section_label = QLabel(f"<b>qct-parse Values</b>")
        spex_layout.addWidget(qct_section_label)
        # Create a toggle button to open a new window
        qct_toggle_button = QPushButton("Open Section")
        qct_toggle_button.clicked.connect(lambda: self.open_new_window('Expected qct-parse options', config_path.config_dict['qct-parse']))
        spex_layout.addWidget(qct_toggle_button)


    def add_images_to_top(self, logo_dir):
        """Add three images to the top of the main layout."""
        image_layout = QHBoxLayout()
        image_files = [
            (os.path.join(logo_dir, "jpc_logo_purple.png")),
            (os.path.join(logo_dir, "av_spex_the_logo.png")),
            (os.path.join(logo_dir, "nmaahc_vert_purple.png"))
        ]

        for image_file in image_files:
            pixmap = QPixmap(image_file).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label = QLabel()
            label.setPixmap(pixmap)
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
        self.update_selected_directories()
        self.check_spex_clicked = True  # Mark that the button was clicked
        self.close()  # Close the GUI if needed, signaling readiness


    def on_profile_selected(self, index):
        # Get the selected profile from the dropdown
        selected_profile = self.command_profile_dropdown.currentText()
        try:
            # Call the backend function to apply the selected profile
            yaml_profiles.apply_selected_profile(selected_profile, command_config)
            logger.debug(f"Profile '{selected_profile}' applied successfully.")
            command_config.reload()
            self.config_widget.refresh_checkboxes(command_config.command_dict)
        except ValueError as e:
            logger.critical(f"Error: {e}")


    def on_filename_profile_changed(self, index):
        """
        Handle changes in the filename profile dropdown.
        :param index: The index of the selected item.
        """
        selected_option = self.filename_profile_dropdown.itemText(index)
        logger.debug(f"Selected filename profile: {selected_option}")
        if selected_option == "JPC file names":
            fn_config_changes = yaml_profiles.JPCAV_filename
        elif selected_option == "Bowser file names":
            fn_config_changes = yaml_profiles.bowser_filename
        else:
            fn_config_changes = None
        if fn_config_changes:
            yaml_profiles.update_config(config_path, 'filename_values', fn_config_changes)
            config_path.reload()


    def on_signalflow_profile_changed(self, index):
        # Get the selected profile from the dropdown
        selected_option = self.signalflow_profile_dropdown.itemText(index)
        logger.debug(f"Selected signal flow profile: {selected_option}")
        if selected_option == "JPC_AV_SVHS Signal Flow":
            sn_config_changes = yaml_profiles.JPC_AV_SVHS
        elif selected_option == "BVH3100 Signal Flow":
            sn_config_changes = yaml_profiles.BVH3100
        else:
            sn_config_changes = None
        if sn_config_changes:    
            yaml_profiles.update_config(config_path, 'ffmpeg_values.format.tags.ENCODER_SETTINGS', sn_config_changes)
            yaml_profiles.update_config(config_path, 'mediatrace.ENCODER_SETTINGS', sn_config_changes)
            config_path.reload()
        else:
            logger.error("Signal flow identifier not recognized, config not updated")


    def open_new_window(self, title, nested_dict):
        """
        Create and open a new window to display the section's content.
        Dynamically processes the nested_dict to avoid precomputing it.
        """

        # Process the nested_dict into a string representation
        content_text = self.dict_to_string(nested_dict)

        # Create a new window to display the processed content
        self.new_window = QWidget()
        self.new_window.setWindowTitle(title)
        self.new_window.setLayout(QVBoxLayout())

        # Add the content in a scrollable area
        scroll_area = QScrollArea(self.new_window)
        scroll_area.setWidgetResizable(True)

        # Create a content widget for detailed content
        content_widget = QTextEdit()
        content_widget.setPlainText(content_text)  # Use plain-text mode
        content_widget.setReadOnly(True)  # Make the text widget read-only
        content_widget.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        content_widget.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        scroll_area.setWidget(content_widget)

        # Add the scroll area to the new window
        self.new_window.layout().addWidget(scroll_area)

        # Show the new window
        self.new_window.resize(600, 400)  # Set an appropriate size
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
        self.close()  # Close the GUI