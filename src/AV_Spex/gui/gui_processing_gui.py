from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QAbstractItemView, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette

import os
from ..gui.gui_theme_manager import ThemeManager, ThemeableMixin

class ProcessingWindow(QMainWindow, ThemeableMixin):
    """Window to display processing status and progress."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Status")
        self.resize(500, 200)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label with larger font
        self.status_label = QLabel("Initializing...")
        font = self.status_label.font()
        font.setPointSize(12)
        self.status_label.setFont(font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # This makes it into a "bouncing ball" progress bar
        layout.addWidget(self.progress_bar)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMinimumHeight(100)
        layout.addWidget(self.details_text, 1) # stretch factor of 1

        # Add cancel button
        self.cancel_button = QPushButton("Cancel")
        layout.addWidget(self.cancel_button)

        # Detailed status
        self.detailed_status = QLabel("")
        self.detailed_status.setWordWrap(True)
        layout.addWidget(self.detailed_status)
        
        # Center the window on screen
        self._center_on_screen()
        
        # Setup theme handling (only once)
        self.setup_theme_handling()

    def update_detailed_status(self, message):
        """Update the detailed status message."""
        self.detailed_status.setText(message)
        QApplication.processEvents()

    def update_status(self, message):
        """Update the main status message and append to details text."""
        self.status_label.setText(message)
        self.details_text.append(message)
        # Scroll to bottom
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _center_on_screen(self):
        """Centers the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        window_size = self.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()  # Bring window to front
        self.activateWindow()  # Activate the window

    def closeEvent(self, event):
        # Get a reference to the parent (MainWindow)
        parent = self.parent()
        
        # If parent exists and has a cancel_processing method, call it
        if parent and hasattr(parent, 'cancel_processing'):
            parent.cancel_processing()
        
        # Call the parent class's closeEvent to properly handle window closure
        super().closeEvent(event)

    def on_theme_changed(self, palette):
        """Handle theme changes"""
        # Apply palette to all components
        self.setPalette(palette)
        self.details_text.setPalette(palette)
        self.status_label.setPalette(palette)
        
        # Style the cancel button
        theme_manager = ThemeManager.instance()
        theme_manager.style_buttons(self)
        
        # Force repaint
        self.update()


class DirectoryListWidget(QListWidget):
    """Custom list widget with drag and drop support for directories."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Critical settings for drag and drop
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.main_window = parent

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            
            for url in urls:
                path = url.toLocalFile()
                
                if os.path.isdir(path):
                    # Check for duplicates before adding
                    if path not in [self.item(i).text() for i in range(self.count())]:
                        self.addItem(path)
                        
                        # Update selected_directories if main_window is available
                        if hasattr(self.main_window, 'selected_directories'):
                            if path not in self.main_window.selected_directories:
                                self.main_window.selected_directories.append(path)
            
            event.acceptProposedAction()
