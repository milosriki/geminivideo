#!/usr/bin/env python3
"""
Demo Data Seeder for GeminiVideo Platform
€5M Investment-Grade Presentation Data

Seeds realistic demo data for investor presentations including:
- Sample campaigns with performance metrics
- High-performing ads with predictions
- Winning creative DNA patterns
- Cross-account learning examples
- Realistic performance trajectories

Usage:
    python scripts/seed-demo.py                # Seed all demo data
    python scripts/seed-demo.py --minimal      # Minimal dataset (faster)
    python scripts/seed-demo.py --clear        # Clear existing demo data first
"""

import os
import sys
import argparse
import random
import psycopg2
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict
import json

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg): print(f"{Colors.GREEN}✓ {msg}{Colors.END}")
def print_info(msg): print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")
def print_error(msg): print(f"{Colors.RED}✗ {msg}{Colors.END}")

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

def get_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(get_database_url())
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        sys.exit(1)

# Sample data generators
HOOK_TYPES = [
    "question", "stat", "controversy", "story", "transformation",
    "problem_agitation", "curiosity_gap", "pattern_interrupt"
]

INDUSTRIES = [
    "ecommerce", "saas", "fitness", "finance", "education",
    "real_estate", "healthcare", "food_delivery"
]

PRODUCTS = {
    "ecommerce": ["Premium Headphones", "Smart Watch", "Eco-Friendly Water Bottle"],
    "saas": ["Project Management Tool", "CRM Software", "Email Marketing Platform"],
    "fitness": ["30-Day Challenge", "Online Coaching", "Workout App"],
    "finance": ["Investment Course", "Budgeting App", "Crypto Trading Guide"],
    "education": ["Online Course", "Coding Bootcamp", "Language Learning App"]
}

def generate_user(conn, email: str, full_name: str, industry: str) -> str:
    """Create a demo user"""
    user_id = str(uuid4())
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (id, email, full_name, company_name, role, created_at)
            VALUES (%s, %s, %s, %s, 'admin', NOW())
            ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name
            RETURNING id
        """, (user_id, email, full_name, f"{full_name.split()[0]} {industry.title()}"))
        result = cur.fetchone()
        user_id = result[0] if result else user_id
    conn.commit()
    return user_id

def generate_campaign(conn, user_id: str, product: str, industry: str, status: str = "active") -> str:
    """Create a demo campaign"""
    campaign_id = str(uuid4())

    # Generate performance metrics
    days_running = random.randint(7, 30)
    daily_budget = random.uniform(500, 2000)
    spend = daily_budget * days_running
    roas = random.uniform(2.5, 5.5) if status == "active" else random.uniform(1.5, 3.0)
    revenue = spend * roas
    conversions = int(revenue / random.uniform(50, 150))

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO campaigns (
                id, user_id, name, product_name, offer, status,
                budget_daily, spend, revenue, roas, conversions,
                total_generated, approved_count, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s days', NOW()
            )
        """, (
            campaign_id, user_id,
            f"{product} Launch Campaign",
            product,
            f"Get {product} - Limited Time Offer",
            status,
            daily_budget, spend, revenue, roas, conversions,
            random.randint(10, 50), random.randint(5, 20),
            days_running
        ))
    conn.commit()
    return campaign_id

