from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QLabel, 
    QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, QToolButton, QComboBox
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
        
        # Create a collapsible toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setText("Expand Section")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.clicked.connect(self.toggle_content)
        self.layout().addWidget(self.toggle_button)
        
        # Convert the content dictionary to a string before passing to QLabel
        content_text = self.dict_to_string(content)
        
        # Add content inside collapsible section
        self.content_widget = QLabel(content_text)
        self.content_widget.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.content_widget.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        self.layout().addWidget(self.content_widget)

         # Create a QScrollArea and set the content_widget as the scrollable widget
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # Correct constant usage for horizontal scroll
        self.scroll_area.setWidget(self.content_widget)  # Set the content_widget inside the scroll area
        
        # Add the scroll area to the layout
        self.layout().addWidget(self.scroll_area)
        
        self.toggle_content()  # Set the initial state

    def toggle_content(self):
        # Show/hide the content widget
        is_expanded = self.toggle_button.isChecked()
        self.content_widget.setVisible(is_expanded)
        self.scroll_area.setVisible(is_expanded)
        self.toggle_button.setText("Collapse Section" if is_expanded else "Expand Section")

    def dict_to_string(self, content_dict):
        """Convert a dictionary to a string representation for display."""
        content_str = "\n".join(f"{key}: {value}" for key, value in content_dict.items())
        return content_str
    

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

        # Scroll Area for Vertical Scrolling of Entire Layout
        main_scroll_area = QScrollArea(self)
        main_scroll_area.setWidgetResizable(True)
        main_widget = QWidget(self)
        main_scroll_area.setWidget(main_widget)
        
        # Horizontal layout for the main content
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

        # Third column: Selected expected values (Collapsible Sections)
        expected_values_column = QVBoxLayout()
        # Add a dropdown menu for command profiles
        values_profile_label = QLabel("Expected values options:")
        self.values_profile_dropdown = QComboBox()
        self.values_profile_dropdown.addItem("JPC_AV_SVHS Signal Flow")
        self.values_profile_dropdown.addItem("BVH3100 Signal Flow")
        self.values_profile_dropdown.addItem("Bowser file names")
        self.values_profile_dropdown.addItem("JPC file names")
        expected_values_column.addWidget(self.values_profile_dropdown)

        expected_values_column.addWidget(QLabel("Expected Values:"))

        # Dynamically add collapsible sections from config_dict
        for section, content in config_dict.items():
            collapsible_section = CollapsibleSection(section, content)
            expected_values_column.addWidget(collapsible_section)

        # Set a fixed width for the expected values section
        expected_values_column_widget = QWidget()
        expected_values_column_widget.setLayout(expected_values_column)
        expected_values_column_widget.setFixedWidth(300)  # Set a fixed width for the column

        horizontal_layout.addWidget(expected_values_column_widget)

        main_scroll_area.setMinimumWidth(1200)

        # Add the horizontal layout to the main layout
        self.main_layout.addWidget(main_scroll_area)

        # Bottom row with "Check Spex!" button
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        check_spex_button = QPushButton("Check Spex!")
        bottom_row.addWidget(check_spex_button)
        self.main_layout.addLayout(bottom_row)

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
        # You can perform different actions based on the selected profile here
        # For example, update other parts of the GUI or load different data
        # For now, we just print the selected profile to the console
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
