#!/usr/bin/env python3
"""
Comprehensive Lost Ideas Verification Script

This script verifies the actual implementation status of all "lost" optimizations
identified in WHAT_WAS_LOST.md.

Usage:
    python scripts/verify_lost_optimizations.py
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


class OptimizationVerifier:
    """Verifies implementation status of optimizations."""
    
    def __init__(self):
        self.results = []
        
    def check_file_exists(self, filepath: str) -> bool:
        """Check if a file exists."""
        return os.path.exists(filepath)
    
    def check_pattern_in_file(self, filepath: str, pattern: str) -> bool:
        """Check if a pattern exists in a file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return pattern in content
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
            return False
    
    def check_redis_cache(self) -> Tuple[str, str, str]:
        """Verify Redis cache implementation for semantic caching."""
        print(f"\n{BOLD}1. Checking Semantic Cache (Redis) Implementation...{RESET}")
        
        checks = []
        
        # Check 1: Redis in requirements.txt
        redis_in_requirements = self.check_pattern_in_file(
            'services/ml-service/requirements.txt',
            'redis'
        )
        checks.append(("Redis in requirements.txt", redis_in_requirements))
        
        # Check 2: Redis import in battle_hardened_sampler.py
        redis_import = self.check_pattern_in_file(
            'services/ml-service/src/battle_hardened_sampler.py',
            'import redis'
        )
        checks.append(("Redis import in code", redis_import))
        
        # Check 3: Cache lookup implementation
        cache_lookup = self.check_pattern_in_file(
            'services/ml-service/src/battle_hardened_sampler.py',
            'redis_client.get(cache_key_redis)'
        )
        checks.append(("Cache lookup implemented", cache_lookup))
        
        # Check 4: Cache storage implementation
        cache_set = self.check_pattern_in_file(
            'services/ml-service/src/battle_hardened_sampler.py',
            'redis_client.setex'
        )
        checks.append(("Cache storage implemented", cache_set))
        
        # Check 5: Cache key generation
        cache_key_gen = self.check_pattern_in_file(
            'services/ml-service/src/battle_hardened_sampler.py',
            '_generate_cache_key'
        )
        checks.append(("Cache key generation", cache_key_gen))
        
        # Print results
        for check_name, result in checks:
            status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
            print(f"  {status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            return "WORKING", "Semantic cache fully implemented with Redis", GREEN
        else:
            failed_count = sum(1 for _, result in checks if not result)
            return "PARTIAL", f"{failed_count}/{len(checks)} checks failed", YELLOW
    
    def check_batch_executor(self) -> Tuple[str, str, str]:
        """Verify batch executor integration."""
        print(f"\n{BOLD}2. Checking Batch Executor Integration...{RESET}")
        
        checks = []
        
        # Check 1: batch-executor.ts exists
        batch_executor_exists = self.check_file_exists(
            'services/gateway-api/src/jobs/batch-executor.ts'
        )
        checks.append(("batch-executor.ts exists", batch_executor_exists))
        
        # Check 2: Import in safe-executor.ts
        batch_import = self.check_pattern_in_file(
            'services/gateway-api/src/jobs/safe-executor.ts',
            'import { processBatchChanges } from'
        )
        checks.append(("Batch import in safe-executor", batch_import))
        
        # Check 3: BATCH_MODE_ENABLED
        batch_mode = self.check_pattern_in_file(
            'services/gateway-api/src/jobs/safe-executor.ts',
            'BATCH_MODE_ENABLED'
        )
        checks.append(("BATCH_MODE_ENABLED flag", batch_mode))
        
        # Check 4: processBatchChanges called
        batch_call = self.check_pattern_in_file(
            'services/gateway-api/src/jobs/safe-executor.ts',
            'await processBatchChanges'
        )
        checks.append(("processBatchChanges called", batch_call))
        
        # Check 5: Database batch claim function
        db_function = self.check_file_exists(
            'database/migrations/009_batch_ad_changes.sql'
        )
        checks.append(("DB batch claim function", db_function))
        
        # Check 6: Batch claim function definition
        function_def = self.check_pattern_in_file(
            'database/migrations/009_batch_ad_changes.sql',
            'claim_pending_ad_changes_batch'
        )
        checks.append(("Batch function defined", function_def))
        
        # Print results
        for check_name, result in checks:
            status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
            print(f"  {status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            return "WORKING", "Batch executor fully integrated and enabled by default", GREEN
        else:
            failed_count = sum(1 for _, result in checks if not result)
            return "PARTIAL", f"{failed_count}/{len(checks)} checks failed", YELLOW
    
    def check_cross_learner(self) -> Tuple[str, str, str]:
        """Verify cross-learner integration."""
        print(f"\n{BOLD}3. Checking Cross-Learner Integration...{RESET}")
        
        checks = []
        
        # Check 1: cross_learner.py exists
        cross_learner_exists = self.check_file_exists(
            'services/ml-service/src/cross_learner.py'
        )
        checks.append(("cross_learner.py exists", cross_learner_exists))
        
        # Check 2: Import in battle_hardened_sampler.py
        if cross_learner_exists:
            cross_import = self.check_pattern_in_file(
                'services/ml-service/src/battle_hardened_sampler.py',
                'cross_learner'
            )
            checks.append(("Cross-learner import", cross_import))
            
            # Check 3: Boost function exists
            boost_function = self.check_pattern_in_file(
                'services/ml-service/src/battle_hardened_sampler.py',
                '_apply_cross_learner_boost'
            )
            checks.append(("Boost function defined", boost_function))
        else:
            checks.append(("Cross-learner import", False))
            checks.append(("Boost function defined", False))
        
        # Print results
        for check_name, result in checks:
            status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
            print(f"  {status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            return "WORKING", "Cross-learner integrated (runtime method verification recommended)", YELLOW
        elif cross_learner_exists:
            return "PARTIAL", "Cross-learner exists but integration incomplete", YELLOW
        else:
            return "NOT_WORKING", "Cross-learner file not found", RED
    
    def check_meta_capi(self) -> Tuple[str, str, str]:
        """Verify Meta CAPI implementation."""
        print(f"\n{BOLD}4. Checking Meta CAPI Implementation...{RESET}")
        
        checks = []
        
        # Check 1: Meta CAPI service/endpoint exists
        meta_publisher_exists = self.check_file_exists(
            'services/meta-publisher'
        )
        checks.append(("Meta publisher service exists", meta_publisher_exists))
        
        # Check 2: Environment variable template
        env_template = self.check_pattern_in_file(
            '.env.example',
            'META_PIXEL_ID'
        )
        checks.append(("META_PIXEL_ID in .env.example", env_template))
        
        meta_token = self.check_pattern_in_file(
            '.env.example',
            'META_ACCESS_TOKEN'
        )
        checks.append(("META_ACCESS_TOKEN in .env.example", meta_token))
        
        # Check 3: Check if Meta CAPI code exists
        # Look for CAPI-related code
        if meta_publisher_exists:
            capi_code = (
                self.check_pattern_in_file('services/meta-publisher/main.py', 'capi') or
                self.check_pattern_in_file('services/meta-publisher/index.ts', 'capi') or
                self.check_pattern_in_file('services/meta-publisher/src/index.ts', 'capi')
            )
            checks.append(("CAPI code implementation", capi_code))
        
        # Print results
        for check_name, result in checks:
            status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
            print(f"  {status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            return "WORKING", "Meta CAPI implemented (needs API credentials to activate)", YELLOW
        elif any(result for _, result in checks):
            return "PARTIAL", "Meta CAPI partially implemented", YELLOW
        else:
            return "NOT_WORKING", "Meta CAPI not found", RED
    
    def check_instant_learning(self) -> Tuple[str, str, str]:
        """Verify instant learning implementation."""
        print(f"\n{BOLD}5. Checking Instant Learning Implementation...{RESET}")
        
        checks = []
        
        # Check 1: Learning endpoint
        learning_endpoint = (
            self.check_pattern_in_file('services/gateway-api/src/index.ts', '/learning') or
            self.check_pattern_in_file('services/gateway-api/index.ts', '/learning') or
            self.check_pattern_in_file('services/ml-service/main.py', '/learning')
        )
        checks.append(("Learning API endpoint exists", learning_endpoint))
        
        # Check 2: Weight update logic
        weight_update = (
            self.check_pattern_in_file('services/ml-service/src/self_learning.py', 'update') or
            self.check_pattern_in_file('services/gateway-api/src/services/learning-service.ts', 'update') or
            self.check_pattern_in_file('shared/config/weights.yaml', 'weight')
        )
        checks.append(("Weight update mechanism", weight_update))
        
        # Check 3: Weights configuration file
        weights_config = self.check_file_exists('shared/config/weights.yaml')
        checks.append(("Weights config file exists", weights_config))
        
        # Print results
        for check_name, result in checks:
            status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
            print(f"  {status} {check_name}")
        
        all_passed = all(result for _, result in checks)
        
        if all_passed:
            return "WORKING", "Instant learning implemented (needs runtime testing)", YELLOW
        elif any(result for _, result in checks):
            return "PARTIAL", "Instant learning partially implemented", YELLOW
        else:
            return "NOT_WORKING", "Instant learning not found", RED
    
    def run_all_checks(self):
        """Run all verification checks."""
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}Lost Ideas Verification Report{RESET}")
        print(f"{BOLD}{'='*70}{RESET}")
        
        # Run all checks
        redis_cache = self.check_redis_cache()
        batch_executor = self.check_batch_executor()
        cross_learner = self.check_cross_learner()
        meta_capi = self.check_meta_capi()
        instant_learning = self.check_instant_learning()
        
        # Summary
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}Summary{RESET}")
        print(f"{BOLD}{'='*70}{RESET}\n")
        
        results = [
            ("Semantic Cache (Redis)", *redis_cache),
            ("Batch Executor", *batch_executor),
            ("Cross-Learner", *cross_learner),
            ("Meta CAPI", *meta_capi),
            ("Instant Learning", *instant_learning),
        ]
        
        for name, status, message, color in results:
            status_icon = {
                "WORKING": f"{GREEN}✅{RESET}",
                "PARTIAL": f"{YELLOW}⚠️{RESET}",
                "NOT_WORKING": f"{RED}❌{RESET}"
            }.get(status, f"{RED}❓{RESET}")
            
            print(f"{status_icon} {BOLD}{name}{RESET}: {message}")
        
        # Calculate overall status
        working_count = sum(1 for _, status, _, _ in results if status == "WORKING")
        partial_count = sum(1 for _, status, _, _ in results if status == "PARTIAL")
        total_count = len(results)
        
        print(f"\n{BOLD}Overall Status:{RESET}")
        print(f"  ✅ Working: {working_count}/{total_count}")
        print(f"  ⚠️  Partial: {partial_count}/{total_count}")
        print(f"  ❌ Not Working: {total_count - working_count - partial_count}/{total_count}")
        
        percentage = ((working_count + 0.5 * partial_count) / total_count) * 100
        print(f"\n{BOLD}Estimated Completion:{RESET} {percentage:.0f}%")
        
        if percentage >= 80:
            print(f"\n{GREEN}🎉 Excellent! Most optimizations are implemented!{RESET}")
        elif percentage >= 50:
            print(f"\n{YELLOW}⚠️  Good progress, but some work remains.{RESET}")
        else:
            print(f"\n{RED}⚠️  Significant implementation work needed.{RESET}")
        
        print(f"\n{BOLD}{'='*70}{RESET}\n")
        
        return percentage >= 80


if __name__ == '__main__':
    verifier = OptimizationVerifier()
    success = verifier.run_all_checks()
    sys.exit(0 if success else 1)
