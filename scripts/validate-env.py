#!/usr/bin/env python3
"""
Environment Validation Script for €5M Ad Platform
Validates all required environment variables, API keys, and service connectivity
"""

import os
import sys
import json
import re
import socket
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse


@dataclass
class ValidationResult:
    """Result of a validation check"""
    name: str
    category: str
    status: str  # 'pass', 'fail', 'warn', 'skip'
    message: str
    details: Optional[Dict] = None


class EnvironmentValidator:
    """Comprehensive environment validation for production deployment"""

    def __init__(self, env_file: Optional[str] = None, skip_connectivity: bool = False):
        self.env_file = env_file
        self.skip_connectivity = skip_connectivity
        self.results: List[ValidationResult] = []
        self.load_environment()

    def load_environment(self):
        """Load environment variables from .env file if specified"""
        if self.env_file and os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        os.environ[key] = value

    def add_result(self, name: str, category: str, status: str, message: str, details: Optional[Dict] = None):
        """Add validation result"""
        self.results.append(ValidationResult(name, category, status, message, details))

    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================

    def check_env_var(self, name: str, category: str, required: bool = True,
                      pattern: Optional[str] = None, min_length: Optional[int] = None) -> bool:
        """Check if environment variable exists and is valid"""
        value = os.getenv(name)

        if not value:
            if required:
                self.add_result(name, category, 'fail', 'Missing required variable')
                return False
            else:
                self.add_result(name, category, 'skip', 'Optional variable not set')
                return True

        # Check for placeholder values
        placeholder_patterns = [
            r'^(your[_-]|YOUR[_-])',
            r'(placeholder|PLACEHOLDER)',
            r'^(xxxx|XXXX)',
            r'change[_-]this',
            r'_here$',
        ]

        for p in placeholder_patterns:
            if re.search(p, value, re.IGNORECASE):
                status = 'fail' if required else 'warn'
                self.add_result(name, category, status, 'Placeholder value detected')
                return False

        # Check pattern if provided
        if pattern and not re.match(pattern, value):
            self.add_result(name, category, 'fail', f'Invalid format (expected pattern: {pattern})')
            return False

        # Check minimum length
        if min_length and len(value) < min_length:
            status = 'warn' if not required else 'fail'
            self.add_result(name, category, status, f'Too short (min {min_length} chars, got {len(value)})')
            return not required

        self.add_result(name, category, 'pass', f'Set ({len(value)} chars)')
        return True

    def check_url(self, name: str, category: str, required: bool = True, schemes: Optional[List[str]] = None) -> bool:
        """Check if URL is valid"""
        value = os.getenv(name)

        if not value:
            if required:
                self.add_result(name, category, 'fail', 'Missing required URL')
                return False
            else:
                self.add_result(name, category, 'skip', 'Optional URL not set')
                return True

        if schemes is None:
            schemes = ['http', 'https', 'postgresql', 'postgres', 'redis', 'rediss']

        pattern = f"^({'|'.join(schemes)})://.+"
        if not re.match(pattern, value):
            self.add_result(name, category, 'fail', f'Invalid URL format (expected: {", ".join(schemes)}://...)')
            return False

        self.add_result(name, category, 'pass', f'Valid URL ({value[:50]}...)')
        return True

    def check_api_key_format(self, name: str, category: str, prefix: str,
                            required: bool = True, min_length: int = 20) -> bool:
        """Check API key format"""
        value = os.getenv(name)

        if not value:
            if required:
                self.add_result(name, category, 'fail', 'Missing required API key')
                return False
            else:
                self.add_result(name, category, 'skip', 'Optional API key not set')
                return True

        if not value.startswith(prefix):
            self.add_result(name, category, 'fail', f'Invalid format (should start with "{prefix}")')
            return False

        if len(value) < min_length:
            self.add_result(name, category, 'warn', f'Suspiciously short ({len(value)} chars)')
            return True

        self.add_result(name, category, 'pass', f'Valid format ({len(value)} chars)')
        return True

    # =========================================================================
    # CONNECTIVITY TESTS
    # =========================================================================

    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL database connectivity"""
        if self.skip_connectivity:
            self.add_result('PostgreSQL', 'Database', 'skip', 'Connectivity test skipped')
            return True

        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.add_result('PostgreSQL', 'Database', 'fail', 'DATABASE_URL not set')
            return False

        try:
            import psycopg2
            from urllib.parse import urlparse

            parsed = urlparse(database_url)

            # Test connection with short timeout
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/').split('?')[0],
                connect_timeout=5
            )

            # Test query
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            self.add_result('PostgreSQL', 'Database', 'pass',
                          'Connection successful',
                          {'version': version[:50]})
            return True

        except ImportError:
            self.add_result('PostgreSQL', 'Database', 'warn',
                          'psycopg2 not installed, skipping connectivity test')
            return True
        except Exception as e:
            self.add_result('PostgreSQL', 'Database', 'fail',
                          f'Connection failed: {str(e)[:100]}')
            return False

    def test_redis_connection(self) -> bool:
        """Test Redis connectivity"""
        if self.skip_connectivity:
            self.add_result('Redis', 'Cache', 'skip', 'Connectivity test skipped')
            return True

        redis_url = os.getenv('REDIS_URL') or os.getenv('UPSTASH_REDIS_REST_URL')
        if not redis_url:
            self.add_result('Redis', 'Cache', 'skip', 'Redis not configured')
            return True

        try:
            import redis
            from urllib.parse import urlparse

            # Handle Upstash REST API differently
            if 'upstash' in redis_url.lower():
                # Upstash uses REST, can't test with standard redis-py
                self.add_result('Redis', 'Cache', 'pass',
                              'Upstash Redis configured (REST API)')
                return True

            parsed = urlparse(redis_url)

            r = redis.Redis(
                host=parsed.hostname,
                port=parsed.port or 6379,
                password=parsed.password,
                socket_connect_timeout=5
            )

            # Test ping
            if r.ping():
                info = r.info('server')
                self.add_result('Redis', 'Cache', 'pass',
                              'Connection successful',
                              {'version': info.get('redis_version')})
                return True
            else:
                self.add_result('Redis', 'Cache', 'fail', 'Ping failed')
                return False

        except ImportError:
            self.add_result('Redis', 'Cache', 'warn',
                          'redis-py not installed, skipping connectivity test')
            return True
        except Exception as e:
            self.add_result('Redis', 'Cache', 'fail',
                          f'Connection failed: {str(e)[:100]}')
            return False

    def test_s3_access(self) -> bool:
        """Test S3/R2 bucket access"""
        if self.skip_connectivity:
            self.add_result('S3/R2', 'Storage', 'skip', 'Connectivity test skipped')
            return True

        # Check if AWS/S3 is configured
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        bucket = os.getenv('S3_BUCKET') or os.getenv('R2_BUCKET')

        if not (access_key and secret_key and bucket):
            self.add_result('S3/R2', 'Storage', 'skip', 'S3/R2 not configured')
            return True

        try:
            import boto3
            from botocore.config import Config

            # Determine endpoint (R2 or S3)
            endpoint_url = os.getenv('R2_ENDPOINT') or os.getenv('S3_ENDPOINT')

            config = Config(
                signature_version='s3v4',
                connect_timeout=5,
                read_timeout=5
            )

            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=endpoint_url,
                config=config
            )

            # Test bucket access
            response = s3_client.head_bucket(Bucket=bucket)

            self.add_result('S3/R2', 'Storage', 'pass',
                          f'Bucket "{bucket}" accessible',
                          {'status_code': response['ResponseMetadata']['HTTPStatusCode']})
            return True

        except ImportError:
            self.add_result('S3/R2', 'Storage', 'warn',
                          'boto3 not installed, skipping connectivity test')
            return True
        except Exception as e:
            self.add_result('S3/R2', 'Storage', 'fail',
                          f'Bucket access failed: {str(e)[:100]}')
            return False

    # =========================================================================
    # AI API TESTS
    # =========================================================================

    def test_gemini_api(self) -> bool:
        """Test Gemini API with minimal request"""
        if self.skip_connectivity:
            self.add_result('Gemini API', 'AI Services', 'skip', 'API test skipped')
            return True

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.add_result('Gemini API', 'AI Services', 'fail', 'API key not set')
            return False

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')

            # Minimal test request
            response = model.generate_content("Hi",
                                             generation_config={'max_output_tokens': 5})

            if response.text:
                self.add_result('Gemini API', 'AI Services', 'pass',
                              'API key valid, request successful')
                return True
            else:
                self.add_result('Gemini API', 'AI Services', 'warn',
                              'Response empty, but no error')
                return True

        except ImportError:
            self.add_result('Gemini API', 'AI Services', 'warn',
                          'google-generativeai not installed, skipping API test')
            return True
        except Exception as e:
            error_msg = str(e)[:200]
            if 'API_KEY_INVALID' in error_msg or 'invalid' in error_msg.lower():
                self.add_result('Gemini API', 'AI Services', 'fail',
                              f'Invalid API key: {error_msg}')
                return False
            else:
                self.add_result('Gemini API', 'AI Services', 'warn',
                              f'API test failed: {error_msg}')
                return True

    def test_openai_api(self) -> bool:
        """Test OpenAI API with minimal request"""
        if self.skip_connectivity:
            self.add_result('OpenAI API', 'AI Services', 'skip', 'API test skipped')
            return True

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.add_result('OpenAI API', 'AI Services', 'skip', 'Optional API key not set')
            return True

        try:
            import openai

            client = openai.OpenAI(api_key=api_key, timeout=10.0)

            # Minimal test request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )

            if response.choices:
                self.add_result('OpenAI API', 'AI Services', 'pass',
                              'API key valid, request successful')
                return True
            else:
                self.add_result('OpenAI API', 'AI Services', 'warn',
                              'Response empty, but no error')
                return True

        except ImportError:
            self.add_result('OpenAI API', 'AI Services', 'warn',
                          'openai package not installed, skipping API test')
            return True
        except Exception as e:
            error_msg = str(e)[:200]
            if 'invalid' in error_msg.lower() or 'authentication' in error_msg.lower():
                self.add_result('OpenAI API', 'AI Services', 'fail',
                              f'Invalid API key: {error_msg}')
                return False
            else:
                self.add_result('OpenAI API', 'AI Services', 'warn',
                              f'API test failed: {error_msg}')
                return True

    def test_anthropic_api(self) -> bool:
        """Test Anthropic Claude API with minimal request"""
        if self.skip_connectivity:
            self.add_result('Anthropic API', 'AI Services', 'skip', 'API test skipped')
            return True

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            self.add_result('Anthropic API', 'AI Services', 'skip', 'Optional API key not set')
            return True

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key, timeout=10.0)

            # Minimal test request
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hi"}]
            )

            if message.content:
                self.add_result('Anthropic API', 'AI Services', 'pass',
                              'API key valid, request successful')
                return True
            else:
                self.add_result('Anthropic API', 'AI Services', 'warn',
                              'Response empty, but no error')
                return True

        except ImportError:
            self.add_result('Anthropic API', 'AI Services', 'warn',
                          'anthropic package not installed, skipping API test')
            return True
        except Exception as e:
            error_msg = str(e)[:200]
            if 'invalid' in error_msg.lower() or 'authentication' in error_msg.lower():
                self.add_result('Anthropic API', 'AI Services', 'fail',
                              f'Invalid API key: {error_msg}')
                return False
            else:
                self.add_result('Anthropic API', 'AI Services', 'warn',
                              f'API test failed: {error_msg}')
                return True

    # =========================================================================
    # AD PLATFORM VALIDATION
    # =========================================================================

    def validate_meta_credentials(self) -> bool:
        """Validate Meta Marketing API credentials"""
        app_id = os.getenv('META_APP_ID')
        app_secret = os.getenv('META_APP_SECRET')
        access_token = os.getenv('META_ACCESS_TOKEN')

        if not (app_id or app_secret or access_token):
            self.add_result('Meta Ads', 'Ad Platforms', 'skip', 'Meta not configured')
            return True

        all_valid = True

        # Check App ID (numeric)
        if app_id:
            if app_id.isdigit() and len(app_id) >= 10:
                self.add_result('META_APP_ID', 'Ad Platforms', 'pass', 'Valid format')
            else:
                self.add_result('META_APP_ID', 'Ad Platforms', 'fail', 'Invalid format (should be numeric)')
                all_valid = False
        else:
            self.add_result('META_APP_ID', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False

        # Check App Secret (hex string)
        if app_secret:
            if len(app_secret) >= 32:
                self.add_result('META_APP_SECRET', 'Ad Platforms', 'pass', f'Valid format ({len(app_secret)} chars)')
            else:
                self.add_result('META_APP_SECRET', 'Ad Platforms', 'warn', 'Suspiciously short')
        else:
            self.add_result('META_APP_SECRET', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False

        # Check Access Token
        if access_token:
            if len(access_token) >= 50:
                self.add_result('META_ACCESS_TOKEN', 'Ad Platforms', 'pass', f'Valid format ({len(access_token)} chars)')
            else:
                self.add_result('META_ACCESS_TOKEN', 'Ad Platforms', 'warn', 'Suspiciously short')
        else:
            self.add_result('META_ACCESS_TOKEN', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False

        # Check Ad Account ID (optional but recommended)
        ad_account = os.getenv('META_AD_ACCOUNT_ID')
        if ad_account:
            if ad_account.startswith('act_'):
                self.add_result('META_AD_ACCOUNT_ID', 'Ad Platforms', 'pass', 'Valid format')
            else:
                self.add_result('META_AD_ACCOUNT_ID', 'Ad Platforms', 'warn', 'Should start with "act_"')

        return all_valid

    def validate_google_ads_credentials(self) -> bool:
        """Validate Google Ads API credentials"""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
        developer_token = os.getenv('GOOGLE_DEVELOPER_TOKEN')
        customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID')

        if not any([client_id, client_secret, refresh_token, developer_token]):
            self.add_result('Google Ads', 'Ad Platforms', 'skip', 'Google Ads not configured')
            return True

        all_valid = True

        # Check Client ID
        if client_id:
            if client_id.endswith('.apps.googleusercontent.com'):
                self.add_result('GOOGLE_CLIENT_ID', 'Ad Platforms', 'pass', 'Valid format')
            else:
                self.add_result('GOOGLE_CLIENT_ID', 'Ad Platforms', 'warn', 'Should end with .apps.googleusercontent.com')
        else:
            self.add_result('GOOGLE_CLIENT_ID', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False

        # Check other credentials
        if not client_secret:
            self.add_result('GOOGLE_CLIENT_SECRET', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False
        else:
            self.add_result('GOOGLE_CLIENT_SECRET', 'Ad Platforms', 'pass', f'Set ({len(client_secret)} chars)')

        if not refresh_token:
            self.add_result('GOOGLE_REFRESH_TOKEN', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False
        else:
            self.add_result('GOOGLE_REFRESH_TOKEN', 'Ad Platforms', 'pass', f'Set ({len(refresh_token)} chars)')

        if not developer_token:
            self.add_result('GOOGLE_DEVELOPER_TOKEN', 'Ad Platforms', 'fail', 'Missing')
            all_valid = False
        else:
            self.add_result('GOOGLE_DEVELOPER_TOKEN', 'Ad Platforms', 'pass', f'Set ({len(developer_token)} chars)')

        # Check Customer ID (10 digits)
        if customer_id:
            if customer_id.isdigit() and len(customer_id) == 10:
                self.add_result('GOOGLE_ADS_CUSTOMER_ID', 'Ad Platforms', 'pass', 'Valid format')
            else:
                self.add_result('GOOGLE_ADS_CUSTOMER_ID', 'Ad Platforms', 'warn', 'Should be 10 digits')

        return all_valid

    def validate_tiktok_credentials(self) -> bool:
        """Validate TikTok Ads API credentials"""
        access_token = os.getenv('TIKTOK_ACCESS_TOKEN')
        advertiser_id = os.getenv('TIKTOK_ADVERTISER_ID')
        app_id = os.getenv('TIKTOK_APP_ID')

        if not any([access_token, advertiser_id, app_id]):
            self.add_result('TikTok Ads', 'Ad Platforms', 'skip', 'TikTok not configured')
            return True

        if access_token:
            self.add_result('TIKTOK_ACCESS_TOKEN', 'Ad Platforms', 'pass', f'Set ({len(access_token)} chars)')
        else:
            self.add_result('TIKTOK_ACCESS_TOKEN', 'Ad Platforms', 'fail', 'Missing')
            return False

        if advertiser_id:
            self.add_result('TIKTOK_ADVERTISER_ID', 'Ad Platforms', 'pass', 'Set')

        if app_id:
            self.add_result('TIKTOK_APP_ID', 'Ad Platforms', 'pass', 'Set')

        return True

    # =========================================================================
    # MAIN VALIDATION ORCHESTRATOR
    # =========================================================================

    def validate_all(self) -> Dict:
        """Run all validation checks"""

        # 1. DATABASE CONFIGURATION
        print("Validating Database Configuration...")
        self.check_url('DATABASE_URL', 'Database', required=True, schemes=['postgresql', 'postgres'])
        self.check_env_var('POSTGRES_PASSWORD', 'Database', required=True, min_length=16)
        self.check_env_var('POSTGRES_USER', 'Database', required=False)
        self.check_env_var('POSTGRES_DB', 'Database', required=False)

        # Supabase (alternative)
        supabase_url = os.getenv('SUPABASE_URL')
        if supabase_url:
            self.check_url('SUPABASE_URL', 'Database', required=False, schemes=['https'])
            self.check_env_var('SUPABASE_ANON_KEY', 'Database', required=False, min_length=100)
            self.check_env_var('SUPABASE_SERVICE_ROLE_KEY', 'Database', required=False, min_length=100)

        # Test connectivity
        self.test_postgres_connection()

        # 2. CACHE/REDIS CONFIGURATION
        print("Validating Cache Configuration...")
        redis_url = os.getenv('REDIS_URL')
        upstash_url = os.getenv('UPSTASH_REDIS_REST_URL')

        if redis_url:
            self.check_url('REDIS_URL', 'Cache', required=False, schemes=['redis', 'rediss'])
        elif upstash_url:
            self.check_url('UPSTASH_REDIS_REST_URL', 'Cache', required=False, schemes=['https'])
            self.check_env_var('UPSTASH_REDIS_REST_TOKEN', 'Cache', required=False)
        else:
            self.add_result('Redis', 'Cache', 'warn', 'No Redis configured (performance may be limited)')

        self.test_redis_connection()

        # 3. AI API KEYS
        print("Validating AI API Keys...")
        self.check_api_key_format('GEMINI_API_KEY', 'AI Services', 'AI', required=True, min_length=30)
        self.check_api_key_format('OPENAI_API_KEY', 'AI Services', 'sk-', required=False, min_length=40)
        self.check_api_key_format('ANTHROPIC_API_KEY', 'AI Services', 'sk-ant-', required=False, min_length=40)

        # Test AI APIs
        self.test_gemini_api()
        self.test_openai_api()
        self.test_anthropic_api()

        # 4. STORAGE (S3/R2)
        print("Validating Storage Configuration...")
        self.check_env_var('AWS_ACCESS_KEY_ID', 'Storage', required=False, min_length=16)
        self.check_env_var('AWS_SECRET_ACCESS_KEY', 'Storage', required=False, min_length=32)
        self.check_env_var('S3_BUCKET', 'Storage', required=False)
        self.check_env_var('R2_BUCKET', 'Storage', required=False)
        self.check_url('R2_ENDPOINT', 'Storage', required=False, schemes=['https'])

        self.test_s3_access()

        # 5. GCP CONFIGURATION
        print("Validating GCP Configuration...")
        self.check_env_var('GCP_PROJECT_ID', 'GCP', required=False)
        self.check_env_var('GCS_BUCKET_NAME', 'GCP', required=False)
        self.check_env_var('GCP_REGION', 'GCP', required=False)

        # 6. CLOUDFLARE EDGE
        print("Validating Cloudflare Configuration...")
        self.check_env_var('CLOUDFLARE_ACCOUNT_ID', 'Edge', required=False, min_length=32)
        self.check_env_var('CLOUDFLARE_API_TOKEN', 'Edge', required=False, min_length=40)

        # 7. AD PLATFORMS
        print("Validating Ad Platform Credentials...")
        self.validate_meta_credentials()
        self.validate_google_ads_credentials()
        self.validate_tiktok_credentials()

        # 8. SECURITY
        print("Validating Security Configuration...")
        self.check_env_var('JWT_SECRET', 'Security', required=True, min_length=32)
        self.check_env_var('CORS_ORIGINS', 'Security', required=False)

        # 9. FIREBASE (Frontend)
        print("Validating Firebase Configuration...")
        firebase_key = os.getenv('VITE_FIREBASE_API_KEY')
        if firebase_key:
            self.check_api_key_format('VITE_FIREBASE_API_KEY', 'Firebase', 'AI', required=False)
            self.check_env_var('VITE_FIREBASE_PROJECT_ID', 'Firebase', required=False)
            self.check_url('VITE_FIREBASE_AUTH_DOMAIN', 'Firebase', required=False, schemes=['https'])

        # 10. RUNTIME CONFIGURATION
        print("Validating Runtime Configuration...")
        self.check_env_var('NODE_ENV', 'Runtime', required=False)
        self.check_env_var('LOG_LEVEL', 'Runtime', required=False)

        # 11. SERVICE URLS
        print("Validating Service URLs...")
        self.check_url('GATEWAY_API_URL', 'Services', required=False)
        self.check_url('DRIVE_INTEL_URL', 'Services', required=False)
        self.check_url('VIDEO_AGENT_URL', 'Services', required=False)
        self.check_url('ML_SERVICE_URL', 'Services', required=False)
        self.check_url('TITAN_CORE_URL', 'Services', required=False)
        self.check_url('META_PUBLISHER_URL', 'Services', required=False)

        # Generate summary
        return self.generate_summary()

    def generate_summary(self) -> Dict:
        """Generate validation summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == 'pass')
        failed = sum(1 for r in self.results if r.status == 'fail')
        warnings = sum(1 for r in self.results if r.status == 'warn')
        skipped = sum(1 for r in self.results if r.status == 'skip')

        # Group by category
        by_category = {}
        for result in self.results:
            if result.category not in by_category:
                by_category[result.category] = []
            by_category[result.category].append(asdict(result))

        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_checks': total,
                'passed': passed,
                'failed': failed,
                'warnings': warnings,
                'skipped': skipped,
                'success_rate': round(passed / total * 100, 2) if total > 0 else 0,
                'ready_for_deployment': failed == 0
            },
            'by_category': by_category,
            'all_results': [asdict(r) for r in self.results]
        }

    def print_summary(self, summary: Dict):
        """Print human-readable summary"""
        print("\n" + "="*80)
        print("ENVIRONMENT VALIDATION SUMMARY")
        print("="*80)

        s = summary['summary']
        print(f"\nTotal Checks: {s['total_checks']}")
        print(f"✓ Passed:     {s['passed']}")
        print(f"✗ Failed:     {s['failed']}")
        print(f"⚠ Warnings:   {s['warnings']}")
        print(f"⊘ Skipped:    {s['skipped']}")
        print(f"\nSuccess Rate: {s['success_rate']}%")

        if s['ready_for_deployment']:
            print("\n🎉 READY FOR DEPLOYMENT")
        else:
            print("\n❌ NOT READY - Fix failed checks before deployment")

        # Print failed checks
        failed_results = [r for r in self.results if r.status == 'fail']
        if failed_results:
            print("\n" + "="*80)
            print("FAILED CHECKS (must fix):")
            print("="*80)
            for r in failed_results:
                print(f"✗ [{r.category}] {r.name}: {r.message}")

        # Print warnings
        warning_results = [r for r in self.results if r.status == 'warn']
        if warning_results:
            print("\n" + "="*80)
            print("WARNINGS (recommended to fix):")
            print("="*80)
            for r in warning_results:
                print(f"⚠ [{r.category}] {r.name}: {r.message}")

        print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Validate environment configuration for ad platform deployment'
    )
    parser.add_argument(
        '--env-file',
        type=str,
        help='Path to .env file (optional, will use system env vars if not provided)'
    )
    parser.add_argument(
        '--skip-connectivity',
        action='store_true',
        help='Skip connectivity tests (API calls, DB connections, etc.)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Write JSON output to file'
    )

    args = parser.parse_args()

    # Run validation
    validator = EnvironmentValidator(
        env_file=args.env_file,
        skip_connectivity=args.skip_connectivity
    )

    summary = validator.validate_all()

    # Output results
    if args.json or args.output:
        json_output = json.dumps(summary, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"Results written to {args.output}")
        else:
            print(json_output)
    else:
        validator.print_summary(summary)

    # Exit code based on validation result
    if summary['summary']['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