def generate_blueprint(conn, campaign_id: str, hook_type: str) -> str:
    """Create a demo blueprint"""
    blueprint_id = str(uuid4())

    council_score = random.uniform(0.75, 0.95)
    predicted_roas = random.uniform(3.0, 6.0)
    predicted_ctr = random.uniform(0.02, 0.05)

    hooks = {
        "question": "What if I told you this could change everything?",
        "stat": "97% of people don't know this secret...",
        "story": "I was broke 2 years ago. Now I'm...",
        "transformation": "From zero to hero in 90 days"
    }

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO blueprints (
                id, campaign_id, title, hook_text, hook_type,
                script_json, council_score, predicted_roas, predicted_ctr,
                confidence, verdict, rank, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s days'
            )
        """, (
            blueprint_id, campaign_id,
            f"Blueprint: {hook_type.replace('_', ' ').title()}",
            hooks.get(hook_type, "Attention-grabbing hook"),
            hook_type,
            json.dumps({"scenes": ["hook", "problem", "solution", "cta"]}),
            council_score, predicted_roas, predicted_ctr,
            random.uniform(0.8, 0.95),
            "approved",
            random.randint(1, 10),
            random.randint(1, 7)
        ))
    conn.commit()
    return blueprint_id

def generate_video(conn, campaign_id: str, blueprint_id: str) -> str:
    """Create a demo video"""
    video_id = str(uuid4())

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO videos (
                id, campaign_id, blueprint_id, title, status,
                duration_seconds, format, created_at
            ) VALUES (
                %s, %s, %s, %s, 'ready', %s, 'mp4', NOW() - INTERVAL '%s days'
            )
        """, (
            video_id, campaign_id, blueprint_id,
            f"Ad Video {random.randint(1, 100)}",
            random.uniform(15, 60),
            random.randint(1, 5)
        ))
    conn.commit()
    return video_id

def generate_ad(conn, campaign_id: str, video_id: str, blueprint_id: str) -> str:
    """Create a demo ad"""
    ad_id = str(uuid4())

    predicted_ctr = random.uniform(0.02, 0.05)
    predicted_roas = random.uniform(3.0, 6.0)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ads (
                ad_id, campaign_id, video_id, blueprint_id,
                title, status, approved, platform,
                predicted_ctr, predicted_roas,
                created_at, approved_at
            ) VALUES (
                %s, %s, %s, %s, %s, 'published', TRUE, 'facebook',
                %s, %s, NOW() - INTERVAL '%s days', NOW() - INTERVAL '%s days'
            )
        """, (
            ad_id, campaign_id, video_id, blueprint_id,
            f"Ad Creative {random.randint(1, 100)}",
            predicted_ctr, predicted_roas,
            random.randint(2, 10), random.randint(1, 9)
        ))
    conn.commit()
    return ad_id

def generate_prediction(conn, video_id: str, ad_id: str, hook_type: str, is_winner: bool = False):
    """Create a prediction record"""
    prediction_id = str(uuid4())

    if is_winner:
        predicted_ctr = random.uniform(0.035, 0.05)
        predicted_roas = random.uniform(4.0, 6.0)
        actual_ctr = predicted_ctr + random.uniform(-0.005, 0.01)
        actual_roas = predicted_roas + random.uniform(-0.5, 1.0)
    else:
        predicted_ctr = random.uniform(0.02, 0.04)
        predicted_roas = random.uniform(2.5, 4.0)
        actual_ctr = predicted_ctr + random.uniform(-0.01, 0.01)
        actual_roas = predicted_roas + random.uniform(-1.0, 1.0)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO predictions (
                id, video_id, ad_id, platform,
                predicted_ctr, predicted_roas, predicted_conversion,
                actual_ctr, actual_roas, actual_conversion,
                impressions, clicks, spend,
                council_score, hook_type, template_type,
                created_at, actuals_fetched_at
            ) VALUES (
                %s, %s, %s, 'facebook',
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, 'standard',
                NOW() - INTERVAL '%s days', NOW() - INTERVAL '%s days'
            )
        """, (
            prediction_id, video_id, ad_id,
            predicted_ctr, predicted_roas, predicted_ctr * 0.2,
            actual_ctr, actual_roas, actual_ctr * 0.2,
            random.randint(10000, 100000),
            int(random.randint(10000, 100000) * actual_ctr),
            random.uniform(500, 2000),
            random.uniform(0.8, 0.95),
            hook_type,
            random.randint(5, 15), random.randint(1, 10)
        ))
    conn.commit()

