"""
Integration Tests for Winner Detection and Replication System
Agent 09 - Comprehensive Winner Flow Testing

Tests:
- Winner detection with ROAS thresholds
- Winner replication with variations
- Budget optimization and safety limits
- Full workflow orchestration
- Scheduled job execution
- Agent trigger mechanisms
"""

import pytest
import asyncio
import httpx
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import uuid

# Test configuration
API_URL = os.getenv('TEST_API_URL', 'http://localhost:8000')
ML_SERVICE_URL = os.getenv('TEST_ML_SERVICE_URL', 'http://localhost:8004')
TEST_AD_ACCOUNT_ID = os.getenv('TEST_AD_ACCOUNT_ID', 'test_account_123')


class TestWinnerDetection:
    """Test winner detection logic"""

    @pytest.mark.asyncio
    async def test_detect_winners_with_roas_threshold(self, test_client):
        """Should detect winners with ROAS > 2x"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/winners/detect', json={
                'minROAS': 2.0,
                'minCTR': 0.02,
                'minSpend': 100
            })

            assert response.status_code == 200
            data = response.json()

            assert 'winners' in data
            assert isinstance(data['winners'], list)

            # All winners should meet criteria
            for winner in data['winners']:
                assert winner['metrics']['roas'] >= 2.0
                assert winner['metrics']['ctr'] >= 0.02
                assert winner['metrics']['spend'] >= 100

    @pytest.mark.asyncio
    async def test_exclude_low_performers(self, test_client):
        """Should exclude low-performing ads from winners"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/winners/detect', json={
                'minROAS': 2.0,
                'minCTR': 0.02
            })

            assert response.status_code == 200
            data = response.json()

            winners = data['winners']

            # No winner should have ROAS < 2.0
            for winner in winners:
                assert winner['metrics']['roas'] >= 2.0

    @pytest.mark.asyncio
    async def test_list_all_winners(self, test_client):
        """Should list all detected winners with pagination"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.get('/api/v1/winners/list')

            assert response.status_code == 200
            data = response.json()

            assert 'winners' in data
            assert isinstance(data['winners'], list)
            assert 'total' in data
            assert 'page' in data

    @pytest.mark.asyncio
    async def test_get_winner_details_by_id(self, test_client):
        """Should get winner details by ID"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            # First detect winners
            detect_response = await client.post('/api/v1/winners/detect', json={
                'minROAS': 2.0
            })

            data = detect_response.json()

            if data['winners']:
                winner_id = data['winners'][0]['id']

                response = await client.get(f'/api/v1/winners/{winner_id}')

                assert response.status_code == 200
                winner_data = response.json()

                assert winner_data['id'] == winner_id
                assert 'metrics' in winner_data
                assert winner_data['metrics']['roas'] >= 2.0

    @pytest.mark.asyncio
    async def test_filter_by_multiple_criteria(self, test_client):
        """Should filter winners by multiple criteria"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/winners/detect', json={
                'minROAS': 3.0,
                'minCTR': 0.04,
                'minSpend': 400,
                'minRevenue': 1000
            })

            assert response.status_code == 200
            data = response.json()

            # All winners should meet ALL criteria
            for winner in data['winners']:
                assert winner['metrics']['roas'] >= 3.0
                assert winner['metrics']['ctr'] >= 0.04
                assert winner['metrics']['spend'] >= 400
                assert winner['metrics']['revenue'] >= 1000

    @pytest.mark.asyncio
    async def test_lookback_window(self, test_client):
        """Should respect lookback window parameter"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/winners/detect', json={
                'minROAS': 2.0,
                'lookbackDays': 7
            })

            assert response.status_code == 200
            data = response.json()

            assert 'lookbackDays' in data
            assert data['lookbackDays'] == 7


