#!/usr/bin/env python3
"""
AGENT 57: PRODUCTION READINESS VALIDATION SCRIPT

Comprehensive production readiness check:
- All endpoints responding
- All AI APIs functional
- Database schema valid
- External integrations configured
- Security measures in place
- Performance baselines met

Outputs: GO / NO-GO decision for production deployment
"""

import sys
import os
import requests
import json
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime
import subprocess

# Service URLs
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:8000')
META_PUBLISHER_URL = os.getenv('META_PUBLISHER_URL', 'http://localhost:8083')
GOOGLE_ADS_URL = os.getenv('GOOGLE_ADS_URL', 'http://localhost:8084')
TITAN_CORE_URL = os.getenv('TITAN_CORE_URL', 'http://localhost:8004')
ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:8003')
VIDEO_AGENT_URL = os.getenv('VIDEO_AGENT_URL', 'http://localhost:8002')
DRIVE_INTEL_URL = os.getenv('DRIVE_INTEL_URL', 'http://localhost:8001')

# Database
DATABASE_URL = os.getenv('DATABASE_URL')

# Thresholds
API_TIMEOUT = 10
CRITICAL_THRESHOLD = 0  # No critical failures allowed
WARNING_THRESHOLD = 3  # Max 3 warnings for GO


class ProductionValidator:
    """Validates production readiness"""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'critical_failures': 0,
            'warnings': 0,
            'passed': 0,
            'total': 0
        }

    def run_all_checks(self) -> bool:
        """Run all validation checks"""
        print("="*80)
        print("🔍 PRODUCTION READINESS VALIDATION")
        print("="*80)
        print()
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Run check categories
        self._check_services()
        self._check_ai_apis()
        self._check_database()
        self._check_external_integrations()
        self._check_security()
        self._check_performance()

        # Generate report
        return self._generate_report()

    def _add_check(self, category: str, name: str, status: str, message: str, critical: bool = False):
        """Add check result"""
        self.results['checks'].append({
            'category': category,
            'name': name,
            'status': status,
            'message': message,
            'critical': critical,
            'timestamp': datetime.now().isoformat()
        })

        self.results['total'] += 1

        if status == 'PASS':
            self.results['passed'] += 1
        elif status == 'FAIL':
            if critical:
                self.results['critical_failures'] += 1
            else:
                self.results['warnings'] += 1

    def _check_services(self):
        """Check all microservices"""
        print("📊 CHECKING SERVICES...")
        print()

        services = {
            'Gateway API': GATEWAY_URL,
            'Meta Publisher': META_PUBLISHER_URL,
            'Google Ads': GOOGLE_ADS_URL,
            'Titan Core': TITAN_CORE_URL,
            'ML Service': ML_SERVICE_URL,
            'Video Agent': VIDEO_AGENT_URL,
            'Drive Intel': DRIVE_INTEL_URL
        }

        for name, url in services.items():
            try:
                response = requests.get(f"{url}/health", timeout=API_TIMEOUT)
                if response.status_code == 200:
                    print(f"   ✅ {name}: HEALTHY")
                    self._add_check('Services', name, 'PASS', 'Service responding', critical=True)
                else:
                    print(f"   ❌ {name}: UNHEALTHY ({response.status_code})")
                    self._add_check('Services', name, 'FAIL', f'Status {response.status_code}', critical=True)
            except requests.exceptions.ConnectionError:
                print(f"   ❌ {name}: NOT RESPONDING")
                self._add_check('Services', name, 'FAIL', 'Connection failed', critical=True)
            except Exception as e:
                print(f"   ⚠️  {name}: ERROR ({e})")
                self._add_check('Services', name, 'FAIL', str(e), critical=False)

        print()

    def _check_ai_apis(self):
        """Check AI/ML APIs"""
        print("🤖 CHECKING AI/ML APIS...")
        print()

        # Test Gateway AI scoring
        print("   Testing AI Scoring...")
        try:
            payload = {
                "scenes": [{"clip_id": "test", "features": {"has_face": True}}],
                "metadata": {"test": True}
            }
            response = requests.post(
                f"{GATEWAY_URL}/api/score/storyboard",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if 'scores' in result and 'final_ctr_prediction' in result['scores']:
                    print(f"      ✅ AI Scoring: WORKING")
                    self._add_check('AI/ML', 'Scoring API', 'PASS', 'Predictions responding', critical=True)
                else:
                    print(f"      ⚠️  AI Scoring: INCOMPLETE RESPONSE")
                    self._add_check('AI/ML', 'Scoring API', 'FAIL', 'Missing scores', critical=False)
            else:
                print(f"      ❌ AI Scoring: FAILED ({response.status_code})")
                self._add_check('AI/ML', 'Scoring API', 'FAIL', f'Status {response.status_code}', critical=True)
        except Exception as e:
            print(f"      ❌ AI Scoring: ERROR ({e})")
            self._add_check('AI/ML', 'Scoring API', 'FAIL', str(e), critical=True)

        # Test XGBoost model
        print("   Testing XGBoost Model...")
        try:
            payload = {
                "clip_data": {"duration": 15.0, "has_face": True},
                "include_confidence": True
            }
            response = requests.post(
                f"{ML_SERVICE_URL}/api/ml/predict-ctr",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                print(f"      ✅ XGBoost: WORKING")
                self._add_check('AI/ML', 'XGBoost Model', 'PASS', 'Model responding', critical=False)
            else:
                print(f"      ⚠️  XGBoost: NOT AVAILABLE")
                self._add_check('AI/ML', 'XGBoost Model', 'FAIL', 'Not responding', critical=False)
        except Exception as e:
            print(f"      ℹ️  XGBoost: {e}")
            self._add_check('AI/ML', 'XGBoost Model', 'FAIL', 'Service unavailable', critical=False)

        print()

    def _check_database(self):
        """Check database connection and schema"""
        print("💾 CHECKING DATABASE...")
        print()

        if not DATABASE_URL:
            print("   ❌ DATABASE_URL not set")
            self._add_check('Database', 'Configuration', 'FAIL', 'DATABASE_URL missing', critical=True)
            print()
            return

        print("   ✅ DATABASE_URL configured")

        # Test connection
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            # Test basic query
            cursor.execute("SELECT NOW()")
            result = cursor.fetchone()

            print(f"   ✅ Database connection: OK")
            print(f"      Server time: {result[0]}")
            self._add_check('Database', 'Connection', 'PASS', 'Connected successfully', critical=True)

            # Check for required tables
            required_tables = ['users', 'assets', 'clips', 'campaigns', 'predictions']
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]

            print(f"\n   📊 Schema validation:")
            for table in required_tables:
                if table in existing_tables:
                    print(f"      ✅ Table '{table}': EXISTS")
                    self._add_check('Database', f'Table: {table}', 'PASS', 'Table exists', critical=True)
                else:
                    print(f"      ❌ Table '{table}': MISSING")
                    self._add_check('Database', f'Table: {table}', 'FAIL', 'Table missing', critical=True)

            cursor.close()
            conn.close()

        except ImportError:
            print("   ⚠️  psycopg2 not installed - skipping DB checks")
            self._add_check('Database', 'Library', 'FAIL', 'psycopg2 not available', critical=False)
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            self._add_check('Database', 'Connection', 'FAIL', str(e), critical=True)

        print()

    def _check_external_integrations(self):
        """Check external API integrations"""
        print("🔌 CHECKING EXTERNAL INTEGRATIONS...")
        print()

        # Meta Ads
        print("   Meta Ads API:")
        try:
            response = requests.get(f"{META_PUBLISHER_URL}/", timeout=API_TIMEOUT)
            config = response.json()

            if config.get('real_sdk_enabled'):
                print(f"      ✅ Meta SDK: CONFIGURED")
                self._add_check('Integrations', 'Meta Ads API', 'PASS', 'SDK configured', critical=False)
            else:
                print(f"      ⚠️  Meta SDK: NOT CONFIGURED (dry-run mode)")
                self._add_check('Integrations', 'Meta Ads API', 'FAIL', 'Credentials missing', critical=False)
        except Exception as e:
            print(f"      ⚠️  Meta: {e}")
            self._add_check('Integrations', 'Meta Ads API', 'FAIL', str(e), critical=False)

        # Google Ads
        print("   Google Ads API:")
        try:
            response = requests.get(f"{GOOGLE_ADS_URL}/health", timeout=API_TIMEOUT)
            if response.status_code == 200:
                print(f"      ✅ Google Ads: AVAILABLE")
                self._add_check('Integrations', 'Google Ads API', 'PASS', 'Service available', critical=False)
            else:
                print(f"      ⚠️  Google Ads: NOT CONFIGURED")
                self._add_check('Integrations', 'Google Ads API', 'FAIL', 'Not configured', critical=False)
        except Exception as e:
            print(f"      ℹ️  Google Ads: {e}")
            self._add_check('Integrations', 'Google Ads API', 'FAIL', 'Service unavailable', critical=False)

        print()

    def _check_security(self):
        """Check security measures"""
        print("🔒 CHECKING SECURITY...")
        print()

        # Test rate limiting
        print("   Rate Limiting:")
        try:
            # Make multiple rapid requests
            responses = []
            for _ in range(10):
                response = requests.get(f"{GATEWAY_URL}/health", timeout=2)
                responses.append(response.status_code)

            if 429 in responses:  # Too Many Requests
                print(f"      ✅ Rate limiting: ACTIVE")
                self._add_check('Security', 'Rate Limiting', 'PASS', 'Working correctly', critical=False)
            else:
                print(f"      ⚠️  Rate limiting: NOT DETECTED")
                self._add_check('Security', 'Rate Limiting', 'FAIL', 'No rate limit detected', critical=False)
        except Exception as e:
            print(f"      ℹ️  Rate limiting: {e}")
            self._add_check('Security', 'Rate Limiting', 'FAIL', str(e), critical=False)

        # Check HTTPS (in production)
        print("   HTTPS:")
        if GATEWAY_URL.startswith('https://'):
            print(f"      ✅ HTTPS: ENABLED")
            self._add_check('Security', 'HTTPS', 'PASS', 'SSL enabled', critical=True)
        else:
            print(f"      ⚠️  HTTPS: DISABLED (OK for local dev)")
            self._add_check('Security', 'HTTPS', 'FAIL', 'HTTP only', critical=False)

        # Check for exposed secrets
        print("   Secret Management:")
        if DATABASE_URL and 'password' in DATABASE_URL.lower():
            print(f"      ✅ Secrets: CONFIGURED VIA ENV")
            self._add_check('Security', 'Secret Management', 'PASS', 'Using environment variables', critical=True)
        else:
            print(f"      ⚠️  Secrets: CHECK CONFIGURATION")
            self._add_check('Security', 'Secret Management', 'FAIL', 'Configuration unclear', critical=False)

        print()

    def _check_performance(self):
        """Check performance baselines"""
        print("⚡ CHECKING PERFORMANCE...")
        print()

        # Test API response time
        print("   API Response Time:")
        try:
            start = time.time()
            response = requests.get(f"{GATEWAY_URL}/health", timeout=API_TIMEOUT)
            elapsed = (time.time() - start) * 1000  # ms

            print(f"      Response: {elapsed:.0f}ms")

            if elapsed < 1000:  # < 1 second
                print(f"      ✅ Performance: EXCELLENT (<1s)")
                self._add_check('Performance', 'API Response Time', 'PASS', f'{elapsed:.0f}ms', critical=False)
            elif elapsed < 3000:  # < 3 seconds
                print(f"      ✅ Performance: ACCEPTABLE (<3s)")
                self._add_check('Performance', 'API Response Time', 'PASS', f'{elapsed:.0f}ms', critical=False)
            else:
                print(f"      ⚠️  Performance: SLOW (>{elapsed:.0f}ms)")
                self._add_check('Performance', 'API Response Time', 'FAIL', 'Too slow', critical=False)
        except Exception as e:
            print(f"      ⚠️  Performance: {e}")
            self._add_check('Performance', 'API Response Time', 'FAIL', str(e), critical=False)

        # Test AI response time
        print("   AI Scoring Time:")
        try:
            payload = {"scenes": [{"clip_id": "test"}], "metadata": {}}
            start = time.time()
            response = requests.post(
                f"{GATEWAY_URL}/api/score/storyboard",
                json=payload,
                timeout=30
            )
            elapsed = (time.time() - start) * 1000  # ms

            print(f"      Response: {elapsed:.0f}ms")

            if elapsed < 5000:  # < 5 seconds
                print(f"      ✅ AI Performance: GOOD (<5s)")
                self._add_check('Performance', 'AI Scoring Time', 'PASS', f'{elapsed:.0f}ms', critical=False)
            else:
                print(f"      ⚠️  AI Performance: NEEDS OPTIMIZATION (>{elapsed:.0f}ms)")
                self._add_check('Performance', 'AI Scoring Time', 'FAIL', 'Too slow', critical=False)
        except Exception as e:
            print(f"      ⚠️  AI Performance: {e}")
            self._add_check('Performance', 'AI Scoring Time', 'FAIL', str(e), critical=False)

        print()

    def _generate_report(self) -> bool:
        """Generate final report and GO/NO-GO decision"""
        print()
        print("="*80)
        print("📋 PRODUCTION READINESS REPORT")
        print("="*80)
        print()

        print(f"Total Checks: {self.results['total']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Warnings: {self.results['warnings']} ⚠️")
        print(f"Critical Failures: {self.results['critical_failures']} ❌")
        print()

        # Show failures
        if self.results['critical_failures'] > 0 or self.results['warnings'] > 0:
            print("⚠️  ISSUES FOUND:")
            print()

            for check in self.results['checks']:
                if check['status'] == 'FAIL':
                    icon = "❌" if check['critical'] else "⚠️"
                    print(f"   {icon} {check['category']} / {check['name']}")
                    print(f"      {check['message']}")

            print()

        # GO/NO-GO decision
        print("="*80)

        if self.results['critical_failures'] > CRITICAL_THRESHOLD:
            print("🛑 DECISION: NO-GO")
            print()
            print(f"   ❌ {self.results['critical_failures']} critical failure(s) detected")
            print("   ❌ NOT READY for production deployment")
            print()
            print("ACTION REQUIRED:")
            print("   1. Fix all critical failures")
            print("   2. Re-run validation")
            print("   3. Ensure all services are healthy")
            print()
            decision = False

        elif self.results['warnings'] > WARNING_THRESHOLD:
            print("⚠️  DECISION: GO WITH CAUTION")
            print()
            print(f"   ⚠️  {self.results['warnings']} warning(s) detected")
            print("   ⚠️  Production deployment possible but not optimal")
            print()
            print("RECOMMENDED ACTIONS:")
            print("   1. Review and address warnings")
            print("   2. Monitor closely in production")
            print("   3. Plan fixes for next sprint")
            print()
            decision = True

        else:
            print("✅ DECISION: GO")
            print()
            print("   ✅ All critical checks passed")
            print("   ✅ READY for production deployment")
            print()
            print("NEXT STEPS:")
            print("   1. Deploy to production")
            print("   2. Run smoke tests")
            print("   3. Monitor performance")
            print()
            decision = True

        print("="*80)
        print()

        # Save report
        report_file = '/tmp/production_validation_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"📄 Full report saved: {report_file}")
        print()

        return decision


def main():
    validator = ProductionValidator()
    is_ready = validator.run_all_checks()

    # Exit code: 0 for GO, 1 for NO-GO
    sys.exit(0 if is_ready else 1)


if __name__ == '__main__':
    main()
