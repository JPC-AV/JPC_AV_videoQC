from PyQt6.QtWidgets import QApplication, QWidget, QGroupBox, QPushButton
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    """
    Singleton class to manage theme changes across the application.
    Acts as a central point for all theme-related functionality.
    """
    # Signal emitted when theme changes
    themeChanged = pyqtSignal(QPalette)
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the theme manager"""
        self.app = QApplication.instance()
        # Connect to application's palette change signal
        self.app.paletteChanged.connect(self._on_application_palette_changed)
    
    def _on_application_palette_changed(self, palette):
        """Internal handler for system palette changes"""
        # Emit our own signal
        self.themeChanged.emit(palette)
    
    def apply_theme_to_widget(self, widget):
        """Apply current theme to a widget and all its children"""
        self._apply_theme_recursively(widget, self.app.palette())
    
    def _apply_theme_recursively(self, parent_widget, palette):
        """Recursively apply theme to a widget and all its children"""
        # Apply palette to the parent widget
        if hasattr(parent_widget, 'setPalette'):
            parent_widget.setPalette(palette)
        
        # Refresh widget's style
        if hasattr(parent_widget, 'style') and hasattr(parent_widget.style(), 'unpolish'):
            parent_widget.style().unpolish(parent_widget)
            parent_widget.style().polish(parent_widget)
            
        # Apply theme to all children
        for child in parent_widget.children():
            if isinstance(child, QWidget):
                self._apply_theme_recursively(child, palette)
        
        # Force repaint
        if hasattr(parent_widget, 'update'):
            parent_widget.update()
    
    def style_groupbox(self, group_box, title_position="top center"):
        """
        Apply consistent styling to a group box
        
        Parameters:
        - group_box: The QGroupBox to update
        - title_position: The position of the title (e.g., "top left", "top center")
        """
        if not isinstance(group_box, QGroupBox):
            return
            
        palette = self.app.palette()
        midlight_color = palette.color(palette.ColorRole.Midlight).name()
        text_color = palette.color(palette.ColorRole.Text).name()
        
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
        """
        Apply consistent styling to all buttons under a parent widget
        
        Parameters:
        - parent_widget: The parent widget containing buttons to style
        """
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
        
        buttons = parent_widget.findChildren(QPushButton)
        for button in buttons:
            button.setStyleSheet(button_style)
            # Force button to refresh its appearance
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
    
    def get_tab_style(self):
        """Generate style for tab widgets based on current palette"""
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
                                
            /* Reset the tab widget's background to default */
            QTabWidget::pane {{
                border: 1px solid lightgray;
                background-color: none;
            }}
        """


# Create a mixin class for widgets that need theme support
class ThemeableMixin:
    """
    Mixin class for widgets that need theme support.
    Provides common theme-related functionality.
    """
    
    def setup_theme_handling(self):
        """Setup theme handling for this widget"""
        self.theme_manager = ThemeManager()
        self.theme_manager.themeChanged.connect(self.on_theme_changed)
    
    def on_theme_changed(self, palette):
        """
        Handle theme changes.
        This method should be overridden by subclasses that need
        custom theme handling.
        """
        self.setPalette(palette)
        self.theme_manager.apply_theme_to_widget(self)
        self.update()
