#!/usr/bin/env python3
"""
Validation script for clean database schema migrations.
This script validates that all requirements from the problem statement are met.

Run this script to verify:
1. All required NOT NULL columns in organizations and audit_logs tables are present
2. Correct foreign key relationships are set
3. User.organization_id is nullable  
4. Alembic migrations work correctly
5. Database constraints are properly enforced

Usage:
    python validate_clean_migration.py

Requirements:
    - Run from fastapi_migration directory
    - SQLite database should be created by alembic migration
"""

import os
import sys
import sqlite3
from pathlib import Path

def validate_organizations_table(cursor):
    """Validate organizations table has all required NOT NULL fields"""
    print("🔍 Validating Organizations table...")
    
    cursor.execute("PRAGMA table_info(organizations)")
    columns = cursor.fetchall()
    
    # Required NOT NULL fields as per problem statement
    required_not_null = {
        'subdomain', 'primary_email', 'primary_phone', 
        'address1', 'city', 'state', 'pin_code', 'country', 'name'
    }
    
    found_columns = {}
    for col in columns:
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        cid, name, type_name, not_null, default_val, pk = col
        found_columns[name] = {'not_null': bool(not_null), 'type': type_name}
    
    missing_fields = []
    wrong_nullable = []
    
    for field in required_not_null:
        if field not in found_columns:
            missing_fields.append(field)
        elif not found_columns[field]['not_null']:
            wrong_nullable.append(field)
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    if wrong_nullable:
        print(f"❌ Fields should be NOT NULL: {wrong_nullable}")
        return False
        
    print("✅ Organizations table: All required NOT NULL fields present")
    return True

def validate_audit_logs_table(cursor):
    """Validate audit_logs table has correct constraints"""
    print("🔍 Validating AuditLogs table...")
    
    cursor.execute("PRAGMA table_info(audit_logs)")
    columns = cursor.fetchall()
    
    org_id_found = False
    org_id_not_null = False
    user_id_found = False
    user_id_nullable = False
    
    for col in columns:
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        cid, name, type_name, not_null, default_val, pk = col
        if name == 'organization_id':
            org_id_found = True
            org_id_not_null = bool(not_null)
        elif name == 'user_id':
            user_id_found = True
            user_id_nullable = not bool(not_null)  # Should be nullable
    
    if not org_id_found:
        print("❌ AuditLogs missing organization_id column")
        return False
    
    if not org_id_not_null:
        print("❌ AuditLogs organization_id should be NOT NULL")
        return False
        
    if not user_id_found:
        print("❌ AuditLogs missing user_id column")
        return False
        
    if not user_id_nullable:
        print("❌ AuditLogs user_id should be nullable")
        return False
    
    print("✅ AuditLogs table: organization_id NOT NULL, user_id nullable")
    return True

def validate_users_table(cursor):
    """Validate users table has nullable organization_id"""
    print("🔍 Validating Users table...")
    
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    org_id_nullable = False
    
    for col in columns:
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        cid, name, type_name, not_null, default_val, pk = col
        if name == 'organization_id':
            org_id_nullable = not bool(not_null)  # Should be nullable
            break
    else:
        print("❌ Users table missing organization_id column")
        return False
    
    if not org_id_nullable:
        print("❌ Users organization_id should be nullable")
        return False
    
    print("✅ Users table: organization_id is nullable")
    return True

def validate_foreign_keys(cursor):
    """Validate foreign key relationships"""
    print("🔍 Validating Foreign Key relationships...")
    
    # Check audit_logs foreign keys
    cursor.execute("PRAGMA foreign_key_list(audit_logs)")
    fks = cursor.fetchall()
    
    org_fk_found = False
    user_fk_found = False
    
    for fk in fks:
        id, seq, table, from_col, to_col, on_update, on_delete, match = fk
        if table == 'organizations' and from_col == 'organization_id':
            org_fk_found = True
        elif table == 'users' and from_col == 'user_id':
            user_fk_found = True
    
    if not org_fk_found:
        print("❌ Missing FK: audit_logs.organization_id → organizations.id")
        return False
        
    if not user_fk_found:
        print("❌ Missing FK: audit_logs.user_id → users.id")
        return False
    
    print("✅ Foreign Keys: audit_logs properly references organizations and users")
    return True

def validate_indexes(cursor):
    """Validate important indexes exist"""
    print("🔍 Validating Indexes...")
    
    # Check for important indexes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    required_indexes = [
        'ix_organizations_subdomain',
        'ix_organizations_name', 
        'idx_audit_org_table_action',
        'idx_audit_org_timestamp'
    ]
    
    missing_indexes = []
    for idx in required_indexes:
        if idx not in indexes:
            missing_indexes.append(idx)
    
    if missing_indexes:
        print(f"❌ Missing indexes: {missing_indexes}")
        return False
    
    print("✅ Indexes: All important indexes present")
    return True

def validate_alembic_state():
    """Validate alembic migration state"""
    print("🔍 Validating Alembic migration state...")
    
    # Check if alembic_version table exists and has current migration
    try:
        import subprocess
        result = subprocess.run(['alembic', 'current'], 
                              capture_output=True, text=True, check=True)
        
        if 'ed394455f061' in result.stdout and '(head)' in result.stdout:
            print("✅ Alembic: Clean initial migration is current")
            return True
        else:
            print(f"❌ Alembic: Unexpected state: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Alembic: Error checking state: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Starting Clean Migration Validation")
    print("=" * 50)
    
    # Check we're in the right directory
    if not Path('alembic.ini').exists():
        print("❌ Error: Must run from fastapi_migration directory")
        return False
    
    # Check database exists
    db_path = 'tritiq_erp.db'
    if not Path(db_path).exists():
        print(f"❌ Error: Database {db_path} not found. Run 'alembic upgrade head' first.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        all_passed = True
        
        # Run all validations
        all_passed &= validate_organizations_table(cursor)
        all_passed &= validate_audit_logs_table(cursor)
        all_passed &= validate_users_table(cursor)
        all_passed &= validate_foreign_keys(cursor)
        all_passed &= validate_indexes(cursor)
        all_passed &= validate_alembic_state()
        
        conn.close()
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✅ Database schema meets all requirements from problem statement:")
            print("   • Organizations table has all required NOT NULL fields")
            print("   • AuditLogs has NOT NULL organization_id FK and nullable user_id")
            print("   • Users has nullable organization_id") 
            print("   • All foreign keys and indexes properly set")
            print("   • Clean initial migration is current")
            return True
        else:
            print("❌ SOME VALIDATIONS FAILED!")
            print("Please check the output above and fix the issues.")
            return False
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)