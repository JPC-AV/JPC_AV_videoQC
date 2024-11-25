from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QLabel, 
    QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, QToolButton, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt
from ruamel.yaml import YAML
import os
import sys


class ConfigWindow(QWidget):
    def __init__(self, command_config_dict):
        super().__init__()
        self.command_config_dict = command_config_dict
        self.init_ui()

    def init_ui(self):
        # Create the main layout
        main_layout = QVBoxLayout(self)
        
        # Populate the GUI based on the nested dictionary
        for section, items in self.command_config_dict.items():
            section_box = self.create_section(section, items)
            main_layout.addWidget(section_box)
        
        # Spacer for remaining space
        main_layout.addStretch()

    def create_section(self, section_name, items):
        # Create a QGroupBox for each main section
        group_box = QGroupBox(section_name)
        layout = QVBoxLayout()
        
        for key, value in items.items():
            if isinstance(value, dict):  # Nested dictionary
                sub_section = self.create_section(key, value)
                layout.addWidget(sub_section)
            elif isinstance(value, str):
                if value in ("yes", "no"):  # Checkbox for yes/no values
                    checkbox = QCheckBox(key)
                    checkbox.setChecked(value == "yes")
                    layout.addWidget(checkbox)
                else:  # QLineEdit for text fields
                    label = QLabel(key)
                    text_field = QLineEdit(value)
                    layout.addWidget(label)
                    layout.addWidget(text_field)
            elif isinstance(value, bool):  # Checkbox for True/False values
                checkbox = QCheckBox(key)
                checkbox.setChecked(value)
                layout.addWidget(checkbox)

        group_box.setLayout(layout)
        return group_box


class CollapsibleSection(QGroupBox):
    def __init__(self, title, content):
        super().__init__()
        self.setTitle("")  # Remove the default group box title
        self.setLayout(QVBoxLayout())
        
        # Create a label to display the section name
        section_label = QLabel(f"<b>{title}</b>")
        self.layout().addWidget(section_label)

        if title == 'filename_values':
            # Add a dropdown menu for command profiles
            filenames_profile_label = QLabel("Expected filename options:")
            self.filename_profile_dropdown = QComboBox()
            self.filename_profile_dropdown.addItem("Bowser file names")
            self.filename_profile_dropdown.addItem("JPC file names")
            self.layout().addWidget(self.filename_profile_dropdown)

        if title == 'mediatrace':
            # Add a dropdown menu for command profiles
            signalflow_profile_label = QLabel("Expected Signalflow options:")
            self.signalflow_profile_dropdown = QComboBox()
            self.signalflow_profile_dropdown.addItem("JPC_AV_SVHS Signal Flow")
            self.signalflow_profile_dropdown.addItem("BVH3100 Signal Flow")
            self.layout().addWidget(self.signalflow_profile_dropdown)

        # Create a toggle button to open a new window
        self.toggle_button = QPushButton("Open Section")
        self.toggle_button.clicked.connect(self.open_new_window)
        self.layout().addWidget(self.toggle_button)

        # Convert the content dictionary to a string for display in the new window
        self.content_text = self.dict_to_string(content)
        self.title = title

        # Keep a reference to the new window to prevent it from being garbage-collected
        self.new_window = None

    def open_new_window(self):
        # Create a new window to display the section's content
        self.new_window = QWidget()
        self.new_window.setWindowTitle(self.title)
        self.new_window.setLayout(QVBoxLayout())

        # Add the content in a scrollable area
        scroll_area = QScrollArea(self.new_window)
        scroll_area.setWidgetResizable(True)

        # Create a content widget for detailed content
        content_widget = QLabel(self.content_text)
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
                    content_lines.append(f"{indent}{indent}  {item}")
            else:  # For all other types (e.g., strings, numbers)
                content_lines.append(f"{indent}{key}: {value}")

        return "\n".join(content_lines)



