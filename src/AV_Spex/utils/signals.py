from PyQt6.QtCore import QObject, pyqtSignal

class ProcessingSignals(QObject):
    started = pyqtSignal(str)
    completed = pyqtSignal(str)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)