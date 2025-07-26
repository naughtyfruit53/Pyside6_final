# src/logic/config.py
import os

def get_project_root():
    """Get the root directory of the project (tritiq_erp_2)."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Removed get_db_path() as we no longer use a file path for PostgreSQL.
# Added get_database_url() to load from environment variable.
def get_database_url():
    """Get the PostgreSQL database URL from environment variable."""
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise ValueError("DATABASE_URL environment variable not set. Set it to your PostgreSQL connection string.")
    return url

def get_log_path():
    """Get the path to the log file, creating the logs directory if it doesn't exist."""
    logs_dir = os.path.join(get_project_root(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return os.path.join(logs_dir, 'erp_app.log')

def get_static_path(filename):
    """Get the path to a static asset, pointing to src/static."""
    static_dir = os.path.join(get_project_root(), 'src', 'static')
    os.makedirs(static_dir, exist_ok=True)
    return os.path.join(static_dir, filename)

def get_backup_path():
    """Get the path to the backups directory, creating it if it doesn't exist."""
    backups_dir = os.path.join(get_project_root(), 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    return backups_dir