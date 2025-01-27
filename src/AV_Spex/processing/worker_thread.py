from PyQt6.QtCore import QThread, pyqtSignal
from ..processing.avspex_processor import AVSpexProcessor

class ProcessingWorker(QThread):
    """Worker thread for handling AV Spex processing"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    processing_time = pyqtSignal(str)
    started_processing = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, source_directories, signals):
        super().__init__()
        self.source_directories = source_directories
        self.signals = signals
        self.processor = None
        self._is_cancelled = False

    def run(self):
        try:
            if self._is_cancelled:
                return
            
            # Emit started signal before beginning processing
            self.started_processing.emit("Initializing processing...")
            
            self.processor = AVSpexProcessor(signals=self.signals)
            
            # Initialize will trigger the progress window updates
            # if initialize() returns false then setup has failed and return will end the thread
            if not self.processor.initialize():
                return
            
            # Process directories
            formatted_time = self.processor.process_directories(self.source_directories)
            
            # Emit results
            # Only emit processing_time if we got a valid string result
            if not self._is_cancelled and isinstance(formatted_time, str):
                self.processing_time.emit(formatted_time)
                self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._is_cancelled = True
        if self.processor:
            self.processor.cancel()