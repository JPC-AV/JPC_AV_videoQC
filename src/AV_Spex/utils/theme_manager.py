from PyQt6.QtWidgets import QApplication, QWidget, QGroupBox, QPushButton
from PyQt6.QtGui import QPalette
from PyQt6.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    # Signal emitted when theme changes
    themeChanged = pyqtSignal(QPalette)
    
    # Make this a class variable rather than an instance variable
    _instance = None
    
    # New: Store slots and connection types directly
    _connected_slots = []
    
    @classmethod
    def instance(cls):
        """Get the ThemeManager singleton instance"""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance
        
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            # Don't initialize here, delay until QApplication exists
        return cls._instance
    
    def _initialize(self):
        """Initialize the theme manager"""
        self.app = QApplication.instance()
        
        # Verify application exists before connecting
        if self.app is None:
            print("Warning: QApplication not available yet, delaying palette connection")
            return False
        
        # Connect to application's palette change signal
        self.app.paletteChanged.connect(self._on_application_palette_changed)
        print("ThemeManager initialized and connected to palette changes")
        return True
    
    def _ensure_initialized(self):
        """Ensure the manager is initialized"""
        if not hasattr(self, 'app') or self.app is None:
            return self._initialize()
        return True
    
    def _on_application_palette_changed(self, palette):
        """Internal handler for system palette changes"""
        print("System palette changed detected in ThemeManager")
        print(f"ThemeManager: About to emit themeChanged signal. Active connections: {len(ThemeManager._connected_slots)}")
        
        # Emit our own signal
        self.themeChanged.emit(palette)
        print("ThemeManager: themeChanged signal emitted")
    
    def connect_to_theme_change(self, slot, connection_type=None):
        """Connect a slot to the theme change signal and track it"""
        from PyQt6.QtCore import Qt
        
        # Ensure we're initialized
        if not self._ensure_initialized():
            print("Warning: Couldn't connect slot because ThemeManager not fully initialized")
            # Still store the slot for later connection
            if (slot, connection_type) not in ThemeManager._connected_slots:
                ThemeManager._connected_slots.append((slot, connection_type))
            return slot
        
        # Try to get information about the slot in a safer way
        try:
            slot_name = slot.__name__ if hasattr(slot, '__name__') else str(slot)
            print(f"ThemeManager: Connecting slot {slot_name}")
        except Exception as e:
            print(f"ThemeManager: Connecting slot (couldn't get details: {e})")
        
        # Store the slot and connection type for reconnection if needed
        if (slot, connection_type) not in ThemeManager._connected_slots:
            ThemeManager._connected_slots.append((slot, connection_type))
        
        # Connect the slot
        if connection_type:
            self.themeChanged.connect(slot, type=connection_type)
        else:
            self.themeChanged.connect(slot)
        
        print(f"ThemeManager: Connection added. Total connections: {len(ThemeManager._connected_slots)}")
        
        # Return the slot for reference
        return slot
    
    def style_groupbox(self, group_box, title_position="top center"):
        """Apply consistent styling to a group box"""
        from PyQt6.QtWidgets import QGroupBox
        
        if not isinstance(group_box, QGroupBox):
            return
            
        # Ensure we're initialized first
        if not self._ensure_initialized():
            return
                
        palette = self.app.palette()
        midlight_color = palette.color(palette.ColorRole.Midlight).name()
        text_color = palette.color(palette.ColorRole.Text).name()
        
        # Clear existing style first
        group_box.setStyleSheet("")
        
        # Then apply new style
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
        
        # Force a style refresh
        if hasattr(group_box, 'style'):
            group_box.style().unpolish(group_box)
            group_box.style().polish(group_box)
            group_box.update()

    def style_buttons(self, parent_widget):
        """
        Apply consistent styling to all buttons under a parent widget
        
        Parameters:
        - parent_widget: The parent widget containing buttons to style
        """
        from PyQt6.QtWidgets import QPushButton
        
        # Ensure we're initialized first
        if not self._ensure_initialized():
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
        
        buttons = parent_widget.findChildren(QPushButton)
        for button in buttons:
            button.setStyleSheet(button_style)
            # Force button to refresh its appearance
            if hasattr(button, 'style'):
                button.style().unpolish(button)
                button.style().polish(button)
                button.update()

    def refresh_widget_style(self, widget):
        """Force a complete style refresh on a widget"""
        if not widget or not hasattr(widget, 'style'):
            return
            
        # Store current stylesheet
        current_style = widget.styleSheet()
        
        # Clear stylesheet temporarily
        widget.setStyleSheet("")
        
        # Force style refresh
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        
        # Reapply original stylesheet
        widget.setStyleSheet(current_style)
        
        # Force update
        widget.update()

    def refresh_all_styles(self, parent_widget):
        """Recursively refresh styles for all widgets"""
        from PyQt6.QtWidgets import QWidget
        
        # Begin updating the widget - prevents multiple repaints
        if hasattr(parent_widget, 'setUpdatesEnabled'):
            parent_widget.setUpdatesEnabled(False)
        
        try:
            self.refresh_widget_style(parent_widget)
            
            # Process all children
            for child in parent_widget.children():
                if isinstance(child, QWidget):
                    # Recursively refresh child styles, but don't enable updates yet
                    if hasattr(child, 'setUpdatesEnabled'):
                        child.setUpdatesEnabled(False)
                    self.refresh_all_styles(child)
        finally:
            # Re-enable updates and force a single repaint
            if hasattr(parent_widget, 'setUpdatesEnabled'):
                parent_widget.setUpdatesEnabled(True)
                parent_widget.update()
    
    def ensure_connections(self):
        """Ensure all stored connections are active"""
        # Ensure we're initialized first
        if not self._ensure_initialized():
            print("Warning: Can't ensure connections because ThemeManager not fully initialized")
            return
            
        print(f"ThemeManager: Ensuring {len(ThemeManager._connected_slots)} connections are active")
        
        # Temporarily disconnect all slots
        try:
            self.themeChanged.disconnect()
            print("ThemeManager: Disconnected all slots to rebuild connections")
        except Exception as e:
            print(f"ThemeManager: Error disconnecting slots: {e}")
        
        # Reconnect all stored slots
        for slot, connection_type in ThemeManager._connected_slots:
            if connection_type:
                self.themeChanged.connect(slot, type=connection_type)
            else:
                self.themeChanged.connect(slot)
        
        print(f"ThemeManager: Reconnected {len(ThemeManager._connected_slots)} slots")

    def get_tab_style(self):
        """Generate style for tab widgets based on current palette"""
        # Ensure we're initialized first
        if not self._ensure_initialized():
            # Return a minimal style if not initialized
            return """
                QTabBar::tab {
                    padding: 8px 12px;
                    margin-right: 2px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """

        # Get the application palette
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
        # Check if already set up
        if hasattr(self, '_theme_handling_setup') and self._theme_handling_setup:
            print(f"{self.__class__.__name__}: Theme handling already set up, skipping")
            return
        
        # Check if QApplication exists
        app = QApplication.instance()
        if app is None:
            print(f"{self.__class__.__name__}: QApplication not available, skipping theme setup")
            return
                
        print(f"{self.__class__.__name__}: Setting up theme handling")
        
        # Get singleton instance of ThemeManager
        self._theme_manager = ThemeManager.instance()
        
        # Import Qt.ConnectionType for direct connection
        from PyQt6.QtCore import Qt
        
        # Preserve the original method for debugging
        if not hasattr(self, '_original_on_theme_changed'):
            self._original_on_theme_changed = self.on_theme_changed
            
            # Create a debug wrapper for the method
            def debug_on_theme_changed(palette):
                print(f"on_theme_changed called for {self.__class__.__name__}")
                try:
                    return self._original_on_theme_changed(palette)
                except Exception as e:
                    print(f"Error in {self.__class__.__name__}.on_theme_changed: {e}")
                    # Fallback implementation
                    if hasattr(self, 'setPalette'):
                        self.setPalette(palette)
                    self.update()
            
            self.on_theme_changed = debug_on_theme_changed
        
        # Connect to the theme changed signal using the tracking method
        self._theme_connection = self._theme_manager.connect_to_theme_change(
            self.on_theme_changed,
            connection_type=Qt.ConnectionType.DirectConnection
        )
        
        # Mark as set up
        self._theme_handling_setup = True

    def on_theme_changed(self, palette):
        """Handle theme changes - base implementation"""
        print(f"ThemeableMixin.on_theme_changed called for {self.__class__.__name__}")
        
        # Apply palette to this widget
        if hasattr(self, 'setPalette'):
            self.setPalette(palette)
        
        # Force repaint
        self.update()
        
    def cleanup_theme_handling(self):
        """Clean up theme connections - call this in your closeEvent or destructor"""
        if hasattr(self, '_theme_manager') and hasattr(self, '_theme_connection'):
            print(f"{self.__class__.__name__}: Cleaning up theme connection")
            try:
                self._theme_manager.themeChanged.disconnect(self.on_theme_changed)
                print(f"{self.__class__.__name__}: Successfully disconnected theme signal")
            except Exception as e:
                print(f"{self.__class__.__name__}: Error disconnecting theme signal: {e}")
            self._theme_connection = None
