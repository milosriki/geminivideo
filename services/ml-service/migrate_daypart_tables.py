"""
Database Migration Script for Day-Part Optimization Tables
Agent 8 - Day-Part Optimizer

Creates the necessary database tables for the day-part optimization system:
- daypart_performance: Historical performance data by time buckets
- daypart_patterns: Detected patterns
- daypart_schedules: Generated schedules
- daypart_analyses: Analysis results

Usage:
    python migrate_daypart_tables.py
"""
import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from daypart.models import (
    Base,
    DayPartPerformance,
    DayPartPattern,
    DayPartSchedule,
    DayPartAnalysis
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)


def check_table_exists(engine, table_name):
    """Check if a table already exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def create_daypart_tables():
    """Create all day-part optimization tables."""
    print("="*60)
    print("Day-Part Optimization - Database Migration")
    print("="*60)

    print(f"\n📊 Connecting to database...")
    print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

    try:
        engine = create_engine(DATABASE_URL)

        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful")

        # Check existing tables
        print(f"\n🔍 Checking existing tables...")
        tables_to_create = [
            ('daypart_performance', DayPartPerformance),
            ('daypart_patterns', DayPartPattern),
            ('daypart_schedules', DayPartSchedule),
            ('daypart_analyses', DayPartAnalysis)
        ]

        existing_tables = []
        new_tables = []

        for table_name, model in tables_to_create:
            if check_table_exists(engine, table_name):
                existing_tables.append(table_name)
                print(f"   ⚠️  Table '{table_name}' already exists")
            else:
                new_tables.append(table_name)
                print(f"   ✨ Table '{table_name}' will be created")

        if not new_tables:
            print(f"\n✅ All tables already exist. No migration needed.")
            return

        # Create new tables
        print(f"\n📝 Creating {len(new_tables)} new tables...")

        # Create only the tables that don't exist
        Base.metadata.create_all(
            engine,
            tables=[
                model.__table__
                for table_name, model in tables_to_create
                if table_name in new_tables
            ]
        )

        print(f"✅ Tables created successfully!")

        # Verify creation
        print(f"\n🔍 Verifying table creation...")
        for table_name in new_tables:
            if check_table_exists(engine, table_name):
                print(f"   ✅ {table_name}")
            else:
                print(f"   ❌ {table_name} - FAILED TO CREATE")

        # Show table details
        print(f"\n📋 Table Details:")
        inspector = inspect(engine)

        for table_name in new_tables:
            if check_table_exists(engine, table_name):
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)

                print(f"\n   {table_name}:")
                print(f"      Columns: {len(columns)}")
                for col in columns[:5]:  # Show first 5 columns
                    print(f"         - {col['name']}: {col['type']}")
                if len(columns) > 5:
                    print(f"         ... and {len(columns) - 5} more")

                print(f"      Indexes: {len(indexes)}")
                for idx in indexes:
                    print(f"         - {idx['name']}: {idx['column_names']}")

        print(f"\n" + "="*60)
        print("Migration Complete!")
        print("="*60)

        # Next steps
        print(f"\n📚 Next Steps:")
        print(f"   1. Start collecting performance data:")
        print(f"      python daypart_usage_example.py  # Run example 6")
        print(f"   ")
        print(f"   2. Run campaign analysis:")
        print(f"      python daypart_usage_example.py  # Run example 1")
        print(f"   ")
        print(f"   3. Generate optimized schedules:")
        print(f"      python daypart_usage_example.py  # Run example 2")
        print(f"   ")
        print(f"   4. API endpoints available at:")
        print(f"      POST /daypart/analyze")
        print(f"      GET  /daypart/recommend/{{campaign_id}}")
        print(f"      POST /daypart/schedule")
        print(f"      GET  /daypart/schedule/{{schedule_id}}")
        print(f"      GET  /daypart/health")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def rollback_daypart_tables():
    """Drop all day-part optimization tables."""
    print("="*60)
    print("Day-Part Optimization - Rollback Migration")
    print("="*60)

    confirm = input("\n⚠️  This will DELETE all day-part tables and data. Continue? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Rollback cancelled.")
        return

    print(f"\n📊 Connecting to database...")

    try:
        engine = create_engine(DATABASE_URL)

        tables_to_drop = [
            'daypart_analyses',
            'daypart_schedules',
            'daypart_patterns',
            'daypart_performance'
        ]

        print(f"\n🗑️  Dropping tables...")
        for table_name in tables_to_drop:
            if check_table_exists(engine, table_name):
                with engine.connect() as conn:
                    conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    conn.commit()
                print(f"   ✅ Dropped {table_name}")
            else:
                print(f"   ⏭️  {table_name} doesn't exist")

        print(f"\n✅ Rollback complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def show_table_stats():
    """Show statistics for day-part tables."""
    print("="*60)
    print("Day-Part Optimization - Table Statistics")
    print("="*60)

    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()

        tables = [
            ('daypart_performance', DayPartPerformance),
            ('daypart_patterns', DayPartPattern),
            ('daypart_schedules', DayPartSchedule),
            ('daypart_analyses', DayPartAnalysis)
        ]

        print(f"\n📊 Table Statistics:\n")

        for table_name, model in tables:
            if check_table_exists(engine, table_name):
                count = db.query(model).count()
                print(f"   {table_name:25s}: {count:6d} rows")
            else:
                print(f"   {table_name:25s}: (not exists)")

        db.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Main migration script."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "rollback":
            rollback_daypart_tables()
        elif command == "stats":
            show_table_stats()
        elif command == "help":
            print("Day-Part Optimization - Database Migration")
            print("\nCommands:")
            print("  python migrate_daypart_tables.py          # Create tables")
            print("  python migrate_daypart_tables.py rollback # Drop tables")
            print("  python migrate_daypart_tables.py stats    # Show statistics")
            print("  python migrate_daypart_tables.py help     # Show this help")
        else:
            print(f"Unknown command: {command}")
            print("Run 'python migrate_daypart_tables.py help' for usage")
    else:
        create_daypart_tables()


if __name__ == "__main__":
    main()
