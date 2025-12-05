#!/usr/bin/env python3
"""
Database Health Checker for GeminiVideo Platform
€5M Investment-Grade Health Monitoring

Performs comprehensive database health checks:
- Database connectivity validation
- Table existence verification
- pgvector extension check
- Row count reporting
- Index usage statistics
- Performance metrics
- Migration status
- Data integrity checks

Usage:
    python scripts/db-health.py              # Run all health checks
    python scripts/db-health.py --quick      # Quick check (connectivity + tables)
    python scripts/db-health.py --detailed   # Detailed report with statistics
    python scripts/db-health.py --json       # Output as JSON
"""

import os
import sys
import argparse
import psycopg2
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

# ANSI colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def get_database_url() -> str:
    """Get database URL from environment"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        user = os.getenv("POSTGRES_USER", "geminivideo")
        password = os.getenv("POSTGRES_PASSWORD", "geminivideo")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "geminivideo")
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return db_url.replace("postgresql+asyncpg://", "postgresql://")

def check_connectivity() -> Tuple[bool, Optional[psycopg2.extensions.connection], str]:
    """Check database connectivity"""
    try:
        conn = psycopg2.connect(get_database_url())
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
        return True, conn, version
    except Exception as e:
        return False, None, str(e)

def check_pgvector(conn) -> Tuple[bool, Optional[str]]:
    """Check if pgvector extension is installed"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT extversion
                FROM pg_extension
                WHERE extname = 'vector'
            """)
            result = cur.fetchone()
            if result:
                return True, result[0]
            else:
                return False, None
    except Exception as e:
        return False, str(e)

def check_tables(conn) -> Dict[str, bool]:
    """Check if all required tables exist"""
    required_tables = [
        # Core tables
        "users", "campaigns", "blueprints", "videos", "ads", "clips", "emotions",
        "performance_metrics", "daily_analytics", "jobs", "render_jobs", "audit_logs",
        # ML and AI tables
        "predictions",
        # Vector tables
        "video_embeddings", "script_embeddings", "ad_creative_embeddings", "winning_ad_patterns",
        # Semantic cache
        "semantic_cache_entries",
        # Creative DNA
        "creative_formulas", "creative_dna_extractions", "dna_applications",
        # Cross-account learning
        "cross_account_patterns", "pattern_contributions", "pattern_applications", "industry_benchmarks",
        # Compound learning
        "learning_cycles", "learning_metrics", "feedback_loops", "feedback_events",
        "compound_learnings", "improvement_trajectory",
        # Migration tracking
        "_migrations"
    ]

    results = {}
    with conn.cursor() as cur:
        for table in required_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table,))
            results[table] = cur.fetchone()[0]

    return results

def get_table_counts(conn, tables: List[str]) -> Dict[str, int]:
    """Get row counts for tables"""
    counts = {}
    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
            except Exception as e:
                counts[table] = -1  # Error
    return counts

def get_migration_status(conn) -> Dict:
    """Get migration status"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as total,
                       COUNT(*) FILTER (WHERE success = TRUE) as successful,
                       COUNT(*) FILTER (WHERE success = FALSE) as failed,
                       MAX(executed_at) as last_migration
                FROM _migrations
            """)
            result = cur.fetchone()
            return {
                "total": result[0],
                "successful": result[1],
                "failed": result[2],
                "last_migration": result[3]
            }
    except:
        return {"total": 0, "successful": 0, "failed": 0, "last_migration": None}

def get_index_usage(conn) -> List[Dict]:
    """Get index usage statistics"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    pg_size_pretty(pg_relation_size(indexrelid)) as size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                ORDER BY idx_scan DESC
                LIMIT 10
            """)
            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "scans": row[3],
                    "tuples_read": row[4],
                    "size": row[5]
                }
                for row in cur.fetchall()
            ]
    except:
        return []

def get_database_size(conn) -> str:
    """Get total database size"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            return cur.fetchone()[0]
    except:
        return "Unknown"