def generate_performance_metrics(conn, video_id: str, campaign_id: str, days: int = 14):
    """Generate daily performance metrics"""
    base_date = datetime.now().date() - timedelta(days=days)

    for i in range(days):
        date = base_date + timedelta(days=i)
        impressions = random.randint(5000, 20000)
        ctr = random.uniform(0.02, 0.05)
        clicks = int(impressions * ctr)
        cpc = random.uniform(0.5, 2.0)
        spend = clicks * cpc
        conversions = int(clicks * random.uniform(0.05, 0.15))
        revenue = conversions * random.uniform(50, 150)
        roas = revenue / spend if spend > 0 else 0

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO performance_metrics (
                    id, video_id, campaign_id, platform, date,
                    impressions, clicks, spend, revenue, conversions,
                    ctr, cpc, roas, created_at
                ) VALUES (
                    %s, %s, %s, 'facebook', %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, NOW()
                )
            """, (
                str(uuid4()), video_id, campaign_id, date,
                impressions, clicks, spend, revenue, conversions,
                ctr, cpc, roas
            ))
    conn.commit()

def generate_creative_dna(conn, account_id: str, creative_id: str, is_winner: bool = True):
    """Generate creative DNA extraction"""
    extraction_id = str(uuid4())

    if is_winner:
        roas = random.uniform(4.0, 6.0)
        ctr = random.uniform(0.04, 0.06)
    else:
        roas = random.uniform(2.0, 3.5)
        ctr = random.uniform(0.02, 0.035)

    hook_dna = {
        "hook_type": random.choice(HOOK_TYPES),
        "intensity": random.uniform(0.7, 0.95),
        "curiosity_score": random.uniform(0.8, 1.0)
    }

    visual_dna = {
        "dominant_color": random.choice(["blue", "red", "green", "orange"]),
        "motion_intensity": random.uniform(0.6, 0.9),
        "face_presence": random.choice([True, False])
    }

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO creative_dna_extractions (
                extraction_id, creative_id, account_id,
                hook_dna, visual_dna, ctr, roas, conversion_rate,
                extracted_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s days'
            )
        """, (
            extraction_id, creative_id, account_id,
            json.dumps(hook_dna), json.dumps(visual_dna),
            ctr, roas, ctr * 0.2,
            random.randint(1, 30)
        ))
    conn.commit()

def generate_cross_pattern(conn, pattern_type: str):
    """Generate cross-account pattern"""
    pattern_id = str(uuid4())

    pattern_features = {
        "type": pattern_type,
        "characteristics": ["high_energy", "clear_cta", "social_proof"],
        "optimal_duration": random.uniform(15, 30)
    }

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO cross_account_patterns (
                pattern_id, pattern_name, pattern_type, pattern_features,
                sample_size, account_count, avg_roas, avg_ctr,
                confidence_score, industries, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '%s days'
            )
        """, (
            pattern_id,
            f"High-Performing {pattern_type.replace('_', ' ').title()} Pattern",
            pattern_type,
            json.dumps(pattern_features),
            random.randint(50, 200),
            random.randint(10, 30),
            random.uniform(3.5, 5.5),
            random.uniform(0.03, 0.05),
            random.uniform(0.85, 0.95),
            random.sample(INDUSTRIES, k=random.randint(2, 4)),
            random.randint(10, 60)
        ))
    conn.commit()

def seed_demo_data(conn, minimal: bool = False):
    """Seed comprehensive demo data"""
    print_info("🌱 Seeding demo data for investor presentation...\n")

    # Create demo users
    print_info("Creating demo users...")
    demo_users = [
        ("demo@geminivideo.ai", "Demo User", "ecommerce"),
        ("investor@example.com", "Investor Preview", "saas"),
        ("success@example.com", "Success Story", "fitness")
    ]

    user_ids = []
    for email, name, industry in demo_users:
        user_id = generate_user(conn, email, name, industry)
        user_ids.append((user_id, industry))
        print_success(f"  Created user: {name}")

    # Create campaigns for each user
    print_info("\nCreating campaigns...")
    campaigns = []
    for user_id, industry in user_ids[:2 if minimal else 3]:
        products = PRODUCTS.get(industry, ["Product A", "Product B"])
        for i, product in enumerate(products[:1 if minimal else 2]):
            campaign_id = generate_campaign(
                conn, user_id, product, industry,
                status="active" if i == 0 else random.choice(["active", "completed"])
            )
            campaigns.append(campaign_id)
            print_success(f"  Created campaign: {product}")

    # Create blueprints, videos, and ads
    print_info("\nGenerating creative content...")
    total_ads = 0
    for campaign_id in campaigns[:3 if minimal else len(campaigns)]:
        for hook_type in random.sample(HOOK_TYPES, k=2 if minimal else 4):
            blueprint_id = generate_blueprint(conn, campaign_id, hook_type)
            video_id = generate_video(conn, campaign_id, blueprint_id)
            ad_id = generate_ad(conn, campaign_id, video_id, blueprint_id)

            # Generate predictions
            is_winner = random.random() > 0.6  # 40% are high performers
            generate_prediction(conn, video_id, ad_id, hook_type, is_winner)

            # Generate performance metrics
            generate_performance_metrics(conn, video_id, campaign_id, days=7 if minimal else 14)

            # Generate DNA extractions for winners
            if is_winner:
                generate_creative_dna(conn, f"account_{random.randint(1,5)}", ad_id, True)

            total_ads += 1

    print_success(f"  Generated {total_ads} ads with predictions and metrics")

    # Generate cross-account patterns
    if not minimal:
        print_info("\nGenerating cross-account patterns...")
        for pattern_type in ["hook", "visual", "pacing", "copy"][:2 if minimal else 4]:
            generate_cross_pattern(conn, pattern_type)
        print_success("  Created cross-account learning patterns")

    # Generate daily analytics
    print_info("\nGenerating aggregated analytics...")
    for i in range(7 if minimal else 30):
        date = datetime.now().date() - timedelta(days=i)
        spend = random.uniform(500, 2000)
        roas = random.uniform(2.5, 5.0)
        revenue = spend * roas

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO daily_analytics (date, spend, revenue, roas, impressions, clicks, conversions, ctr, cpc, cpa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    spend = EXCLUDED.spend,
                    revenue = EXCLUDED.revenue,
                    roas = EXCLUDED.roas
            """, (
                date, spend, revenue, roas,
                random.randint(50000, 200000),
                random.randint(1000, 5000),
                random.randint(50, 300),
                random.uniform(0.02, 0.05),
                random.uniform(0.5, 2.0),
                random.uniform(10, 50)
            ))
    conn.commit()
    print_success("  Generated daily analytics data")

