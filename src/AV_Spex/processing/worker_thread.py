from PyQt6.QtCore import QThread, pyqtSignal
from ..processing.avspex_processor import AVSpexProcessor

class ProcessingWorker(QThread):
    """Worker thread for handling AV Spex processing"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    processing_time = pyqtSignal(str)
    started_processing = pyqtSignal(str)  # New signal for process start

    def __init__(self, source_directories, signals):
        super().__init__()
        self.source_directories = source_directories
        self.signals = signals
        self.processor = None

    def run(self):
        try:
            # Emit started signal before beginning processing
            self.started_processing.emit("Initializing processing...")
            
            self.processor = AVSpexProcessor(signals=self.signals)
            
            # Initialize will trigger the progress window updates
            self.processor.initialize()
            
            # Process directories
            formatted_time = self.processor.process_directories(self.source_directories)
            
            # Emit results
            self.processing_time.emit(formatted_time)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))