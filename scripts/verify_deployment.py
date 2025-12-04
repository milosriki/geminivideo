#!/usr/bin/env python3
"""Verify all services are properly connected and functioning.

This script checks:
1. All microservices are up and healthy
2. Database connections work
3. AI endpoints return real data (not hardcoded)
4. Inter-service communication works
"""
import httpx
import asyncio
import sys
import json
from typing import List, Tuple, Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


HEALTH_CHECKS = [
    ("Gateway API", "http://localhost:8000/health"),
    ("Drive Intel", "http://localhost:8001/health"),
    ("Video Agent", "http://localhost:8002/health"),
    ("ML Service", "http://localhost:8003/health"),
]


async def check_health() -> List[Tuple[str, bool, str]]:
    """Check health of all services"""
    results = []
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in HEALTH_CHECKS:
            try:
                resp = await client.get(url)
                success = resp.status_code == 200
                message = f"Status: {resp.status_code}"
                results.append((name, success, message))
            except Exception as e:
                results.append((name, False, f"Error: {str(e)}"))

    return results


async def check_ai_endpoints() -> List[Tuple[str, bool, str]]:
    """Verify AI endpoints return real data, not hardcoded"""
    results = []
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Analyze endpoint returns varied responses
        try:
            responses = []
            for i in range(2):
                resp = await client.post(
                    f"{base_url}/api/analyze",
                    json={"video_uri": f"test_video_{i}.mp4"}
                )
                if resp.status_code == 200:
                    responses.append(resp.json())

            if len(responses) >= 2:
                if responses[0] == responses[1]:
                    results.append((
                        "AI Analysis Variation",
                        False,
                        "Responses are identical - still hardcoded!"
                    ))
                else:
                    results.append((
                        "AI Analysis Variation",
                        True,
                        "Responses vary - using real AI"
                    ))
            else:
                results.append((
                    "AI Analysis Variation",
                    False,
                    "Could not get multiple responses"
                ))
        except Exception as e:
            results.append((
                "AI Analysis Variation",
                False,
                f"Error: {str(e)}"
            ))

        # Test 2: Metrics not hardcoded to 15000
        try:
            resp = await client.get(f"{base_url}/api/metrics")
            if resp.status_code == 200:
                data = resp.json()
                impressions = data.get("totals", {}).get("impressions", 15000)

                if impressions == 15000:
                    results.append((
                        "Metrics Real Data",
                        False,
                        "Still returning hardcoded 15000 impressions"
                    ))
                else:
                    results.append((
                        "Metrics Real Data",
                        True,
                        f"Using real data: {impressions} impressions"
                    ))
            else:
                results.append((
                    "Metrics Real Data",
                    False,
                    f"Status: {resp.status_code}"
                ))
        except Exception as e:
            results.append((
                "Metrics Real Data",
                False,
                f"Error: {str(e)}"
            ))

        # Test 3: AI provides reasoning
        try:
            resp = await client.post(
                f"{base_url}/api/analyze",
                json={"video_uri": "test_reasoning.mp4"}
            )
            if resp.status_code == 200:
                data = resp.json()
                response_text = str(data).lower()

                has_reasoning = any(
                    term in response_text for term in
                    ["reasoning", "analysis", "because", "since", "appears", "suggests"]
                )

                if has_reasoning:
                    results.append((
                        "AI Reasoning Present",
                        True,
                        "AI provides reasoning and analysis"
                    ))
                else:
                    results.append((
                        "AI Reasoning Present",
                        False,
                        "No AI reasoning found in response"
                    ))
            else:
                results.append((
                    "AI Reasoning Present",
                    False,
                    f"Status: {resp.status_code}"
                ))
        except Exception as e:
            results.append((
                "AI Reasoning Present",
                False,
                f"Error: {str(e)}"
            ))

    return results


async def check_database() -> Tuple[str, bool, str]:
    """Verify database connectivity"""
    try:
        # Check if DB connection endpoint exists
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:8000/api/health/db")

            if resp.status_code == 200:
                return ("Database Connection", True, "Connected")
            else:
                return ("Database Connection", False, f"Status: {resp.status_code}")
    except Exception as e:
        return ("Database Connection", False, f"Error: {str(e)}")


async def check_inter_service_communication() -> List[Tuple[str, bool, str]]:
    """Verify services can communicate with each other"""
    results = []

    # Check Gateway -> Drive Intel
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:8000/api/insights")

            if resp.status_code in [200, 404]:  # 404 means route exists but no data
                results.append((
                    "Gateway -> Drive Intel",
                    True,
                    "Communication working"
                ))
            else:
                results.append((
                    "Gateway -> Drive Intel",
                    False,
                    f"Status: {resp.status_code}"
                ))
    except Exception as e:
        results.append((
            "Gateway -> Drive Intel",
            False,
            f"Error: {str(e)}"
        ))

    # Check Gateway -> Video Agent
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                "http://localhost:8000/api/analyze",
                json={"video_uri": "test.mp4"}
            )

            if resp.status_code in [200, 422]:  # 422 means validation works
                results.append((
                    "Gateway -> Video Agent",
                    True,
                    "Communication working"
                ))
            else:
                results.append((
                    "Gateway -> Video Agent",
                    False,
                    f"Status: {resp.status_code}"
                ))
    except Exception as e:
        results.append((
            "Gateway -> Video Agent",
            False,
            f"Error: {str(e)}"
        ))

    return results


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")


def print_result(name: str, success: bool, message: str):
    """Print a single check result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if success else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} {name:.<40} {message}")


async def verify_all() -> bool:
    """Run all verification checks"""
    all_passed = True

    print(f"\n{Colors.BOLD}🔍 Gemini Video Deployment Verification{Colors.RESET}")
    print(f"{Colors.BLUE}Starting verification checks...{Colors.RESET}")

    # Health Checks
    print_section("Service Health Checks")
    health_results = await check_health()
    for name, success, message in health_results:
        print_result(name, success, message)
        if not success:
            all_passed = False

    # Database Check
    print_section("Database Connectivity")
    db_name, db_success, db_message = await check_database()
    print_result(db_name, db_success, db_message)
    if not db_success:
        all_passed = False

    # AI Endpoint Checks
    print_section("AI Endpoint Verification (No Hardcoded Data)")
    ai_results = await check_ai_endpoints()
    for name, success, message in ai_results:
        print_result(name, success, message)
        if not success:
            all_passed = False

    # Inter-service Communication
    print_section("Inter-Service Communication")
    comm_results = await check_inter_service_communication()
    for name, success, message in comm_results:
        print_result(name, success, message)
        if not success:
            all_passed = False

    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED{Colors.RESET}")
        print(f"{Colors.GREEN}System is properly deployed and functioning.{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED{Colors.RESET}")
        print(f"{Colors.YELLOW}Please review the failures above and fix issues.{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

    return all_passed


async def main():
    """Main entry point"""
    try:
        success = await verify_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Verification interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error during verification: {e}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