def clear_demo_data(conn):
    """Clear existing demo data"""
    print_warning("Clearing existing demo data...")

    tables = [
        "feedback_events", "feedback_loops", "improvement_trajectory",
        "compound_learnings", "learning_metrics", "learning_cycles",
        "pattern_applications", "pattern_contributions", "cross_account_patterns",
        "dna_applications", "creative_dna_extractions", "creative_formulas",
        "semantic_cache_entries", "ad_creative_embeddings", "script_embeddings",
        "video_embeddings", "winning_ad_patterns",
        "predictions", "performance_metrics", "daily_analytics",
        "emotions", "clips", "ads", "videos", "render_jobs", "blueprints",
        "campaigns", "jobs", "audit_logs"
    ]

    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} CASCADE")
                print_success(f"  Cleared {table}")
            except Exception as e:
                print_warning(f"  Could not clear {table}: {e}")

    conn.commit()

def main():
    parser = argparse.ArgumentParser(description="Seed demo data for GeminiVideo platform")
    parser.add_argument("--minimal", action="store_true", help="Seed minimal dataset")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}GeminiVideo Demo Data Seeder{Colors.END}")
    print(f"{Colors.BOLD}€5M Investment-Grade Presentation Data{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    conn = get_connection()
    print_success("Database connected")

    try:
        if args.clear:
            clear_demo_data(conn)
            print()

        seed_demo_data(conn, minimal=args.minimal)

        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print_success("Demo data seeding completed!")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

        print("📊 Demo Data Summary:")
        with conn.cursor() as cur:
            tables_to_count = [
                "users", "campaigns", "blueprints", "videos", "ads",
                "predictions", "performance_metrics", "creative_dna_extractions"
            ]
            for table in tables_to_count:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    print(f"   {table}: {count} records")
                except:
                    pass

        print("\n✨ Ready for investor presentation!")
        print("   - Realistic campaign data")
        print("   - High-performing ads with DNA")
        print("   - Prediction accuracy metrics")
        print("   - Cross-account learning patterns\n")

    except Exception as e:
        print_error(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
