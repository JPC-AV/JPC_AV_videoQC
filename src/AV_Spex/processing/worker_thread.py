from PyQt6.QtCore import QThread, pyqtSignal

from ..processing.avspex_processor import AVSpexProcessor
from ..utils.log_setup import logger


class ProcessingWorker(QThread):
    """Worker thread for processing directories."""
    
    # Thread-specific signals
    started_processing = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str)
    processing_time = pyqtSignal(str)
    
    def __init__(self, source_directories, signals, parent=None):
        super().__init__(parent)
        self.source_directories = source_directories
        self.signals = signals
        self.processor = AVSpexProcessor(signals=signals)
        
    def run(self):
        """Run the worker thread."""
        try:
            # Emit that we started
            self.started_processing.emit()
            
            # Initialize the processor
            logger.info("Initializing processor...")
            if not self.processor.initialize():
                self.error.emit("Processor initialization failed or was cancelled")
                return
            
            # Process the directories
            logger.info("Processing directories...")
            processing_time = self.processor.process_directories(self.source_directories)
            
            if processing_time:
                self.processing_time.emit(processing_time)
            
            self.finished.emit()
        
        except Exception as e:
            logger.exception("Error in processing worker")
            self.error.emit(f"Processing error: {str(e)}")
            # Commenting this out to keep the window open after an error
            # self.finished.emit()
    
    def cancel(self):
        """Cancel the processing."""
        if self.processor:
            self.processor.cancel()