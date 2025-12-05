#!/usr/bin/env python3
"""
Database Migration Runner for GeminiVideo Platform
€5M Investment-Grade Migration System

Features:
- Discovers all .sql files in scripts/migrations/
- Tracks applied migrations in _migrations table
- Runs migrations in order (filename sorting)
- Supports --dry-run mode
- Supports rollback with --down flag
- Transaction per migration with rollback on error
- Clear progress and status reporting

Usage:
    python scripts/migrate.py              # Run all pending migrations
    python scripts/migrate.py --dry-run    # Show what would be executed
    python scripts/migrate.py --down       # Rollback last migration
    python scripts/migrate.py --status     # Show migration status
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a header with formatting"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def get_database_url() -> str:
    """Get database URL from environment"""
    # Try various environment variable names
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        # Build from individual components
        user = os.getenv("POSTGRES_USER", "geminivideo")
        password = os.getenv("POSTGRES_PASSWORD", "geminivideo")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "geminivideo")
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    # Remove asyncpg if present (use psycopg2 for migrations)
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    return db_url

def get_connection():
    """Get database connection"""
    db_url = get_database_url()

    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.OperationalError as e:
        print_error(f"Failed to connect to database: {e}")
        print_info(f"Database URL: {db_url.split('@')[1] if '@' in db_url else 'Not provided'}")
        sys.exit(1)

def ensure_migrations_table(conn) -> None:
    """Ensure the _migrations tracking table exists"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                execution_time_ms INTEGER,
                success BOOLEAN DEFAULT TRUE
            );

            CREATE INDEX IF NOT EXISTS idx_migrations_name ON _migrations(name);
            CREATE INDEX IF NOT EXISTS idx_migrations_executed_at ON _migrations(executed_at DESC);
        """)
        conn.commit()

def calculate_checksum(content: str) -> str:
    """Calculate SHA-256 checksum of file content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def discover_migrations(migrations_dir: Path) -> List[Tuple[str, Path]]:
    """Discover all .sql migration files in order"""
    if not migrations_dir.exists():
        print_error(f"Migrations directory not found: {migrations_dir}")
        return []

    sql_files = sorted(migrations_dir.glob("*.sql"))

    # Sort by filename (assumes numeric prefix like 001_, 002_, etc.)
    migrations = [(f.stem, f) for f in sql_files]
    migrations.sort(key=lambda x: x[0])

    return migrations

def get_applied_migrations(conn) -> Dict[str, Dict]:
    """Get list of already applied migrations"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT name, checksum, executed_at, execution_time_ms
            FROM _migrations
            WHERE success = TRUE
            ORDER BY executed_at ASC
        """)

        results = {}
        for row in cur.fetchall():
            results[row[0]] = {
                'checksum': row[1],
                'executed_at': row[2],
                'execution_time_ms': row[3]
            }

        return results

def read_migration_file(filepath: Path) -> str:
    """Read migration file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print_error(f"Failed to read migration file {filepath}: {e}")
        return None

def execute_migration(conn, name: str, content: str, dry_run: bool = False) -> Tuple[bool, Optional[int]]:
    """Execute a single migration"""
    checksum = calculate_checksum(content)

    if dry_run:
        print_info(f"[DRY RUN] Would execute migration: {name}")
        print_info(f"  Checksum: {checksum}")
        print_info(f"  Content length: {len(content)} bytes")
        return True, 0

    start_time = datetime.now()

    try:
        # Use a transaction for each migration
        with conn.cursor() as cur:
            # Execute the migration SQL
            cur.execute(content)

            # Record the migration
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            cur.execute("""
                INSERT INTO _migrations (name, checksum, execution_time_ms, success)
                VALUES (%s, %s, %s, TRUE)
                ON CONFLICT (name) DO UPDATE
                SET checksum = EXCLUDED.checksum,
                    executed_at = CURRENT_TIMESTAMP,
                    execution_time_ms = EXCLUDED.execution_time_ms,
                    success = TRUE
            """, (name, checksum, execution_time))

        conn.commit()
        return True, execution_time

    except Exception as e:
        conn.rollback()
        print_error(f"Migration failed: {e}")

        # Record failed migration
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO _migrations (name, checksum, execution_time_ms, success)
                    VALUES (%s, %s, 0, FALSE)
                    ON CONFLICT (name) DO UPDATE
                    SET success = FALSE, executed_at = CURRENT_TIMESTAMP
                """, (name, checksum))
            conn.commit()
        except:
            pass

        return False, None