class MainWindow(QMainWindow):
    def __init__(self, command_config_dict, config_dict):
        super().__init__()
        self.setWindowTitle("Main Application")
        
        # Set up menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.file_menu = self.menu_bar.addMenu("File")
        self.import_action = self.file_menu.addAction("Import Directory")
        self.import_action.triggered.connect(self.import_directory)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

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
        
        # Horizontal layout for the main content in "Checks"
        horizontal_layout = QHBoxLayout(main_widget)

        # First column: Selected directories
        directory_column = QVBoxLayout()
        directory_column.addWidget(QLabel("Selected Directories:"))
        self.directory_list = QListWidget()
        directory_column.addWidget(self.directory_list)
        horizontal_layout.addLayout(directory_column)

        # Second column: Command Profile Dropdown + Checkboxes (ConfigWidget)
        config_column = QVBoxLayout()
        
        # Add a dropdown menu for command profiles
        command_profile_label = QLabel("Command profiles:")
        self.command_profile_dropdown = QComboBox()
        self.command_profile_dropdown.addItem("step1")
        self.command_profile_dropdown.addItem("step2")
        self.command_profile_dropdown.currentIndexChanged.connect(self.on_profile_selected)

        # Add the dropdown to the config column
        config_column.addWidget(command_profile_label)
        config_column.addWidget(self.command_profile_dropdown)

        # Checkboxes (ConfigWidget) section
        command_checks_label = QLabel("Command options:")
        config_scroll_area = QScrollArea()
        self.config_widget = ConfigWindow(command_config_dict)
        config_scroll_area.setWidgetResizable(True)
        config_scroll_area.setWidget(self.config_widget)

        # Add checkboxes and label to config column
        config_column.addWidget(command_checks_label)
        config_column.addWidget(config_scroll_area)

        # Set a minimum width for the config widget to ensure legibility
        config_scroll_area.setMinimumWidth(400)  # Set minimum width for the center column
        
        horizontal_layout.addLayout(config_column)

        # Add the horizontal layout to the "checks" tab layout
        checks_layout.addWidget(main_scroll_area)

        # Bottom row with "Check Spex!" button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        check_spex_button = QPushButton("Check Spex!")
        bottom_row.addWidget(check_spex_button)
        checks_layout.addLayout(bottom_row)

        # Second tab: "spex"
        spex_tab = QWidget()
        spex_layout = QVBoxLayout(spex_tab)
        self.tabs.addTab(spex_tab, "Spex")

        # Dynamically add collapsible sections from config_dict
        spex_layout.addWidget(QLabel("Expected Values:"))
        for section, content in config_dict.items():
            collapsible_section = CollapsibleSection(section, content)
            spex_layout.addWidget(collapsible_section)

        # Directory storage
        self.selected_directories = []

    def import_directory(self):
        # Open a file dialog to select a directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory and directory not in self.selected_directories:
            self.selected_directories.append(directory)
            self.directory_list.addItem(directory)

    def on_profile_selected(self, index):
        # Handle the dropdown menu selection change
        selected_profile = self.command_profile_dropdown.currentText()
        print(f"Selected profile: {selected_profile}")
        if selected_profile == "step1":
            print("Step 1 profile selected.")
        elif selected_profile == "step2":
            print("Step 2 profile selected.")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load config_dict from a YAML file
    yaml = YAML()
    yaml.preserve_quotes = True
    config_yml = os.path.join('/Users/eddycolloton/git/JPC_AV/JPC_AV_videoQC/config/', 'config.yaml')

    with open(config_yml) as f:
        config_dict = yaml.load(f)

    # Example command_config_dict for checkboxes section
    command_config_dict = {
        'outputs': {
            'access_file': 'no',
            'report': 'no',
            'fixity': {
                'check_fixity': 'no',
                'check_stream_fixity': 'no',
                'embed_stream_fixity': 'yes',
                'output_fixity': 'yes',
                'overwrite_stream_fixity': 'no'
            },
            'qctools_ext': 'qctools.xml.gz'
        },
        'tools': {
            'exiftool': {'check_exiftool': 'yes', 'run_exiftool': 'yes'},
            'ffprobe': {'check_ffprobe': 'no', 'run_ffprobe': 'yes'},
            'mediaconch': {'mediaconch_policy': 'JPC_AV_NTSC_MKV_2024-07-31.xml', 'run_mediaconch': 'yes'},
            'mediainfo': {'check_mediainfo': 'yes', 'run_mediainfo': 'yes'},
            'mediatrace': {'check_mediatrace': 'yes', 'run_mediatrace': 'yes'},
            'qctools': {'check_qctools': 'no', 'run_qctools': 'no'},
            'qct-parse': {
                'barsDetection': True,
                'evaluateBars': True,
                'contentFilter': None,
                'profile': None,
                'tagname': None,
                'thumbExport': True
            }
        }
    }

    # Create and display the main window
    window = MainWindow(command_config_dict, config_dict)
    window.show()

    sys.exit(app.exec())
