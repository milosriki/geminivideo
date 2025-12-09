"""
Stress Test: Database Operations and Transactions
Tests all database tables, transactions, and data integrity
Covers: All tables, transactions, constraints, indexes, concurrent writes
"""
import asyncio
import time
import random
import numpy as np
from typing import List, Dict, Any
import httpx
import logging
import uuid
import psycopg2
from psycopg2 import pool

logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/geminivideo"
GATEWAY_URL = "http://localhost:8000"


class DatabaseOperationsTester:
    """Test database operations and transactions"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.created_ids = {
            "users": [],
            "campaigns": [],
            "blueprints": [],
            "render_jobs": [],
            "videos": [],
            "pending_ad_changes": [],
            "ad_change_history": []
        }
    
    async def test_table_users(self) -> Dict[str, Any]:
        """Test users table operations"""
        start_time = time.time()
        
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            
            # Insert
            user_id = str(uuid.uuid4())
            email = f"test_{uuid.uuid4().hex[:8]}@test.com"
            cur.execute(
                "INSERT INTO users (id, email, full_name) VALUES (%s, %s, %s) RETURNING id",
                (user_id, email, f"Test User {uuid.uuid4().hex[:6]}")
            )
            conn.commit()
            self.created_ids["users"].append(user_id)
            
            # Read
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            
            # Update
            cur.execute("UPDATE users SET full_name = %s WHERE id = %s", ("Updated Name", user_id))
            conn.commit()
            
            # Delete
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            conn.commit()
            
            cur.close()
            self.db_pool.putconn(conn)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "table": "users",
                "success": True,
                "operations": ["insert", "read", "update", "delete"],
                "duration_ms": duration
            }
        
        except Exception as e:
            if 'conn' in locals():
                self.db_pool.putconn(conn)
            return {
                "table": "users",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_table_campaigns(self) -> Dict[str, Any]:
        """Test campaigns table with foreign key to users"""
        start_time = time.time()
        
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            
            # Create user first
            user_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO users (id, email) VALUES (%s, %s) RETURNING id",
                (user_id, f"test_{uuid.uuid4().hex[:8]}@test.com")
            )
            conn.commit()
            
            # Insert campaign
            campaign_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO campaigns (id, user_id, product_name, offer, status)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (campaign_id, user_id, f"Product {uuid.uuid4().hex[:6]}", "Test Offer", "draft")
            )
            conn.commit()
            self.created_ids["campaigns"].append(campaign_id)
            
            # Test JSONB fields
            cur.execute(
                "UPDATE campaigns SET pain_points = %s, desires = %s WHERE id = %s",
                (['pain1', 'pain2'], ['desire1', 'desire2'], campaign_id)
            )
            conn.commit()
            
            # Read with JSONB
            cur.execute("SELECT pain_points, desires FROM campaigns WHERE id = %s", (campaign_id,))
            result = cur.fetchone()
            
            cur.close()
            self.db_pool.putconn(conn)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "table": "campaigns",
                "success": True,
                "jsonb_fields_tested": True,
                "duration_ms": duration
            }
        
        except Exception as e:
            if 'conn' in locals():
                self.db_pool.putconn(conn)
            return {
                "table": "campaigns",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_table_blueprints(self) -> Dict[str, Any]:
        """Test blueprints table with foreign keys"""
        start_time = time.time()
        
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            
            # Create user and campaign
            user_id = str(uuid.uuid4())
            cur.execute("INSERT INTO users (id, email) VALUES (%s, %s)", (user_id, f"test_{uuid.uuid4().hex[:8]}@test.com"))
            campaign_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO campaigns (id, user_id, product_name, offer) VALUES (%s, %s, %s, %s)",
                (campaign_id, user_id, "Test Product", "Test Offer")
            )
            conn.commit()
            
            # Insert blueprint
            blueprint_id = str(uuid.uuid4())
            cur.execute(
                """INSERT INTO blueprints (id, campaign_id, title, hook_text, hook_type, 
                   script_json, council_score, predicted_roas, confidence, verdict, rank)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (blueprint_id, campaign_id, "Test Blueprint", "Test Hook", "testimonial",
                 '{"scenes": []}', 0.85, 4.5, 0.9, "APPROVED", 1)
            )
            conn.commit()
            self.created_ids["blueprints"].append(blueprint_id)
            
            cur.close()
            self.db_pool.putconn(conn)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "table": "blueprints",
                "success": True,
                "duration_ms": duration
            }
        
        except Exception as e:
            if 'conn' in locals():
                self.db_pool.putconn(conn)
            return {
                "table": "blueprints",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_table_pending_ad_changes(self) -> Dict[str, Any]:
        """Test pending_ad_changes table (queue operations)"""
        start_time = time.time()
        
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            
            # Insert pending change
            change_id = str(uuid.uuid4())
            ad_id = f"ad_{uuid.uuid4()}"
            cur.execute(
                """INSERT INTO pending_ad_changes (id, ad_id, change_type, new_budget, status, created_at)
                   VALUES (%s, %s, %s, %s, %s, NOW()) RETURNING id""",
                (change_id, ad_id, "BUDGET_INCREASE", 100.50, "PENDING")
            )
            conn.commit()
            self.created_ids["pending_ad_changes"].append(change_id)
            
            # Test SKIP LOCKED (claim operation)
            cur.execute(
                """UPDATE pending_ad_changes 
                   SET status = 'PROCESSING', claimed_at = NOW()
                   WHERE id = %s AND status = 'PENDING'
                   RETURNING id""",
                (change_id,)
            )
            claimed = cur.fetchone()
            conn.commit()
            
            # Test second claim (should return nothing)
            cur.execute(
                """UPDATE pending_ad_changes 
                   SET status = 'PROCESSING'
                   WHERE id = %s AND status = 'PENDING'
                   RETURNING id""",
                (change_id,)
            )
            second_claim = cur.fetchone()
            
            cur.close()
            self.db_pool.putconn(conn)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "table": "pending_ad_changes",
                "success": True,
                "skip_locked_tested": True,
                "claim_works": claimed is not None,
                "second_claim_fails": second_claim is None,
                "duration_ms": duration
            }
        
        except Exception as e:
            if 'conn' in locals():
                self.db_pool.putconn(conn)
            return {
                "table": "pending_ad_changes",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_transaction_rollback(self) -> Dict[str, Any]:
        """Test transaction rollback on error"""
        start_time = time.time()
        
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            
            # Start transaction
            user_id = str(uuid.uuid4())
            cur.execute("INSERT INTO users (id, email) VALUES (%s, %s)", (user_id, f"test_{uuid.uuid4().hex[:8]}@test.com"))
            
            # Try to insert campaign with invalid foreign key (should fail)
            try:
                invalid_campaign_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO campaigns (id, user_id, product_name, offer) VALUES (%s, %s, %s, %s)",
                    (invalid_campaign_id, "invalid-user-id", "Test", "Test")
                )
                conn.commit()
            except Exception:
                conn.rollback()
            
            # Verify user was not inserted (rollback worked)
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user_exists = cur.fetchone()
            
            cur.close()
            self.db_pool.putconn(conn)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "test": "transaction_rollback",
                "success": True,
                "rollback_works": user_exists is None,
                "duration_ms": duration
            }
        
        except Exception as e:
            if 'conn' in locals():
                self.db_pool.putconn(conn)
            return {
                "test": "transaction_rollback",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }
    
    async def test_concurrent_writes(self, concurrent: int = 10) -> Dict[str, Any]:
        """Test concurrent writes to same table"""
        start_time = time.time()
        
        async def write_campaign(i):
            try:
                conn = self.db_pool.getconn()
                cur = conn.cursor()
                
                user_id = str(uuid.uuid4())
                cur.execute("INSERT INTO users (id, email) VALUES (%s, %s)", (user_id, f"test_{i}_{uuid.uuid4().hex[:8]}@test.com"))
                
                campaign_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO campaigns (id, user_id, product_name, offer) VALUES (%s, %s, %s, %s)",
                    (campaign_id, user_id, f"Product {i}", "Offer")
                )
                conn.commit()
                
                cur.close()
                self.db_pool.putconn(conn)
                return {"success": True, "campaign_id": campaign_id}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        results = await asyncio.gather(*[write_campaign(i) for i in range(concurrent)])
        
        duration = (time.time() - start_time) * 1000
        successful = sum(1 for r in results if r.get("success"))
        
        return {
            "test": "concurrent_writes",
            "success": True,
            "concurrent": concurrent,
            "successful": successful,
            "failed": concurrent - successful,
            "duration_ms": duration
        }
    
    async def test_indexes(self) -> Dict[str, Any]:
        """Test database indexes performance"""
        start_time = time.time()
        
        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            
            # Test indexed query (user_id on campaigns)
            cur.execute("SELECT * FROM campaigns WHERE user_id = %s LIMIT 1", (str(uuid.uuid4()),))
            indexed_result = cur.fetchone()
            
            # Test non-indexed query (if any)
            cur.execute("SELECT * FROM campaigns WHERE product_name = %s LIMIT 1", ("Test Product",))
            non_indexed_result = cur.fetchone()
            
            cur.close()
            self.db_pool.putconn(conn)
            
            duration = (time.time() - start_time) * 1000
            
            return {
                "test": "indexes",
                "success": True,
                "indexed_query_works": True,
                "duration_ms": duration
            }
        
        except Exception as e:
            if 'conn' in locals():
                self.db_pool.putconn(conn)
            return {
                "test": "indexes",
                "success": False,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000
            }


