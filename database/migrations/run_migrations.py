#!/usr/bin/env python3
"""
Database Migration Runner for GeminiVideo
Runs SQL migrations in order and tracks their execution
"""

import os
import sys
import re
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
from pathlib import Path
import argparse

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def get_database_url():
    """Get database URL from environment"""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        return database_url

    # Try to construct from individual components
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'password')
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    database = os.getenv('POSTGRES_DB', 'geminivideo')

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_connection():
    """Create database connection"""
    database_url = get_database_url()

    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print_error(f"Failed to connect to database: {e}")
        print_info(f"Database URL: {database_url.split('@')[1] if '@' in database_url else 'invalid'}")
        sys.exit(1)

def ensure_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) UNIQUE NOT NULL,
            executed_at TIMESTAMPTZ DEFAULT NOW(),
            execution_time_ms INTEGER,
            success BOOLEAN DEFAULT TRUE
        )
    """)
    conn.commit()
    cursor.close()

def get_applied_migrations(conn):
    """Get list of already applied migrations"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT migration_name FROM schema_migrations
        WHERE success = TRUE
        ORDER BY id
    """)
    applied = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return applied

def get_migration_files(migrations_dir):
    """Get all migration files in order"""
    files = []
    for file in sorted(migrations_dir.glob('*.sql')):
        if file.name != 'README.md':
            files.append(file)
    return files

def execute_migration(conn, migration_file, dry_run=False):
    """Execute a single migration file"""
    migration_name = migration_file.stem

    print(f"\n{Colors.CYAN}Migration: {Colors.BOLD}{migration_name}{Colors.END}")
    print(f"  File: {migration_file.name}")

    if dry_run:
        print_info("DRY RUN - Would execute this migration")
        return True

    # Read migration file
    try:
        with open(migration_file, 'r') as f:
            sql_content = f.read()
    except Exception as e:
        print_error(f"Failed to read migration file: {e}")
        return False

    # Execute migration
    cursor = conn.cursor()
    start_time = datetime.now()

    try:
        # Execute the SQL
        cursor.execute(sql_content)
        conn.commit()

        # Calculate execution time
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Record migration
        cursor.execute("""
            INSERT INTO schema_migrations (migration_name, execution_time_ms, success)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (migration_name) DO UPDATE
            SET executed_at = NOW(), execution_time_ms = %s, success = TRUE
        """, (migration_name, execution_time, execution_time))
        conn.commit()

        print_success(f"Completed in {execution_time}ms")
        return True

    except Exception as e:
        conn.rollback()
        print_error(f"Migration failed: {e}")

        # Record failed migration
        try:
            cursor.execute("""
                INSERT INTO schema_migrations (migration_name, success)
                VALUES (%s, FALSE)
                ON CONFLICT (migration_name) DO UPDATE
                SET executed_at = NOW(), success = FALSE
            """, (migration_name,))
            conn.commit()
        except:
            pass

        return False
    finally:
        cursor.close()

def show_status(conn, migrations_dir):
    """Show migration status"""
    print_header("MIGRATION STATUS")

    migration_files = get_migration_files(migrations_dir)
    applied_migrations = get_applied_migrations(conn)

    print(f"Total migration files: {len(migration_files)}")
    print(f"Applied migrations: {len(applied_migrations)}")
    print(f"Pending migrations: {len(migration_files) - len(applied_migrations)}\n")

    for migration_file in migration_files:
        migration_name = migration_file.stem
        if migration_name in applied_migrations:
            print_success(f"{migration_name}")
        else:
            print_warning(f"{migration_name} (PENDING)")

    print()

def main():
    """Main migration runner"""
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('--dry-run', action='store_true', help='Preview migrations without executing')
    parser.add_argument('--status', action='store_true', help='Show migration status')
    args = parser.parse_args()

    # Get migrations directory
    script_dir = Path(__file__).parent
    migrations_dir = script_dir

    print_header("DATABASE MIGRATION RUNNER")

    print_info(f"Project root: {script_dir.parent.parent}")
    print_info(f"Migrations directory: {migrations_dir}")

    # Get migration files
    migration_files = get_migration_files(migrations_dir)
    print_success(f"Found {len(migration_files)} migration files")

    # Connect to database
    print_info("Connecting to database...")
    conn = get_connection()
    print_success("Database connection established")

    # Ensure migrations table exists
    ensure_migrations_table(conn)
    print_success("Migration tracking table ready")

    # Show status if requested
    if args.status:
        show_status(conn, migrations_dir)
        conn.close()
        return

    # Get already applied migrations
    applied_migrations = get_applied_migrations(conn)
    print_info(f"Already applied: {len(applied_migrations)} migrations")

    # Get pending migrations
    pending_migrations = [
        f for f in migration_files
        if f.stem not in applied_migrations
    ]

    if not pending_migrations:
        print_success("All migrations are up to date!")
        conn.close()
        return

    print_warning(f"Pending migrations: {len(pending_migrations)}")

    if args.dry_run:
        print_info("DRY RUN MODE - No changes will be made")

    # Execute migrations
    print_header("EXECUTING MIGRATIONS")

    successful = 0
    failed = 0

    for migration_file in pending_migrations:
        if execute_migration(conn, migration_file, dry_run=args.dry_run):
            successful += 1
        else:
            failed += 1
            print_error("Migration failed - stopping execution")
            break

    # Summary
    print_header("MIGRATION SUMMARY")
    print(f"Total migrations: {len(pending_migrations)}")
    print_success(f"Successful: {successful}")
    if failed > 0:
        print_error(f"Failed: {failed}")

    conn.close()

    if failed > 0:
        sys.exit(1)
    else:
        print_success("\n✅ All migrations completed successfully!\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
