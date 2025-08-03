#!/usr/bin/env python3
"""
Demonstration script showing the clean migration workflow.
This demonstrates the testing process mentioned in the problem statement.

This script:
1. Drops all tables in the dev database
2. Runs `alembic upgrade head`
3. Verifies that organizations, audit_logs, and related tables are created
4. Verifies all constraints are enforced

Usage: python demo_clean_migration_workflow.py
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False

def drop_all_tables():
    """Drop all tables in the dev database"""
    print("🗑️  Dropping all tables in dev database...")
    
    db_path = 'tritiq_erp.db'
    if Path(db_path).exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Drop all tables
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # Skip system table
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            conn.commit()
            conn.close()
            print(f"✅ Dropped {len(tables)} tables from database")
            return True
            
        except Exception as e:
            print(f"❌ Failed to drop tables: {e}")
            return False
    else:
        print("✅ Database file doesn't exist, nothing to drop")
        return True

def verify_tables_created():
    """Verify that key tables are created with correct structure"""
    print("🔍 Verifying tables are created with correct constraints...")
    
    db_path = 'tritiq_erp.db'
    if not Path(db_path).exists():
        print("❌ Database file not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if key tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('organizations', 'audit_logs', 'users', 'companies', 'products');")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['organizations', 'audit_logs', 'users', 'companies', 'products']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ Key tables created: {tables}")
        
        # Quick constraint verification
        cursor.execute("PRAGMA table_info(organizations)")
        org_cols = cursor.fetchall()
        subdomain_found = any(col[1] == 'subdomain' and col[3] == 1 for col in org_cols)  # col[3] is notnull
        
        cursor.execute("PRAGMA table_info(audit_logs)")
        audit_cols = cursor.fetchall()
        org_id_not_null = any(col[1] == 'organization_id' and col[3] == 1 for col in audit_cols)
        
        cursor.execute("PRAGMA table_info(users)")
        user_cols = cursor.fetchall()
        user_org_id_nullable = any(col[1] == 'organization_id' and col[3] == 0 for col in user_cols)
        
        conn.close()
        
        if not subdomain_found:
            print("❌ Organizations.subdomain not found or not NOT NULL")
            return False
        
        if not org_id_not_null:
            print("❌ audit_logs.organization_id not found or not NOT NULL")
            return False
            
        if not user_org_id_nullable:
            print("❌ users.organization_id not found or not nullable")
            return False
        
        print("✅ All constraint verification passed")
        return True
        
    except Exception as e:
        print(f"❌ Table verification failed: {e}")
        return False

def main():
    """Main demonstration workflow"""
    print("🚀 Starting Clean Migration Workflow Demonstration")
    print("This demonstrates the testing process from the problem statement")
    print("=" * 70)
    
    # Check we're in the right directory
    if not Path('alembic.ini').exists():
        print("❌ Error: Must run from fastapi_migration directory")
        return False
    
    success = True
    
    # Step 1: Drop all tables in dev database
    success &= drop_all_tables()
    
    # Step 2: Run alembic upgrade head
    success &= run_command("alembic upgrade head", "Running 'alembic upgrade head'")
    
    # Step 3: Verify tables and constraints
    success &= verify_tables_created()
    
    # Step 4: Run the comprehensive validation
    success &= run_command("python validate_clean_migration.py", "Running comprehensive validation")
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 CLEAN MIGRATION WORKFLOW DEMONSTRATION PASSED!")
        print("✅ Successfully demonstrated:")
        print("   • Drop all tables in dev database")
        print("   • Run 'alembic upgrade head'")
        print("   • Verify organizations, audit_logs, and related tables are created")
        print("   • Verify all constraints are enforced")
        print("\n🏆 The clean migration workflow is working perfectly!")
        return True
    else:
        print("❌ WORKFLOW DEMONSTRATION FAILED!")
        print("Please check the output above for issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)