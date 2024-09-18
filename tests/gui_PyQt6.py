from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QCheckBox
)

def create_checkbox(layout, command_dict, key, text):
    """
    Creates a checkbox and adds it to the layout.
    """
    checkbox = QCheckBox(text)
    checkbox.setChecked(command_dict[key]) 
    checkbox.stateChanged.connect(lambda state: command_dict.update({key: state == 2})) 
    layout.addWidget(checkbox)

if __name__ == "__main__":
    app = QApplication([])

    command_dict = {
        "access_file": False,
        "report": False,
        "check_fixity": False,
        "check_stream_fixity": False,
        "embed_stream_fixity": False,
        "output_fixity": False,
        "overwrite_stream_fixity": False
    }

    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)

    for key, value in command_dict.items():
        create_checkbox(layout, command_dict, key, key) 

    window.show()
    app.exec()

    print(command_dict)