from PyQt6.QtWidgets import QApplication, QGroupBox, QPushButton
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QObject, pyqtSignal, Qt

class ThemeManager(QObject):
    """
    Singleton manager for handling theme changes in a PyQt6 application.
    """
    
    # Signal emitted when theme changes
    themeChanged = pyqtSignal(QPalette)
    
    # Singleton instance
    _instance = None
    
    @classmethod
    def instance(cls):
        """Get the ThemeManager singleton instance"""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance
    
    def __new__(cls, *args, **kwargs):
        """Create singleton instance"""
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            # Initialize the QObject part here
            QObject.__init__(cls._instance)
            # Set initialized flag
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the ThemeManager."""
        # Only initialize once for the singleton
        if not self._initialized:
            # Note: We don't call super().__init__() here because it's
            # already called in __new__
            self._initialized = True
            self.app = QApplication.instance()
            
            # Connect to application's palette change signal if app exists
            if self.app:
                self.app.paletteChanged.connect(self._on_palette_changed)
    
    def _on_palette_changed(self, palette):
        """Handle system palette changes and propagate to connected widgets."""
        self.themeChanged.emit(palette)
    
    def style_groupbox(self, group_box, title_position=None):
        """
        Apply consistent styling to a group box based on current theme.
        
        Args:
            group_box: The QGroupBox to style
            title_position: Position of the title ("top left", "top center", etc.)
                            If None, maintains the group box's current title position
        """
        if not isinstance(group_box, QGroupBox) or not self.app:
            return
            
        # Get the current palette
        palette = self.app.palette()
        midlight_color = palette.color(palette.ColorRole.Midlight).name()
        text_color = palette.color(palette.ColorRole.Text).name()
        
        # If title_position is None, attempt to extract the current position from the stylesheet
        if title_position is None:
            current_style = group_box.styleSheet()
            # Look for the subcontrol-position property
            import re
            position_match = re.search(r'subcontrol-position:\s*(top \w+)', current_style)
            if position_match:
                title_position = position_match.group(1)
            else:
                # Default if we can't find it
                title_position = "top left"
        
        # Apply style based on current palette with specified or preserved title position
        group_box.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 14px;
                color: {text_color};
                border: 2px solid gray;
                border-radius: 5px;
                margin-top: 10px;
                background-color: {midlight_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: {title_position};
                padding: 0 10px;
                color: {text_color};
            }}
        """)

    def style_buttons(self, parent_widget):
        """Apply consistent styling to all buttons under a parent widget."""
        if not self.app:
            return
        
        palette = self.app.palette()
        highlight_color = palette.color(palette.ColorRole.Highlight).name()
        highlight_text_color = palette.color(palette.ColorRole.HighlightedText).name()
        button_color = palette.color(palette.ColorRole.Button).name()
        button_text_color = palette.color(palette.ColorRole.ButtonText).name()
        
        button_style = f"""
            QPushButton {{
                font-weight: bold;
                padding: 8px;
                border: 1px solid gray;
                border-radius: 4px;
                background-color: {button_color};
                color: {button_text_color};
            }}
            QPushButton:hover {{
                background-color: {highlight_color};
                color: {highlight_text_color};
            }}
        """
        
        # Apply to all buttons in the widget
        buttons = parent_widget.findChildren(QPushButton)
        for button in buttons:
            button.setStyleSheet(button_style)

    def get_tab_style(self):
        """
        Generate style for tab widgets based on current palette.
        
        Returns:
            str: CSS stylesheet for QTabWidget and QTabBar
        """
        if not self.app:
            return ""
            
        palette = self.app.palette()
        highlight_color = palette.color(palette.ColorRole.Highlight).name()
        highlight_text_color = palette.color(palette.ColorRole.HighlightedText).name()
        dark_color = palette.color(palette.ColorRole.Mid).name()
        
        return f"""
            QTabBar::tab {{
                padding: 8px 12px;
                margin-right: 2px;
                font-size: 14px;
                font-weight: bold;
                background-color: {dark_color};
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected, QTabBar::tab:hover {{
                background-color: {highlight_color};
                color: {highlight_text_color};
            }}
            QTabBar::tab:selected {{
                border-bottom: 2px solid #0066cc;
            }}
                                
            QTabWidget::pane {{
                border: 1px solid lightgray;
                background-color: none;
            }}
        """


class ThemeableMixin:
    """
    Mixin class for widgets that need theme support.
    
    Add this to any QWidget class that needs to respond to theme changes.
    """
    
    def setup_theme_handling(self):
        """Set up theme change handling for this widget."""
        # Skip if already set up
        if hasattr(self, '_theme_handling_setup') and self._theme_handling_setup:
            return
        
        # Get theme manager and connect to signal with direct connection
        self._theme_manager = ThemeManager.instance()
        self._theme_manager.themeChanged.connect(
            self.on_theme_changed, 
            type=Qt.ConnectionType.DirectConnection
        )
        
        # Mark as set up
        self._theme_handling_setup = True

    def on_theme_changed(self, palette):
        """
        Handle theme changes. Override this in subclasses to customize behavior.
        
        Default implementation just applies the palette to this widget.
        """
        # Apply palette to this widget
        if hasattr(self, 'setPalette'):
            self.setPalette(palette)
        
        # Force repaint
        self.update()
        
    def cleanup_theme_handling(self):
        """
        Clean up theme connections before widget destruction.
        Call this in closeEvent or similar.
        """
        if hasattr(self, '_theme_manager') and hasattr(self, '_theme_handling_setup') and self._theme_handling_setup:
            try:
                self._theme_manager.themeChanged.disconnect(self.on_theme_changed)
            except:
                pass  # Already disconnected or error
            self._theme_handling_setup = False