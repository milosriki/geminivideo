#!/usr/bin/env python3
"""
Apply Prediction Logging Database Migration

This script applies the 005_prediction_logging.sql migration to create
the predictions table and analytical views.

Usage:
    python apply_prediction_migration.py

Or with custom database URL:
    DATABASE_URL=postgresql://... python apply_prediction_migration.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from shared.db.connection import engine, check_db_connection
from shared.db.models import Base
from sqlalchemy import text


async def apply_migration():
    """Apply the prediction logging migration."""
    print("=" * 70)
    print("Prediction Logging Migration - Application")
    print("=" * 70)
    print()

    # Check database connection
    print("Step 1: Checking database connection...")
    try:
        is_connected = await check_db_connection()
        if not is_connected:
            print("✗ Database connection failed!")
            print("Please check your DATABASE_URL environment variable.")
            return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

    print("✓ Database connection successful")
    print()

    # Read migration file
    print("Step 2: Reading migration file...")
    migration_file = Path(__file__).parent.parent.parent / "database_migrations" / "005_prediction_logging.sql"

    if not migration_file.exists():
        print(f"✗ Migration file not found: {migration_file}")
        return False

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    print(f"✓ Loaded migration file: {migration_file}")
    print(f"  File size: {len(migration_sql)} bytes")
    print()

    # Apply migration
    print("Step 3: Applying migration...")
    try:
        async with engine.begin() as conn:
            # Execute the migration SQL
            await conn.execute(text(migration_sql))

        print("✓ Migration applied successfully")
        print()

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

    # Verify tables and views created
    print("Step 4: Verifying migration...")
    try:
        async with engine.connect() as conn:
            # Check table exists
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name = 'predictions'
            """))
            tables = result.fetchall()

            if not tables:
                print("✗ predictions table not found")
                return False

            print("✓ predictions table created")

            # Check views exist
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.views
                WHERE table_name LIKE 'prediction_%'
                ORDER BY table_name
            """))
            views = result.fetchall()

            print(f"✓ {len(views)} analytical views created:")
            for view in views:
                print(f"    - {view[0]}")

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False

    print()
    print("=" * 70)
    print("Migration Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run tests: pytest test_prediction_logger.py -v")
    print("2. Run demo: python test_prediction_logger.py")
    print("3. Review README: PREDICTION_LOGGING_README.md")
    print("4. Start logging predictions in your application")
    print()

    return True


async def show_migration_status():
    """Show current migration status."""
    print("Checking current migration status...")
    print()

    try:
        async with engine.connect() as conn:
            # Check if predictions table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'predictions'
                )
            """))
            exists = result.scalar()

            if exists:
                print("✓ predictions table EXISTS")

                # Get row count
                result = await conn.execute(text("SELECT COUNT(*) FROM predictions"))
                count = result.scalar()
                print(f"  Current records: {count}")

                # Get counts by status
                result = await conn.execute(text("""
                    SELECT
                        COUNT(*) as total,
                        COUNT(actual_ctr) as with_actuals,
                        COUNT(*) - COUNT(actual_ctr) as pending
                    FROM predictions
                """))
                stats = result.fetchone()

                if stats and stats[0] > 0:
                    print(f"  Total predictions: {stats[0]}")
                    print(f"  With actuals: {stats[1]}")
                    print(f"  Pending actuals: {stats[2]}")

            else:
                print("✗ predictions table DOES NOT EXIST")
                print("  Run this script to apply migration")

            print()

    except Exception as e:
        print(f"Error checking status: {e}")
        print()


async def main():
    """Main execution function."""
    # Check if --status flag
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        await show_migration_status()
        return

    # Show status first
    await show_migration_status()

    # Ask for confirmation
    response = input("Apply prediction logging migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        return

    print()

    # Apply migration
    success = await apply_migration()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
