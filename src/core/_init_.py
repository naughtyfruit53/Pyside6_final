from .app import ERPApp
from .frames import (
    initialize_frames, create_home_frame, create_vouchers_frame,
    create_master_frame, create_dashboard_frame, create_service_frame,
    create_hr_management_frame, create_backup_boss_frame
)
from .navigation import populate_mega_menu

__all__ = [
    'ERPApp',
    'initialize_frames', 'create_home_frame', 'create_vouchers_frame',
    'create_master_frame', 'create_dashboard_frame', 'create_service_frame',
    'create_hr_management_frame', 'create_backup_boss_frame',
    'populate_mega_menu'
]