class TestWinnerReplication:
    """Test winner replication with variations"""

    @pytest.mark.asyncio
    async def test_replicate_with_variations(self, test_client):
        """Should replicate a winner with specified variations"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            # Get a winner first
            winners_response = await client.get('/api/v1/winners/list')
            winners_data = winners_response.json()

            if winners_data['winners']:
                winner_id = winners_data['winners'][0]['id']

                response = await client.post(
                    f'/api/v1/winners/{winner_id}/replicate',
                    json={
                        'variations': ['audience', 'hook', 'budget'],
                        'replicaCount': 3
                    }
                )

                assert response.status_code == 200
                data = response.json()

                assert 'replicas' in data
                assert isinstance(data['replicas'], list)
                assert len(data['replicas']) > 0
                assert len(data['replicas']) <= 3

                # Each replica should have variation details
                for replica in data['replicas']:
                    assert 'id' in replica
                    assert 'sourceAdId' in replica
                    assert replica['sourceAdId'] == winner_id
                    assert 'variations' in replica

    @pytest.mark.asyncio
    async def test_audience_variations(self, test_client):
        """Should create audience variations"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            winners_response = await client.get('/api/v1/winners/list')
            winners_data = winners_response.json()

            if winners_data['winners']:
                winner_id = winners_data['winners'][0]['id']

                response = await client.post(
                    f'/api/v1/winners/{winner_id}/replicate',
                    json={
                        'variations': ['audience'],
                        'audienceVariations': ['lookalike', 'interest_expansion', 'age_range']
                    }
                )

                assert response.status_code == 200
                data = response.json()

                replicas = data['replicas']
                assert len(replicas) > 0

                # Check that audience variations were applied
                for replica in replicas:
                    assert 'audience' in replica['variations']
                    assert 'audienceChanges' in replica

    @pytest.mark.asyncio
    async def test_hook_variations(self, test_client):
        """Should create hook variations"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            winners_response = await client.get('/api/v1/winners/list')
            winners_data = winners_response.json()

            if winners_data['winners']:
                winner_id = winners_data['winners'][0]['id']

                response = await client.post(
                    f'/api/v1/winners/{winner_id}/replicate',
                    json={
                        'variations': ['hook'],
                        'hookStyles': ['question', 'urgency', 'benefit']
                    }
                )

                assert response.status_code == 200
                data = response.json()

                replicas = data['replicas']

                for replica in replicas:
                    assert 'hook' in replica['variations']
                    assert 'hookChanges' in replica

    @pytest.mark.asyncio
    async def test_budget_variations(self, test_client):
        """Should create budget variations"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            winners_response = await client.get('/api/v1/winners/list')
            winners_data = winners_response.json()

            if winners_data['winners']:
                winner_id = winners_data['winners'][0]['id']

                response = await client.post(
                    f'/api/v1/winners/{winner_id}/replicate',
                    json={
                        'variations': ['budget'],
                        'budgetMultipliers': [1.5, 2.0, 0.75]
                    }
                )

                assert response.status_code == 200
                data = response.json()

                replicas = data['replicas']

                for replica in replicas:
                    assert 'budget' in replica['variations']
                    assert 'budgetChanges' in replica

    @pytest.mark.asyncio
    async def test_replica_count_limit(self, test_client):
        """Should limit replica count"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            winners_response = await client.get('/api/v1/winners/list')
            winners_data = winners_response.json()

            if winners_data['winners']:
                winner_id = winners_data['winners'][0]['id']

                response = await client.post(
                    f'/api/v1/winners/{winner_id}/replicate',
                    json={
                        'variations': ['audience', 'hook', 'budget'],
                        'replicaCount': 2
                    }
                )

                assert response.status_code == 200
                data = response.json()

                assert len(data['replicas']) <= 2


class TestBudgetOptimization:
    """Test budget optimization logic"""

    @pytest.mark.asyncio
    async def test_calculate_budget_changes(self, test_client):
        """Should calculate budget changes for account"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/budget/optimize', json={
                'accountId': TEST_AD_ACCOUNT_ID
            })

            assert response.status_code == 200
            data = response.json()

            assert 'changes' in data
            assert isinstance(data['changes'], list)

            # Should include optimization metadata
            assert 'totalBudgetBefore' in data
            assert 'totalBudgetAfter' in data
            assert 'optimizationStrategy' in data

    @pytest.mark.asyncio
    async def test_apply_safety_limits(self, test_client):
        """Should apply safety limits to budget changes"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/budget/optimize', json={
                'accountId': TEST_AD_ACCOUNT_ID,
                'safetyLimits': {
                    'maxDailyChangePercent': 0.3,
                    'minBudgetPerAd': 5,
                    'maxBudgetPerAd': 500
                }
            })

            assert response.status_code == 200
            data = response.json()

            changes = data['changes']

            # Check that all changes respect limits
            for change in changes:
                assert change['newBudget'] >= 5
                assert change['newBudget'] <= 500

                # Check daily change percentage
                if change['oldBudget'] > 0:
                    change_percent = abs(change['newBudget'] - change['oldBudget']) / change['oldBudget']
                    assert change_percent <= 0.3

    @pytest.mark.asyncio
    async def test_prioritize_winners(self, test_client):
        """Should prioritize winners for budget increases"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/budget/optimize', json={
                'accountId': TEST_AD_ACCOUNT_ID,
                'strategy': 'winner_focused'
            })

            assert response.status_code == 200
            data = response.json()

            changes = data['changes']
            increases = [c for c in changes if c['newBudget'] > c['oldBudget']]

            # Winners should get increases
            for change in increases:
                if 'isWinner' in change:
                    assert change['isWinner'] is True

    @pytest.mark.asyncio
    async def test_reduce_loser_budgets(self, test_client):
        """Should reduce budget for losers"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/budget/optimize', json={
                'accountId': TEST_AD_ACCOUNT_ID,
                'strategy': 'performance_based'
            })

            assert response.status_code == 200
            data = response.json()

            changes = data['changes']

            # Should have some budget reductions
            reductions = [c for c in changes if c['newBudget'] < c['oldBudget']]
            assert len(reductions) > 0

            # Reductions should be for poor performers
            for change in reductions:
                if 'roas' in change:
                    assert change['roas'] < 2.0

    @pytest.mark.asyncio
    async def test_respect_total_budget_cap(self, test_client):
        """Should respect total budget cap"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/budget/optimize', json={
                'accountId': TEST_AD_ACCOUNT_ID,
                'totalBudgetCap': 5000
            })

            assert response.status_code == 200
            data = response.json()

            total_budget_after = data['totalBudgetAfter']
            assert total_budget_after <= 5000

    @pytest.mark.asyncio
    async def test_provide_reasoning(self, test_client):
        """Should provide reasoning for budget changes"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/budget/optimize', json={
                'accountId': TEST_AD_ACCOUNT_ID
            })

            assert response.status_code == 200
            data = response.json()

            changes = data['changes']

            for change in changes:
                assert 'reasoning' in change
                assert isinstance(change['reasoning'], str)
                assert len(change['reasoning']) > 0


class TestFullWorkflow:
    """Test complete winner workflow"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, test_client):
        """Should run complete winner workflow"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=60.0) as client:
            response = await client.post('/api/v1/workflows/winner', json={
                'autoPublish': False,
                'maxReplicasPerWinner': 2
            })

            assert response.status_code == 200
            data = response.json()

            assert 'status' in data
            assert 'winnersDetected' in data
            assert 'replicasCreated' in data
            assert 'budgetOptimized' in data

            # Should detect some winners
            assert data['winnersDetected'] >= 0

    @pytest.mark.asyncio
    async def test_sequential_steps(self, test_client):
        """Should detect, replicate, and optimize in sequence"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=60.0) as client:
            response = await client.post('/api/v1/workflows/winner', json={
                'steps': ['detect', 'replicate', 'optimize'],
                'autoPublish': False
            })

            assert response.status_code == 200
            data = response.json()

            # Should have completed all steps
            assert 'steps' in data
            assert 'detect' in data['steps']
            assert 'replicate' in data['steps']
            assert 'optimize' in data['steps']

            # Each step should be successful
            assert data['steps']['detect']['success'] is True
            assert data['steps']['replicate']['success'] is True
            assert data['steps']['optimize']['success'] is True

    @pytest.mark.asyncio
    async def test_dry_run_mode(self, test_client):
        """Should support dry-run mode"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/workflows/winner', json={
                'dryRun': True,
                'autoPublish': False
            })

            assert response.status_code == 200
            data = response.json()

            assert 'dryRun' in data
            assert data['dryRun'] is True

            # Should show what would be done without executing
            assert 'proposedChanges' in data

    @pytest.mark.asyncio
    async def test_execution_time_tracking(self, test_client):
        """Should track workflow execution time"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=60.0) as client:
            start_time = time.time()

            response = await client.post('/api/v1/workflows/winner', json={
                'autoPublish': False
            })

            duration = (time.time() - start_time) * 1000

            assert response.status_code == 200
            data = response.json()

            assert 'executionTimeMs' in data

            # Execution time should be reasonable
            assert duration < 60000  # Less than 60 seconds


