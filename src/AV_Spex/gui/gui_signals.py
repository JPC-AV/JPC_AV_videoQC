from PyQt6.QtCore import QObject, pyqtSignal

class ProcessingSignals(QObject):
    started = pyqtSignal(str)  # Signal for when processing starts
    completed = pyqtSignal(str)  # Signal for when processing completes
    error = pyqtSignal(str)  # Signal for when an error occurs
    cancelled = pyqtSignal() # For cancel button
    
    status_update = pyqtSignal(str)  # Signal for general status updates
    progress = pyqtSignal(int, int)  # Signal for numerical progress (current, total)

    file_started = pyqtSignal(str)  # Signal for when processing of a specific file starts
    tool_started = pyqtSignal(str)  # Signal for when a specific tool starts
    tool_completed = pyqtSignal(str)  # Signal for when a tool completes
    step_completed = pyqtSignal(str)  # Signal when a specific step is completed
    
    fixity_progress = pyqtSignal(str)  # For detailed fixity status
    mediaconch_progress = pyqtSignal(str)  # For detailed mediaconch status
    metadata_progress = pyqtSignal(str)  # For detailed metadata status
    output_progress = pyqtSignal(str)  # For detailed output creation status
    