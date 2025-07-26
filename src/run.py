import sys
from PySide6.QtWidgets import QApplication
from src.core.app import ERPApp
import logging
from src.core.config import get_log_path

logging.basicConfig(
    filename=get_log_path(),
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.debug("Starting TRITIQ ERP application")
    app = QApplication(sys.argv)
    erp_app = ERPApp()
    erp_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()