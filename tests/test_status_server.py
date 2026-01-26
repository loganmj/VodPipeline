"""Unit tests for Status Server."""
import unittest
import sys
from pathlib import Path
import json
import urllib.request
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.api.status_server import StatusServer
from bin.state.job_state import JobStateManager


class TestStatusServer(unittest.TestCase):
    """Test StatusServer functionality."""

    @classmethod
    def setUpClass(cls):
        """Start the server once for all tests."""
        cls.port = 8888  # Use a different port to avoid conflicts
        cls.server = StatusServer(port=cls.port, host="127.0.0.1")
        cls.server.start()
        # Give the server time to start
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        """Stop the server after all tests."""
        cls.server.stop()

    def setUp(self):
        """Reset state before each test."""
        manager = JobStateManager()
        manager.reset_to_idle()

    def test_server_starts(self):
        """Test that server starts successfully."""
        self.assertIsNotNone(self.server.server)
        self.assertIsNotNone(self.server.thread)
        self.assertTrue(self.server.thread.is_alive())

    def test_status_endpoint_returns_idle(self):
        """Test that /status returns idle state when no job is running."""
        url = f"http://127.0.0.1:{self.port}/status"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            content_type = response.headers.get('Content-Type')
            self.assertEqual(content_type, 'application/json')
            
            data = json.loads(response.read().decode('utf-8'))
            
            self.assertIsNone(data["jobId"])
            self.assertIsNone(data["fileName"])
            self.assertEqual(data["stage"], "Idle")
            self.assertEqual(data["percent"], 0)
            self.assertIsNone(data["errorMessage"])
            self.assertIn("timestamp", data)

    def test_status_endpoint_returns_running_job(self):
        """Test that /status returns current job state when running."""
        manager = JobStateManager()
        manager.start_job("test-job-id", "test-video.mp4")
        manager.update_stage("Silence Removal", 42)
        
        url = f"http://127.0.0.1:{self.port}/status"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            
            data = json.loads(response.read().decode('utf-8'))
            
            self.assertEqual(data["jobId"], "test-job-id")
            self.assertEqual(data["fileName"], "test-video.mp4")
            self.assertEqual(data["stage"], "Silence Removal")
            self.assertEqual(data["percent"], 42)
            self.assertIsNone(data["errorMessage"])
            self.assertIn("timestamp", data)

    def test_status_endpoint_returns_failed_job(self):
        """Test that /status returns failed state."""
        manager = JobStateManager()
        manager.start_job("test-job-id", "test-video.mp4")
        manager.update_stage("Processing", 50)
        manager.fail_job("Test error occurred")
        
        url = f"http://127.0.0.1:{self.port}/status"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            
            data = json.loads(response.read().decode('utf-8'))
            
            self.assertEqual(data["jobId"], "test-job-id")
            self.assertEqual(data["fileName"], "test-video.mp4")
            self.assertEqual(data["stage"], "Failed")
            self.assertEqual(data["errorMessage"], "Test error occurred")
            self.assertIn("timestamp", data)

    def test_status_endpoint_returns_completed_as_idle(self):
        """Test that /status returns idle when job is completed."""
        manager = JobStateManager()
        manager.start_job("test-job-id", "test-video.mp4")
        manager.complete_job()
        
        url = f"http://127.0.0.1:{self.port}/status"
        
        with urllib.request.urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            
            data = json.loads(response.read().decode('utf-8'))
            
            # Completed and not running should show as Idle
            self.assertIsNone(data["jobId"])
            self.assertIsNone(data["fileName"])
            self.assertEqual(data["stage"], "Idle")
            self.assertEqual(data["percent"], 0)
            self.assertIsNone(data["errorMessage"])

    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        url = f"http://127.0.0.1:{self.port}/invalid"
        
        try:
            urllib.request.urlopen(url, timeout=5)
            self.fail("Should have raised HTTPError")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


if __name__ == '__main__':
    unittest.main()
