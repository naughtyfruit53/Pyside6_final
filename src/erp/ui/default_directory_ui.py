# src/erp/ui/default_directory_ui.py
# Converted to use SQLAlchemy in change_directory and browse_directory.

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QDialog, QLineEdit
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
import os
import logging
from datetime import datetime
from sqlalchemy import text
from src.core.config import get_database_url, get_log_path, get_static_path
from src.erp.logic.database.session import engine, Session
from src.erp.logic.default_directory import get_default_directory, save_default_directory

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_default_directory_frame(parent, app):
    """Create the UI frame for setting the default directory."""
    frame = QFrame(parent)
    frame.setObjectName("defaultDirectoryFrame")
    layout = QVBoxLayout(frame)
    
    title_label = QLabel("Set Default Directory")
    title_label.setObjectName("dialogTitleLabel")
    layout.addWidget(title_label)
    
    desc_label = QLabel("Current default directory for storing ERP files:")
    desc_label.setObjectName("fieldLabel")
    layout.addWidget(desc_label)
    
    dir_label = QLabel()
    dir_label.setObjectName("textEntry")
    current_dir = get_default_directory()
    if current_dir and os.path.exists(current_dir):
        formatted_dir = current_dir.replace("\\", "/")  # Preprocess the path
        dir_label.setText(f'<a href="file:///{formatted_dir}" style="color: #0000FF; text-decoration: underline;">{current_dir}</a>')
        dir_label.setOpenExternalLinks(True)
        dir_label.linkActivated.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(current_dir)))
    else:
        dir_label.setText("No default directory set")
    layout.addWidget(dir_label)
    
    def change_directory():
        """Open a directory selection dialog and save the selected directory."""
        session = Session()
        try:
            start_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(start_dir):
                start_dir = os.path.expanduser("~")
                logger.warning(f"Default Documents path not found, falling back to {start_dir}")
            os.chdir(start_dir)  # Set initial directory
            directory = QFileDialog.getExistingDirectory(
                parent=frame,
                caption="Select Default Directory",
                options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            if directory:
                if save_default_directory(directory):
                    formatted_dir = directory.replace("\\", "/")  # Preprocess the path
                    dir_label.setText(f'<a href="file:///{formatted_dir}" style="color: #0000FF; text-decoration: underline;">{directory}</a>')
                    dir_label.setOpenExternalLinks(True)
                    dir_label.linkActivated.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(directory)))
                    QMessageBox.information(frame, "Success", f"Default directory set to: {directory}")
                    logger.info(f"Default directory set to: {directory}")
                    app.default_directory_set = True
                    app.show_frame("home", add_to_history=False)
                else:
                    logger.error(f"Failed to set default directory: {directory}")
                    QMessageBox.critical(frame, "Error", "Failed to set default directory")
            else:
                logger.debug("No directory selected in QFileDialog")
        except Exception as e:
            session.rollback()
            logger.error(f"Error in change_directory: {e}")
            QMessageBox.critical(frame, "Error", f"Failed to open directory dialog: {e}")
        finally:
            session.close()
    
    change_button = QPushButton("Change Default Location")
    change_button.setObjectName("actionButton")
    change_button.clicked.connect(change_directory)
    layout.addWidget(change_button)
    
    layout.addStretch()
    frame.setLayout(layout)
    return frame

class DefaultDirectoryDialog(QDialog):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.setObjectName("defaultDirectoryDialog")
        self.setWindowTitle("Set Default Directory")
        self.setFixedSize(400, 300)
        self.setWindowModality(Qt.ApplicationModal)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel("Set Default Directory")
        title_label.setObjectName("dialogTitleLabel")
        layout.addWidget(title_label)
        
        desc_label = QLabel("Select the default directory for storing ERP files.")
        desc_label.setObjectName("fieldLabel")
        layout.addWidget(desc_label)
        
        browse_button = QPushButton("Browse")
        browse_button.setObjectName("actionButton")
        browse_button.clicked.connect(self.browse_directory)
        layout.addWidget(browse_button)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def browse_directory(self):
        """Open a directory selection dialog and save the selected directory if chosen."""
        session = Session()
        try:
            start_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(start_dir):
                start_dir = os.path.expanduser("~")
                logger.warning(f"Default Documents path not found, falling back to {start_dir}")
            os.chdir(start_dir)  # Set initial directory
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Default Directory",
                "",
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            if directory:
                if save_default_directory(directory):
                    QMessageBox.information(self, "Success", f"Default directory set to: {directory}")
                    logger.info(f"Default directory set to: {directory}")
                    self.app.default_directory_set = True
                    self.accept()
                else:
                    logger.error(f"Failed to set default directory: {directory}")
                    QMessageBox.critical(self, "Error", "Failed to set default directory")
            else:
                logger.debug("No directory selected in QFileDialog")
        except Exception as e:
            session.rollback()
            logger.error(f"Error in browse_directory: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open directory dialog: {e}")
        finally:
            session.close()
    
    def closeEvent(self, event):
        if not self.app.default_directory_set:
            reply = QMessageBox.question(self, "Confirm Close", "Default directory is required. Closing will exit the application. Are you sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
                self.app.exit_app()
            else:
                event.ignore()
        else:
            event.accept()

def show_default_directory_setup(app):
    """Show the default directory setup dialog."""
    return DefaultDirectoryDialog(app)