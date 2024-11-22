from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QCheckBox, QLineEdit, QLabel, QGroupBox, QScrollArea,
    QFileDialog, QMenuBar, QListWidget, QHBoxLayout, QPushButton
)
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

        # Central layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)

        # Directory list display
        self.directory_list = QListWidget()
        self.central_layout.addWidget(QLabel("Selected Directories:"))
        self.central_layout.addWidget(self.directory_list)

        # Config widget
        self.config_widget = ConfigWindow(config_dict)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.config_widget)
        self.central_layout.addWidget(scroll_area)

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
