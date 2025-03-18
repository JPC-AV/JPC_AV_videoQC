from PyQt6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
from PyQt6.QtWidgets import QTextEdit, QSizePolicy
from PyQt6.QtCore import Qt, QRegularExpression, QSize
from enum import Enum, auto

class MessageType(Enum):
    """Message types for console output styling"""
    NORMAL = auto()    # Regular output
    SUCCESS = auto()   # Success messages
    ERROR = auto()     # Error messages
    WARNING = auto()   # Warning messages
    INFO = auto()      # Informational messages
    COMMAND = auto()   # Command being executed

class ConsoleTextEdit(QTextEdit):
    """
    A styled QTextEdit that mimics a console/terminal with
    theme-aware styling and support for different message types.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMinimumHeight(300)
        self.setMaximumHeight(900)
        
        # Set default font to monospace for console-like appearance
        font = QFont("Courier New, monospace")
        self.setFont(font)
        
        # Document margin settings for better appearance
        self.document().setDocumentMargin(10)
        
        # Initialize format cache
        self._format_cache = {}

        # Disable word wrapping for horizontal scrolling
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Set horizontal scrollbar policy to always show
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Set a reasonable minimum width but allow horizontal scrolling
        self.setMinimumWidth(300)
        
    def append_message(self, text, msg_type=MessageType.NORMAL):
        """
        Append text with specific styling based on message type.
        
        Args:
            text (str): The message text to append
            msg_type (MessageType): Type of message for styling
        """
        # Get the format for this message type
        text_format = self._get_format_for_type(msg_type)
        
        # Store cursor position and selection
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # If not empty, add a newline
        if not self.toPlainText().isspace() and self.toPlainText():
            cursor.insertText("\n")
        
        # Set the format and insert the text
        cursor.setCharFormat(text_format)
        
        # Format error, warning, and info messages
        prefix = ""
        if msg_type == MessageType.ERROR:
            prefix = "ERROR: "
        elif msg_type == MessageType.WARNING:
            prefix = "WARNING: "
        elif msg_type == MessageType.INFO:
            prefix = "INFO: "
        elif msg_type == MessageType.SUCCESS:
            prefix = "SUCCESS: "
        elif msg_type == MessageType.COMMAND:
            prefix = ""
            
        cursor.insertText(prefix + text)
        
        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
    
    def _get_format_for_type(self, msg_type):
        """
        Get the text format for a specific message type.
        Formats are cached and created on demand.
        
        Args:
            msg_type (MessageType): The message type
            
        Returns:
            QTextCharFormat: Format for the message type
        """
        # Return from cache if already created
        if msg_type in self._format_cache:
            return self._format_cache[msg_type]
        
        # Create a new format
        fmt = QTextCharFormat()
        
        # Base font (monospace)
        font = QFont("Courier New, monospace")
        font.setPointSize(14)
        
        # Apply styling based on message type
        if msg_type == MessageType.NORMAL:
            # Normal style uses default font and palette color
            pass
        elif msg_type == MessageType.ERROR:
            # Error messages are bold and red (uses a distinct shade)
            font.setBold(True)
            fmt.setForeground(QColor(255, 80, 80))
        elif msg_type == MessageType.WARNING:
            # Warning messages are orange
            font.setBold(True)
            fmt.setForeground(QColor(255, 160, 0))
        elif msg_type == MessageType.INFO:
            # Info messages are cyan/blue
            font.setBold(True)
            fmt.setForeground(QColor(40, 170, 255))
        elif msg_type == MessageType.SUCCESS:
            # Success messages are green
            font.setBold(True)
            fmt.setForeground(QColor(0, 200, 0))
        elif msg_type == MessageType.COMMAND:
            # Command messages are bold
            font.setBold(True)
            
        fmt.setFont(font)
        
        # Store in cache and return
        self._format_cache[msg_type] = fmt
        return fmt
    
    def clear_formats(self):
        """Clear the format cache when theme changes"""
        self._format_cache.clear()

    def add_processing_divider(self, text="New Processing Run"):
        """
        Add a visible divider line to indicate a new processing run.
        
        Args:
            text (str): Optional text to display in the divider
        """
        # Store cursor position
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Add a newline if text exists
        if not self.toPlainText().isspace() and self.toPlainText():
            cursor.insertText("\n\n")
        
        # Create a divider format
        divider_format = QTextCharFormat()
        font = QFont("Courier New, monospace")
        font.setPointSize(14)
        font.setBold(True)
        divider_format.setFont(font)
        divider_format.setForeground(QColor(100, 100, 255))  # Blue color for the divider
        
        # Set the format
        cursor.setCharFormat(divider_format)
        
        # Calculate divider width to fill the visible space
        line_char = "═"  # Unicode double line character
        divider_text = f"\n{line_char * 20} {text} {line_char * 20}\n"
        
        # Insert the divider
        cursor.insertText(divider_text)
        
        # Add a newline after the divider
        cursor.setCharFormat(self._get_format_for_type(MessageType.NORMAL))
        cursor.insertText("\n")
        
        # Scroll to the divider
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())