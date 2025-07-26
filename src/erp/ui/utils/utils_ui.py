# src/ui/utils/utils_ui.py
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget, QComboBox, QMessageBox
from PySide6.QtCore import Qt
import logging
from src.core.config import get_log_path

logging.basicConfig(filename=get_log_path(), level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_scrollable_frame(parent) -> QWidget:
    """Create a scrollable frame with a QScrollArea."""
    try:
        container = QFrame(parent)
        container.setObjectName("scrollableContainer")
        layout = QVBoxLayout(container)
        
        scroll_area = QScrollArea(container)
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        
        scrollable_frame = QWidget()
        scrollable_frame.setObjectName("scrollableFrame")
        
        scroll_area.setWidget(scrollable_frame)
        layout.addWidget(scroll_area)
        container.setLayout(layout)
        
        return scrollable_frame
    except Exception as e:
        logger.error(f"Error creating scrollable frame: {e}")
        raise

def filter_combobox(combo: QComboBox, text: str, starts_with: bool = False):
    """Filter QComboBox values based on user input."""
    try:
        if not hasattr(combo, 'original_values'):
            combo.original_values = [combo.itemText(i) for i in range(combo.count())]
        
        value = text.lower()
        if not value:
            combo.clear()
            combo.addItems(combo.original_values)
            return
        
        filtered = [
            item for item in combo.original_values
            if (value in item.lower() if not starts_with else item.lower().startswith(value))
        ]
        
        combo.clear()
        combo.addItems(filtered)
        combo.setCurrentText(text)
    except Exception as e:
        logger.error(f"Error filtering combobox: {e}")
        QMessageBox.critical(None, "Error", f"Failed to filter combobox: {e}")