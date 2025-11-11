"""
Integration smoke tests
Tests basic functionality of services working together
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDriveIntelIntegration:
    """Integration tests for Drive Intel service"""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        from services.drive_intel.src.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'drive-intel'
    
    def test_ingest_local_folder(self, client):
        """Test local folder ingestion"""
        payload = {
            'path': '/test/videos',
            'recursive': True
        }
        response = client.post("/ingest/local/folder", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'asset_id' in data
        assert data['status'] == 'processing'
    
    def test_list_assets(self, client):
        """Test listing assets"""
        response = client.get("/assets")
        assert response.status_code == 200
        data = response.json()
        assert 'assets' in data
        assert 'count' in data
    
    def test_get_asset_clips_not_found(self, client):
        """Test getting clips for non-existent asset"""
        response = client.get("/assets/nonexistent-id/clips")
        assert response.status_code == 404
    
    def test_ingest_and_get_clips(self, client):
        """Test full flow: ingest -> wait -> get clips"""
        import time
        
        # Ingest
        payload = {'path': '/test/video.mp4', 'recursive': False}
        response = client.post("/ingest/local/folder", json=payload)
        assert response.status_code == 200
        asset_id = response.json()['asset_id']
        
        # Wait for processing
        time.sleep(3)
        
        # Get clips
        response = client.get(f"/assets/{asset_id}/clips?ranked=true&top=5")
        assert response.status_code == 200
        data = response.json()
        assert data['asset_id'] == asset_id
        assert 'clips' in data
        assert data['ranked'] == True


class TestVideoAgentIntegration:
    """Integration tests for Video Agent service"""
    
    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        from services.video_agent.src.index import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'video-agent'
    
    def test_render_remix(self, client):
        """Test render remix endpoint"""
        payload = {
            'storyboard': [
                {
                    'clip_id': 'clip1',
                    'asset_id': 'asset1',
                    'start_time': 0.0,
                    'end_time': 5.0,
                    'transition': 'fade'
                }
            ],
            'output_format': 'mp4',
            'resolution': '1920x1080',
            'fps': 30,
            'compliance_check': True
        }
        
        response = client.post("/render/remix", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert 'job_id' in data
        assert data['status'] == 'queued'
    
    def test_get_render_status(self, client):
        """Test getting render job status"""
        # First create a job
        payload = {
            'storyboard': [
                {
                    'clip_id': 'clip1',
                    'asset_id': 'asset1',
                    'start_time': 0.0,
                    'end_time': 5.0
                }
            ],
            'compliance_check': False
        }
        
        response = client.post("/render/remix", json=payload)
        job_id = response.json()['job_id']
        
        # Check status
        response = client.get(f"/render/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data['job_id'] == job_id
    
    def test_list_render_jobs(self, client):
        """Test listing render jobs"""
        response = client.get("/render/jobs")
        assert response.status_code == 200
        data = response.json()
        assert 'jobs' in data
        assert 'count' in data
    
    def test_compliance_check_failure(self, client):
        """Test compliance check rejects invalid content"""
        # Create storyboard with too many clips
        payload = {
            'storyboard': [
                {
                    'clip_id': f'clip{i}',
                    'asset_id': 'asset1',
                    'start_time': i * 5.0,
                    'end_time': (i + 1) * 5.0
                }
                for i in range(25)  # Exceeds max of 20
            ],
            'compliance_check': True
        }
        
        response = client.post("/render/remix", json=payload)
        assert response.status_code == 400
        assert 'compliance' in response.json()['detail'].lower()


class TestEndToEndFlow:
    """End-to-end integration tests"""
    
    def test_ingest_rank_render_flow(self):
        """Test complete flow: ingest -> rank -> render"""
        from services.drive_intel.src.main import app as drive_app
        from services.video_agent.src.index import app as video_app
        import time
        
        drive_client = TestClient(drive_app)
        video_client = TestClient(video_app)
        
        # Step 1: Ingest video
        response = drive_client.post(
            "/ingest/local/folder",
            json={'path': '/test/video.mp4', 'recursive': False}
        )
        assert response.status_code == 200
        asset_id = response.json()['asset_id']
        
        # Step 2: Wait for processing
        time.sleep(3)
        
        # Step 3: Get ranked clips
        response = drive_client.get(f"/assets/{asset_id}/clips?ranked=true&top=3")
        assert response.status_code == 200
        clips = response.json()['clips']
        assert len(clips) > 0
        
        # Step 4: Create storyboard from top clips
        storyboard = [
            {
                'clip_id': clip['clip_id'],
                'asset_id': clip['asset_id'],
                'start_time': clip['start_time'],
                'end_time': clip['end_time'],
                'transition': 'fade'
            }
            for clip in clips[:2]
        ]
        
        # Step 5: Render video
        response = video_client.post(
            "/render/remix",
            json={
                'storyboard': storyboard,
                'output_format': 'mp4',
                'compliance_check': True
            }
        )
        assert response.status_code == 200
        job_id = response.json()['job_id']
        
        # Step 6: Verify job was created
        response = video_client.get(f"/render/status/{job_id}")
        assert response.status_code == 200
        assert response.json()['job_id'] == job_id


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
