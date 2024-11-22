from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QLineEdit, QLabel, 
    QScrollArea, QFileDialog, QMenuBar, QListWidget, QPushButton, QFrame, QToolButton
)
from PyQt6.QtCore import Qt
import sys


class ConfigWindow(QWidget):
    def __init__(self, config_dict):
        super().__init__()
        self.config_dict = config_dict
        self.init_ui()

    def init_ui(self):
        # Create the main layout
        main_layout = QVBoxLayout(self)
        
        # Populate the GUI based on the nested dictionary
        for section, items in self.config_dict.items():
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
    def __init__(self, title, content_text):
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
        
        # Add content inside collapsible section
        self.content_widget = QLabel(content_text)
        self.content_widget.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)
        self.content_widget.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        self.layout().addWidget(self.content_widget)
        
        self.toggle_content()  # Set the initial state

    def toggle_content(self):
        # Show/hide the content widget
        is_expanded = self.toggle_button.isChecked()
        self.content_widget.setVisible(is_expanded)
        self.toggle_button.setText("Collapse Section" if is_expanded else "Expand Section")


class MainWindow(QMainWindow):
    def __init__(self, config_dict):
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

        # Horizontal layout for the main content
        horizontal_layout = QHBoxLayout()

        # First column: Selected directories
        directory_column = QVBoxLayout()
        directory_column.addWidget(QLabel("Selected Directories:"))
        self.directory_list = QListWidget()
        directory_column.addWidget(self.directory_list)
        horizontal_layout.addLayout(directory_column)

        # Second column: Checkboxes (ConfigWidget)
        config_scroll_area = QScrollArea()
        self.config_widget = ConfigWindow(config_dict)
        config_scroll_area.setWidgetResizable(True)
        config_scroll_area.setWidget(self.config_widget)
        horizontal_layout.addWidget(config_scroll_area)

        # Third column: Selected expected values
        expected_values_column = QVBoxLayout()
        expected_values_column.addWidget(QLabel("Selected Expected Values:"))
        expected_values_column.addWidget(CollapsibleSection("mediainfo", "resolution: 1920x1080"))
        expected_values_column.addWidget(CollapsibleSection("ffprobe", "resolution: 1920x1080"))
        expected_values_column.addWidget(CollapsibleSection("exiftool", "resolution: 1920x1080"))
        horizontal_layout.addLayout(expected_values_column)

        # Add the horizontal layout to the main layout
        self.main_layout.addLayout(horizontal_layout)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example dictionary structure
    config_dict = {
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
    window = MainWindow(config_dict)
    window.show()

    sys.exit(app.exec())
