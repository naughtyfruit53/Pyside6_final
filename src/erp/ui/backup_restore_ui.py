# src/erp/ui/backup_restore_ui.py
# Full conversion to SQLAlchemy.

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QComboBox
from PySide6.QtCore import Qt
import logging
import os
import re
import threading
from datetime import datetime
from sqlalchemy import text, MetaData
from src.erp.logic.database.session import engine, Session
from src.core.config import get_database_url, get_log_path, get_backup_path
from src.erp.ui.utils.utils_ui import create_scrollable_frame
from src.erp.logic.backup_restore import get_table_names, export_table_data, get_column_info

metadata = MetaData()

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_backup_frame(parent, app):
    """Create the UI frame for database backup functionality."""
    logger.debug("Creating backup frame")
    frame = QFrame(parent)
    frame.setObjectName("backupFrame")
    content = create_scrollable_frame(frame)
    
    layout = QVBoxLayout(content)
    
    title_label = QLabel("Backup Database Tables")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    layout.addWidget(title_label)
    
    desc_label = QLabel("Click the button below to create a backup of the ERP database tables.")
    layout.addWidget(desc_label)
    
    def perform_backup():
        """Perform the database backup operation."""
        session = Session()
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"erp_system_backup_{timestamp}.sql"
            backup_path, _ = QFileDialog.getSaveFileName(
                None, "Save Backup", default_filename, "SQL File (*.sql);;All Files (*.*)"
            )
            if not backup_path:
                return
            
            backup_path = os.path.abspath(backup_path)
            logger.debug(f"Backup save path: {backup_path}")
            
            tables = get_table_names()
            with open(backup_path, 'w', encoding='utf-8') as f:
                for table in tables:
                    insert_statements = export_table_data(session, table)
                    if insert_statements:
                        f.write(f"-- Table: {table}\n")
                        for stmt in insert_statements:
                            f.write(stmt + "\n")
                        f.write("\n")
                
            session.execute(text(
                "INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES (:table_name, :record_id, :action, :user, :timestamp)"
            ), {"table_name": "backup", "record_id": 0, "action": "TABLE_BACKUP", "user": app.current_user['username'] if app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            session.commit()
            
            QMessageBox.information(None, "Success", f"Table data backed up successfully to {backup_path}")
            logger.info(f"Table data backed up to {backup_path}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to backup table data: {e}")
            QMessageBox.critical(None, "Error", f"Failed to backup table data: {e}")
        finally:
            session.close()
    
    backup_button = QPushButton("Create Backup")
    backup_button.clicked.connect(perform_backup)
    layout.addWidget(backup_button)
    
    layout.addStretch()
    content.setLayout(layout)
    frame.setLayout(QVBoxLayout())
    frame.layout().addWidget(content)
    return frame

def create_restore_frame(parent, app):
    """Create the UI frame for database restore functionality."""
    logger.debug("Creating restore frame")
    frame = QFrame(parent)
    frame.setObjectName("restoreFrame")
    content = create_scrollable_frame(frame)
    
    layout = QVBoxLayout(content)
    
    title_label = QLabel("Restore Database Tables")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    layout.addWidget(title_label)
    
    desc_label = QLabel("Select a backup file to restore table data. This will overwrite existing table data.")
    layout.addWidget(desc_label)
    
    def parse_insert_columns(insert_stmt):
        """Parse an INSERT statement to extract table name, columns, and values."""
        match = re.match(r"INSERT\s+INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s*\((.*)\);", insert_stmt, re.IGNORECASE | re.DOTALL)
        if not match:
            logger.error(f"Invalid INSERT statement: {insert_stmt}")
            return None, None, None
        
        table_name = match.group(1)
        columns_str = match.group(2).strip()
        values_str = match.group(3).strip()
        
        columns = []
        current = ""
        in_quotes = False
        for char in columns_str + ',':
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                if current.strip():
                    columns.append(current.strip().strip('"'))
                current = ""
            else:
                current += char
        if current.strip():
            columns.append(current.strip().strip('"'))
        
        return table_name, columns, values_str
    
    def perform_restore():
        """Perform the database restore operation."""
        if QMessageBox.question(None, "Confirm Restore", "Restoring will overwrite existing table data. Are you sure you want to proceed?") != QMessageBox.Yes:
            return
        session = Session()
        try:
            backup_path, _ = QFileDialog.getOpenFileName(
                None, "Select Backup File", "", "SQL File (*.sql);;All Files (*.*)"
            )
            if not backup_path:
                return
            
            backup_path = os.path.abspath(backup_path)
            logger.debug(f"Restore backup path: {backup_path}")
            if not os.path.exists(backup_path):
                QMessageBox.critical(None, "Error", "Selected backup file does not exist!")
                logger.error(f"Backup file {backup_path} does not exist")
                return
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                sql_statements = f.read().splitlines()
            
            tables = get_table_names()
            for table in tables:
                session.execute(text(f"DELETE FROM {table}"))
            
            for stmt in sql_statements:
                if stmt.strip() and not stmt.startswith('--'):
                    table_name, columns, values_str = parse_insert_columns(stmt)
                    if not table_name:
                        continue
                    
                    column_info = get_column_info(session, table_name)
                    if not column_info:
                        logger.warning(f"Table {table_name} not found in database, skipping")
                        continue
                    
                    values = []
                    for col in columns:
                        if col not in column_info:
                            logger.warning(f"Column {col} not found in table {table_name}, skipping statement")
                            values = []
                            break
                        values.append(values_str)
                    
                    if values:
                        session.execute(text(stmt))
            
            session.execute(text(
                "INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES (:table_name, :record_id, :action, :user, :timestamp)"
            ), {"table_name": "restore", "record_id": 0, "action": "TABLE_RESTORE", "user": app.current_user['username'] if app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            session.commit()
            QMessageBox.information(None, "Success", "Table data restored successfully")
            logger.info(f"Table data restored from {backup_path}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to restore table data: {e}")
            QMessageBox.critical(None, "Error", f"Failed to restore table data: {e}")
        finally:
            session.close()
    
    restore_button = QPushButton("Restore from File")
    restore_button.clicked.connect(perform_restore)
    layout.addWidget(restore_button)
    
    layout.addStretch()
    content.setLayout(layout)
    frame.setLayout(QVBoxLayout())
    frame.layout().addWidget(content)
    return frame

def create_auto_backup_frame(parent, app):
    """Create the UI frame for configuring automatic backups."""
    logger.debug("Creating auto backup frame")
    frame = QFrame(parent)
    frame.setObjectName("autoBackupFrame")
    content = create_scrollable_frame(frame)
    
    layout = QVBoxLayout(content)
    
    title_label = QLabel("Configure Automatic Backups")
    title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
    layout.addWidget(title_label)
    
    desc_label = QLabel("Set up automatic backups to run at specified intervals.")
    layout.addWidget(desc_label)
    
    interval_label = QLabel("Backup Interval")
    layout.addWidget(interval_label)
    
    interval_combo = QComboBox()
    interval_combo.addItems(["Daily", "Weekly", "Monthly"])
    layout.addWidget(interval_combo)
    
    def save_auto_backup_config():
        """Save the automatic backup configuration."""
        session = Session()
        try:
            interval = interval_combo.currentText()
            backup_dir = get_backup_path()
            logger.debug(f"Saving auto backup config: interval={interval}, dir={backup_dir}")
            
            session.execute(text("UPDATE settings SET value = :value WHERE key = :key"), {"value": interval, "key": "backup_interval"})
            session.execute(text("UPDATE settings SET value = :value WHERE key = :key"), {"value": backup_dir, "key": "backup_directory"})
            session.execute(text(
                "INSERT INTO audit_log (table_name, record_id, action, user, timestamp) VALUES (:table_name, :record_id, :action, :user, :timestamp)"
            ), {"table_name": "settings", "record_id": 0, "action": "AUTO_BACKUP_CONFIG", "user": app.current_user['username'] if app.current_user else "system_user", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            session.commit()
            
            QMessageBox.information(None, "Success", f"Automatic backup configured: {interval}")
            logger.info(f"Automatic backup configured: interval={interval}, dir={backup_dir}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save auto backup config: {e}")
            QMessageBox.critical(None, "Error", f"Failed to save auto backup config: {e}")
        finally:
            session.close()
    
    save_button = QPushButton("Save Auto Backup Settings")
    save_button.clicked.connect(save_auto_backup_config)
    layout.addWidget(save_button)
    
    layout.addStretch()
    content.setLayout(layout)
    frame.setLayout(QVBoxLayout())
    frame.layout().addWidget(content)
    return frame