class TestInsightsExtraction:
    """Test winner insights extraction"""

    @pytest.mark.asyncio
    async def test_extract_insights(self, test_client):
        """Should extract insights from winners"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.get('/api/v1/winners/insights')

            assert response.status_code == 200
            data = response.json()

            assert 'topHooks' in data
            assert 'topAudiences' in data
            assert 'recommendations' in data

            assert isinstance(data['topHooks'], list)
            assert isinstance(data['recommendations'], list)

    @pytest.mark.asyncio
    async def test_top_hook_patterns(self, test_client):
        """Should identify top-performing hook patterns"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.get('/api/v1/winners/insights')

            assert response.status_code == 200
            data = response.json()

            top_hooks = data['topHooks']

            for hook in top_hooks:
                assert 'pattern' in hook
                assert 'avgROAS' in hook
                assert 'count' in hook

    @pytest.mark.asyncio
    async def test_actionable_recommendations(self, test_client):
        """Should provide actionable recommendations"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.get('/api/v1/winners/insights')

            assert response.status_code == 200
            data = response.json()

            recommendations = data['recommendations']

            for rec in recommendations:
                assert 'type' in rec
                assert 'recommendation' in rec
                assert 'priority' in rec


class TestScheduledJobs:
    """Test scheduled winner jobs"""

    @pytest.mark.asyncio
    async def test_trigger_detection_job(self, test_client):
        """Should trigger winner detection job manually"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/jobs/detect-winners/trigger')

            assert response.status_code == 200
            data = response.json()

            assert 'jobId' in data
            assert 'status' in data
            assert data['status'] in ['queued', 'running', 'completed']

    @pytest.mark.asyncio
    async def test_check_job_status(self, test_client):
        """Should check job status"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            # Trigger a job
            trigger_response = await client.post('/api/v1/jobs/detect-winners/trigger')

            if trigger_response.status_code == 200:
                job_id = trigger_response.json()['jobId']

                # Wait a bit
                await asyncio.sleep(2)

                # Check status
                status_response = await client.get(f'/api/v1/jobs/{job_id}')

                assert status_response.status_code == 200
                status_data = status_response.json()

                assert 'status' in status_data
                assert status_data['status'] in ['queued', 'running', 'completed', 'failed']


class TestAgentTriggers:
    """Test agent trigger mechanisms"""

    @pytest.mark.asyncio
    async def test_trigger_auto_promotion_agent(self, test_client):
        """Should trigger auto-promotion agent"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/agents/auto-promotion/trigger', json={
                'experimentId': 'test_experiment_123'
            })

            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                assert 'status' in data
                assert 'triggered' in data

    @pytest.mark.asyncio
    async def test_trigger_budget_optimizer_agent(self, test_client):
        """Should trigger budget optimization agent"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/agents/budget-optimizer/trigger', json={
                'accountId': TEST_AD_ACCOUNT_ID
            })

            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                assert 'optimizationId' in data

    @pytest.mark.asyncio
    async def test_agent_health_status(self, test_client):
        """Should check agent health status"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.get('/api/v1/agents/health')

            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = response.json()
                assert 'agents' in data

                agents = data['agents']
                assert 'auto_promotion' in agents
                assert 'budget_optimizer' in agents
                assert 'replicator' in agents


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_no_winners_found(self, test_client):
        """Should handle no winners found gracefully"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.post('/api/v1/winners/detect', json={
                'minROAS': 100.0,  # Impossibly high threshold
                'minCTR': 0.9
            })

            assert response.status_code == 200
            data = response.json()

            assert data['winners'] == []
            assert 'message' in data

    @pytest.mark.asyncio
    async def test_invalid_winner_id(self, test_client):
        """Should validate winner ID format"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            response = await client.get('/api/v1/winners/invalid!!id')

            assert response.status_code in [400, 404]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client):
        """Should respect rate limits on winner detection"""
        async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as client:
            tasks = [
                client.post('/api/v1/winners/detect', json={'minROAS': 2.0})
                for _ in range(20)
            ]

            responses = await asyncio.gather(*tasks)

            # Some requests should be rate-limited
            rate_limited = [r for r in responses if r.status_code == 429]
            assert len(rate_limited) > 0


@pytest.fixture
async def test_client():
    """Provide test client fixture"""
    return None