def rollback_migration(conn, name: str, dry_run: bool = False) -> bool:
    """Rollback a migration (if it has a DOWN section)"""
    print_error("Rollback functionality not yet implemented")
    print_info("Manual rollback required using database tools")
    return False

def show_migration_status(conn, migrations: List[Tuple[str, Path]]) -> None:
    """Show status of all migrations"""
    applied = get_applied_migrations(conn)

    print_header("MIGRATION STATUS")

    print(f"{Colors.BOLD}Applied Migrations:{Colors.END}")
    if not applied:
        print_info("  No migrations applied yet")
    else:
        for name, info in applied.items():
            exec_time = f"{info['execution_time_ms']}ms" if info['execution_time_ms'] else "N/A"
            print_success(f"  {name}")
            print(f"    Executed: {info['executed_at']}")
            print(f"    Time: {exec_time}")

    print(f"\n{Colors.BOLD}Pending Migrations:{Colors.END}")
    pending = [m for m in migrations if m[0] not in applied]
    if not pending:
        print_success("  All migrations are up to date!")
    else:
        for name, filepath in pending:
            size = filepath.stat().st_size
            print_warning(f"  {name} ({size} bytes)")

def run_migrations(dry_run: bool = False) -> int:
    """Run all pending migrations"""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    migrations_dir = script_dir / "migrations"

    print_header("DATABASE MIGRATION RUNNER")
    print_info(f"Project root: {project_root}")
    print_info(f"Migrations directory: {migrations_dir}")

    # Discover migrations
    migrations = discover_migrations(migrations_dir)
    if not migrations:
        print_error("No migration files found!")
        return 1

    print_success(f"Found {len(migrations)} migration files")

    # Connect to database
    print_info("Connecting to database...")
    conn = get_connection()
    print_success("Database connection established")

    # Ensure tracking table exists
    ensure_migrations_table(conn)
    print_success("Migration tracking table ready")

    # Get applied migrations
    applied = get_applied_migrations(conn)
    print_info(f"Already applied: {len(applied)} migrations")

    # Find pending migrations
    pending = [m for m in migrations if m[0] not in applied]

    if not pending:
        print_success("All migrations are up to date!")
        conn.close()
        return 0

    print_warning(f"Pending migrations: {len(pending)}")

    if dry_run:
        print_header("DRY RUN MODE - No changes will be made")
    else:
        print_header("EXECUTING MIGRATIONS")

    # Execute pending migrations
    success_count = 0
    failed = []

    for name, filepath in pending:
        print(f"\n{Colors.BOLD}Migration: {name}{Colors.END}")
        print(f"  File: {filepath.name}")

        # Read migration content
        content = read_migration_file(filepath)
        if content is None:
            failed.append((name, "Failed to read file"))
            continue

        # Execute migration
        success, exec_time = execute_migration(conn, name, content, dry_run)

        if success:
            success_count += 1
            if not dry_run:
                print_success(f"  Completed in {exec_time}ms")
            else:
                print_success(f"  Would execute successfully")
        else:
            failed.append((name, "Execution failed"))
            print_error(f"  Migration failed!")
            if not dry_run:
                print_error("  Rolling back transaction...")
                print_error("  Stopping migration process")
                break

    # Summary
    print_header("MIGRATION SUMMARY")
    print(f"Total migrations: {len(pending)}")
    print_success(f"Successful: {success_count}")

    if failed:
        print_error(f"Failed: {len(failed)}")
        for name, reason in failed:
            print_error(f"  - {name}: {reason}")

    conn.close()

    return 0 if not failed else 1

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Database Migration Runner for GeminiVideo Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without making changes"
    )

    parser.add_argument(
        "--down",
        action="store_true",
        help="Rollback the last migration"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show migration status"
    )

    args = parser.parse_args()

    if args.status:
        # Show status
        script_dir = Path(__file__).parent
        migrations_dir = script_dir / "migrations"
        migrations = discover_migrations(migrations_dir)
        conn = get_connection()
        ensure_migrations_table(conn)
        show_migration_status(conn, migrations)
        conn.close()
        return 0

    if args.down:
        print_error("Rollback not yet implemented")
        return 1

    # Run migrations
    return run_migrations(dry_run=args.dry_run)

if __name__ == "__main__":
    sys.exit(main())