def check_data_integrity(conn) -> Dict[str, bool]:
    """Perform basic data integrity checks"""
    checks = {}

    try:
        with conn.cursor() as cur:
            # Check for campaigns without users
            cur.execute("""
                SELECT COUNT(*) FROM campaigns c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE u.id IS NULL
            """)
            orphaned_campaigns = cur.fetchone()[0]
            checks["campaigns_have_users"] = orphaned_campaigns == 0

            # Check for videos without campaigns
            cur.execute("""
                SELECT COUNT(*) FROM videos v
                LEFT JOIN campaigns c ON v.campaign_id = c.id
                WHERE c.id IS NULL AND v.campaign_id IS NOT NULL
            """)
            orphaned_videos = cur.fetchone()[0]
            checks["videos_have_campaigns"] = orphaned_videos == 0

            # Check for predictions with actuals
            cur.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE actual_ctr IS NOT NULL) as with_actuals
                FROM predictions
            """)
            result = cur.fetchone()
            if result[0] > 0:
                checks["predictions_have_actuals"] = result[1] > 0
            else:
                checks["predictions_have_actuals"] = True  # No predictions yet

    except Exception as e:
        checks["error"] = str(e)

    return checks

def get_performance_summary(conn) -> Dict:
    """Get performance summary statistics"""
    try:
        with conn.cursor() as cur:
            # Campaign performance
            cur.execute("""
                SELECT
                    COUNT(*) as total_campaigns,
                    AVG(roas) as avg_roas,
                    SUM(spend) as total_spend,
                    SUM(revenue) as total_revenue
                FROM campaigns
                WHERE status = 'active'
            """)
            result = cur.fetchone()
            campaign_stats = {
                "total_campaigns": result[0],
                "avg_roas": float(result[1]) if result[1] else 0,
                "total_spend": float(result[2]) if result[2] else 0,
                "total_revenue": float(result[3]) if result[3] else 0
            }

            # Prediction accuracy
            cur.execute("""
                SELECT
                    COUNT(*) as total_predictions,
                    COUNT(*) FILTER (WHERE actual_ctr IS NOT NULL) as with_actuals,
                    AVG(ABS(predicted_ctr - actual_ctr)) as avg_ctr_error,
                    AVG(ABS(predicted_roas - actual_roas)) as avg_roas_error
                FROM predictions
                WHERE actual_ctr IS NOT NULL
            """)
            result = cur.fetchone()
            prediction_stats = {
                "total_predictions": result[0],
                "with_actuals": result[1],
                "avg_ctr_error": float(result[2]) if result[2] else 0,
                "avg_roas_error": float(result[3]) if result[3] else 0
            }

            return {
                "campaigns": campaign_stats,
                "predictions": prediction_stats
            }
    except:
        return {}

def run_health_check(quick: bool = False, detailed: bool = False) -> Dict:
    """Run comprehensive health check"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {},
        "status": "healthy"
    }

    print_header("DATABASE HEALTH CHECK")

    # 1. Connectivity Check
    print(f"{Colors.BOLD}1. Database Connectivity{Colors.END}")
    connected, conn, info = check_connectivity()

    if connected:
        print_success(f"Connected to database")
        print_info(f"  Version: {info.split(',')[0]}")
        results["checks"]["connectivity"] = {"status": "pass", "info": info}
    else:
        print_error(f"Failed to connect: {info}")
        results["checks"]["connectivity"] = {"status": "fail", "error": info}
        results["status"] = "critical"
        return results

    # 2. pgvector Extension Check
    print(f"\n{Colors.BOLD}2. pgvector Extension{Colors.END}")
    has_pgvector, pgvector_version = check_pgvector(conn)

    if has_pgvector:
        print_success(f"pgvector extension installed (version {pgvector_version})")
        results["checks"]["pgvector"] = {"status": "pass", "version": pgvector_version}
    else:
        print_error("pgvector extension not installed")
        results["checks"]["pgvector"] = {"status": "fail"}
        results["status"] = "degraded"

    # 3. Table Existence Check
    print(f"\n{Colors.BOLD}3. Required Tables{Colors.END}")
    table_status = check_tables(conn)
    missing_tables = [t for t, exists in table_status.items() if not exists]

    if not missing_tables:
        print_success(f"All {len(table_status)} required tables exist")
        results["checks"]["tables"] = {"status": "pass", "count": len(table_status)}
    else:
        print_error(f"Missing {len(missing_tables)} tables:")
        for table in missing_tables:
            print(f"  - {table}")
        results["checks"]["tables"] = {"status": "fail", "missing": missing_tables}
        results["status"] = "degraded"

    if quick:
        conn.close()
        return results

    # 4. Migration Status
    print(f"\n{Colors.BOLD}4. Migration Status{Colors.END}")
    migration_status = get_migration_status(conn)

    if migration_status["total"] > 0:
        print_success(f"Applied {migration_status['successful']} migrations successfully")
        if migration_status["failed"] > 0:
            print_error(f"Failed migrations: {migration_status['failed']}")
        if migration_status["last_migration"]:
            print_info(f"  Last migration: {migration_status['last_migration']}")
    else:
        print_warning("No migrations have been applied")

    results["checks"]["migrations"] = migration_status

    # 5. Table Row Counts
    print(f"\n{Colors.BOLD}5. Table Row Counts{Colors.END}")
    existing_tables = [t for t, exists in table_status.items() if exists]
    counts = get_table_counts(conn, existing_tables)

    important_tables = ["users", "campaigns", "videos", "ads", "predictions",
                       "video_embeddings", "semantic_cache_entries"]

    for table in important_tables:
        if table in counts:
            count = counts[table]
            if count > 0:
                print_success(f"  {table}: {count:,} rows")
            elif count == 0:
                print_warning(f"  {table}: 0 rows (empty)")
            else:
                print_error(f"  {table}: Error reading count")

    results["checks"]["row_counts"] = counts

    # 6. Data Integrity
    print(f"\n{Colors.BOLD}6. Data Integrity{Colors.END}")
    integrity = check_data_integrity(conn)

    for check_name, passed in integrity.items():
        if check_name == "error":
            print_error(f"Integrity check error: {passed}")
        elif passed:
            print_success(f"  {check_name.replace('_', ' ').title()}")
        else:
            print_error(f"  {check_name.replace('_', ' ').title()}")
            results["status"] = "degraded"

    results["checks"]["integrity"] = integrity

    # Detailed checks
    if detailed:
        # 7. Database Size
        print(f"\n{Colors.BOLD}7. Database Size{Colors.END}")
        db_size = get_database_size(conn)
        print_info(f"  Total size: {db_size}")
        results["checks"]["size"] = db_size

        # 8. Index Usage
        print(f"\n{Colors.BOLD}8. Top Index Usage{Colors.END}")
        index_usage = get_index_usage(conn)

        if index_usage:
            print_info("  Top 5 most used indexes:")
            for idx in index_usage[:5]:
                print(f"    {idx['table']}.{idx['index']}: {idx['scans']:,} scans ({idx['size']})")
        else:
            print_warning("  No index usage data available")

        results["checks"]["index_usage"] = index_usage

        # 9. Performance Summary
        print(f"\n{Colors.BOLD}9. Performance Summary{Colors.END}")
        perf = get_performance_summary(conn)

        if "campaigns" in perf:
            print_info(f"  Active campaigns: {perf['campaigns']['total_campaigns']}")
            print_info(f"  Average ROAS: {perf['campaigns']['avg_roas']:.2f}")
            print_info(f"  Total spend: ${perf['campaigns']['total_spend']:,.2f}")
            print_info(f"  Total revenue: ${perf['campaigns']['total_revenue']:,.2f}")

        if "predictions" in perf:
            print_info(f"  Total predictions: {perf['predictions']['total_predictions']}")
            if perf['predictions']['with_actuals'] > 0:
                print_info(f"  Predictions with actuals: {perf['predictions']['with_actuals']}")
                print_info(f"  Avg CTR error: {perf['predictions']['avg_ctr_error']:.4f}")
                print_info(f"  Avg ROAS error: {perf['predictions']['avg_roas_error']:.2f}")

        results["checks"]["performance"] = perf

    conn.close()
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Database Health Checker for GeminiVideo Platform"
    )
    parser.add_argument("--quick", action="store_true", help="Quick check (connectivity + tables only)")
    parser.add_argument("--detailed", action="store_true", help="Detailed report with statistics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.json:
        results = run_health_check(quick=args.quick, detailed=args.detailed)
        print(json.dumps(results, indent=2, default=str))
        return 0 if results["status"] == "healthy" else 1

    results = run_health_check(quick=args.quick, detailed=args.detailed)

    # Summary
    print_header("HEALTH CHECK SUMMARY")

    if results["status"] == "healthy":
        print_success("Database is healthy and operational")
    elif results["status"] == "degraded":
        print_warning("Database is operational but has issues")
    else:
        print_error("Database has critical issues")

    print(f"\n{Colors.BOLD}Status: {results['status'].upper()}{Colors.END}")
    print(f"{Colors.BOLD}Timestamp: {results['timestamp']}{Colors.END}\n")

    return 0 if results["status"] == "healthy" else 1

if __name__ == "__main__":
    sys.exit(main())
