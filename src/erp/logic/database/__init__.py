# src/erp/logic/database/__init__.py

from .schema import INDEXES, create_tables_and_indexes
from .db_utils import initialize_database, reset_database
from .voucher import (
    create_voucher_type,
    get_voucher_types,
    get_default_voucher_type_id_for_module,
    add_voucher_column,
    delete_voucher_column,
    get_voucher_columns,
    create_voucher_instance,
    get_voucher_instances,
    get_next_voucher_number,
    verify_voucher_columns_schema,
    initialize_vouchers
)

# Call initialize_database() here to ensure the database is initialized when the package is imported
initialize_database()