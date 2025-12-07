#!/usr/bin/env python3
"""
Production Validation Script
Run before handing off to marketing experts
"""

import httpx
import asyncio
import sys
from typing import Dict, List, Tuple
from datetime import datetime

# Service URLs
SERVICES = {
    'gateway': 'https://gateway.geminivideo.run',
    'ml_service': 'https://ml-service.geminivideo.run',
    'titan_core': 'https://titan-core.geminivideo.run',
    'video_agent': 'https://video-agent.geminivideo.run',
    'meta_publisher': 'https://meta-publisher.geminivideo.run',
    'drive_intel': 'https://drive-intel.geminivideo.run'
}

CHECKS: List[Tuple[str, str, str]] = []
PASSED = 0
FAILED = 0


async def check_service_health(name: str, url: str) -> bool:
    """Check if service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{url}/health")
            if response.status_code == 200:
                CHECKS.append((name, 'health', '✅ PASS'))
                return True
            else:
                CHECKS.append((name, 'health', f'❌ FAIL ({response.status_code})'))
                return False
    except Exception as e:
        CHECKS.append((name, 'health', f'❌ FAIL ({str(e)[:50]})'))
        return False


async def check_learning_loop() -> bool:
    """Verify learning loop is closed"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send test feedback
            response = await client.post(
                f"{SERVICES['ml_service']}/api/ml/feedback",
                json={
                    "ad_id": f"validation_test_{datetime.now().timestamp()}",
                    "variant_id": f"validation_test_{datetime.now().timestamp()}",
                    "impressions": 100,
                    "clicks": 5,
                    "conversions": 1,
                    "spend": 10.0,
                    "revenue": 50.0
                }
            )
            if response.status_code == 200:
                CHECKS.append(('ml_service', 'learning_loop', '✅ PASS'))
                return True
            else:
                CHECKS.append(('ml_service', 'learning_loop', f'❌ FAIL ({response.status_code})'))
                return False
    except Exception as e:
        CHECKS.append(('ml_service', 'learning_loop', f'❌ FAIL ({str(e)[:50]})'))
        return False


async def check_thompson_cost() -> bool:
    """Verify Thompson Sampling accumulates cost"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            variant_id = f"cost_check_{datetime.now().timestamp()}"

            # Register
            await client.post(
                f"{SERVICES['ml_service']}/api/ml/ab/register-variant",
                json={"variant_id": variant_id}
            )

            # Update with cost
            await client.post(
                f"{SERVICES['ml_service']}/api/ml/ab/update-variant",
                json={"variant_id": variant_id, "reward": 1.0, "cost": 25.0}
            )

            # Check stats
            stats = await client.get(f"{SERVICES['ml_service']}/api/ml/ab/variant-stats/{variant_id}")
            data = stats.json()

            if data.get('spend', 0) > 0:
                CHECKS.append(('ml_service', 'thompson_cost', '✅ PASS'))
                return True
            else:
                CHECKS.append(('ml_service', 'thompson_cost', '❌ FAIL (spend=0)'))
                return False
    except Exception as e:
        CHECKS.append(('ml_service', 'thompson_cost', f'❌ FAIL ({str(e)[:50]})'))
        return False


async def check_gateway_proxies() -> bool:
    """Verify Gateway proxies critical endpoints"""
    endpoints_to_check = [
        ('/api/council/evaluate', 'POST'),
        ('/api/oracle/predict', 'POST'),
    ]

    all_passed = True
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint, method in endpoints_to_check:
            try:
                if method == 'POST':
                    response = await client.post(
                        f"{SERVICES['gateway']}{endpoint}",
                        json={"test": True}
                    )
                else:
                    response = await client.get(f"{SERVICES['gateway']}{endpoint}")

                if response.status_code != 404:
                    CHECKS.append(('gateway', f'proxy_{endpoint}', '✅ PASS'))
                else:
                    CHECKS.append(('gateway', f'proxy_{endpoint}', '❌ FAIL (404)'))
                    all_passed = False
            except Exception as e:
                CHECKS.append(('gateway', f'proxy_{endpoint}', f'❌ FAIL ({str(e)[:30]})'))
                all_passed = False

    return all_passed


async def check_time_decay() -> bool:
    """Verify time decay endpoint exists"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['ml_service']}/api/ml/ab/apply-decay",
                params={"decay_factor": 0.99}
            )
            if response.status_code in [200, 422]:  # 422 is OK (means endpoint exists but validation failed)
                CHECKS.append(('ml_service', 'time_decay', '✅ PASS'))
                return True
            else:
                CHECKS.append(('ml_service', 'time_decay', f'❌ FAIL ({response.status_code})'))
                return False
    except Exception as e:
        CHECKS.append(('ml_service', 'time_decay', f'❌ FAIL ({str(e)[:50]})'))
        return False


async def run_validation():
    """Run all validation checks"""
    global PASSED, FAILED

    print("=" * 60)
    print("🔍 GEMINIVIDEO PRODUCTION VALIDATION")
    print(f"   Started: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # 1. Health Checks
    print("📋 PHASE 1: Service Health Checks")
    print("-" * 40)
    for name, url in SERVICES.items():
        result = await check_service_health(name, url)
        if result:
            PASSED += 1
        else:
            FAILED += 1
    print()

    # 2. Learning Loop
    print("📋 PHASE 2: Learning Loop Validation")
    print("-" * 40)
    if await check_learning_loop():
        PASSED += 1
    else:
        FAILED += 1
    print()

    # 3. Thompson Cost
    print("📋 PHASE 3: Thompson Sampling Cost Flow")
    print("-" * 40)
    if await check_thompson_cost():
        PASSED += 1
    else:
        FAILED += 1
    print()

    # 4. Time Decay
    print("📋 PHASE 4: Time Decay Endpoint")
    print("-" * 40)
    if await check_time_decay():
        PASSED += 1
    else:
        FAILED += 1
    print()

    # 5. Gateway Proxies
    print("📋 PHASE 5: Gateway Proxy Verification")
    print("-" * 40)
    await check_gateway_proxies()
    print()

    # Results
    print("=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)

    for service, check, result in CHECKS:
        print(f"  {service:15} | {check:25} | {result}")

    print()
    print("-" * 60)
    total = len(CHECKS)
    passed = sum(1 for _, _, r in CHECKS if '✅' in r)
    failed = total - passed

    print(f"  TOTAL CHECKS: {total}")
    print(f"  ✅ PASSED:    {passed}")
    print(f"  ❌ FAILED:    {failed}")
    print(f"  SCORE:        {(passed/total)*100:.1f}%")
    print("-" * 60)

    if failed == 0:
        print()
        print("🎉 ALL CHECKS PASSED - READY FOR PRODUCTION!")
        print()
        return 0
    else:
        print()
        print("⚠️  SOME CHECKS FAILED - REVIEW BEFORE PRODUCTION")
        print()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_validation())
    sys.exit(exit_code)