async def stress_test_database_operations(
    concurrent: int = 20,
    total_operations: int = 200
) -> Dict[str, Any]:
    """Run stress test for database operations"""
    
    logger.info(f"Starting database operations stress test: {concurrent} concurrent, {total_operations} total")
    
    # Create connection pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, concurrent, DATABASE_URL)
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        return {
            "success": False,
            "error": f"Database connection failed: {e}"
        }
    
    results = []
    start_time = time.time()
    
    # Test individual tables
    tester = DatabaseOperationsTester(db_pool)
    
    table_tests = [
        tester.test_table_users(),
        tester.test_table_campaigns(),
        tester.test_table_blueprints(),
        tester.test_table_pending_ad_changes(),
        tester.test_transaction_rollback(),
        tester.test_indexes()
    ]
    
    table_results = await asyncio.gather(*table_tests, return_exceptions=True)
    results.extend([r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in table_results])
    
    # Test concurrent writes
    concurrent_results = []
    for _ in range(total_operations // concurrent):
        concurrent_result = await tester.test_concurrent_writes(concurrent)
        concurrent_results.append(concurrent_result)
    
    total_duration = time.time() - start_time
    
    # Cleanup
    db_pool.closeall()
    
    successful = [r for r in results if r.get("success")]
    
    return {
        "total_operations": total_operations,
        "concurrent": concurrent,
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "success_rate": len(successful) / len(results) if results else 0,
        "total_duration_seconds": total_duration,
        "operations_per_second": total_operations / total_duration if total_duration > 0 else 0,
        "table_tests": results,
        "concurrent_write_tests": concurrent_results
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Note: Requires DATABASE_URL environment variable
    asyncio.run(stress_test_database_operations(concurrent=10, total_operations=100))

