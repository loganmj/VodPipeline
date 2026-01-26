"""Unit tests for JobState and JobStateManager."""
import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.state.job_state import JobState, JobStateManager


class TestJobState(unittest.TestCase):
    """Test JobState data class."""

    def test_job_state_creation(self):
        """Test basic JobState creation."""
        now = datetime.now(timezone.utc)
        state = JobState(
            job_id="test-id",
            file_name="test.mp4",
            stage="Processing",
            percent=50,
            started_at=now,
            last_updated_at=now,
            error_message=None,
            is_running=True
        )
        
        self.assertEqual(state.job_id, "test-id")
        self.assertEqual(state.file_name, "test.mp4")
        self.assertEqual(state.stage, "Processing")
        self.assertEqual(state.percent, 50)
        self.assertTrue(state.is_running)
        self.assertIsNone(state.error_message)

    def test_job_state_to_dict(self):
        """Test JobState to_dict serialization."""
        now = datetime.now(timezone.utc)
        state = JobState(
            job_id="test-id",
            file_name="test.mp4",
            stage="Processing",
            percent=50,
            started_at=now,
            last_updated_at=now,
            error_message=None,
            is_running=True
        )
        
        result = state.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["jobId"], "test-id")
        self.assertEqual(result["fileName"], "test.mp4")
        self.assertEqual(result["stage"], "Processing")
        self.assertEqual(result["percent"], 50)
        self.assertEqual(result["timestamp"], now.isoformat().replace('+00:00', 'Z'))
        self.assertIsNone(result["errorMessage"])


class TestJobStateManager(unittest.TestCase):
    """Test JobStateManager functionality."""

    def setUp(self):
        """Reset state manager before each test."""
        # Get singleton instance and reset to idle
        manager = JobStateManager()
        manager.reset_to_idle()

    def test_singleton_pattern(self):
        """Test that JobStateManager is a singleton."""
        manager1 = JobStateManager()
        manager2 = JobStateManager()
        self.assertIs(manager1, manager2)

    def test_initial_state_is_idle(self):
        """Test that initial state is idle."""
        manager = JobStateManager()
        state = manager.get_state()
        
        self.assertIsNone(state.job_id)
        self.assertIsNone(state.file_name)
        self.assertEqual(state.stage, "Idle")
        self.assertEqual(state.percent, 0)
        self.assertFalse(state.is_running)
        self.assertIsNone(state.error_message)

    def test_start_job(self):
        """Test starting a job."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        
        state = manager.get_state()
        self.assertEqual(state.job_id, "test-id")
        self.assertEqual(state.file_name, "test.mp4")
        self.assertEqual(state.stage, "Starting")
        self.assertEqual(state.percent, 0)
        self.assertTrue(state.is_running)
        self.assertIsNone(state.error_message)
        self.assertIsNotNone(state.started_at)

    def test_update_stage(self):
        """Test updating stage."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        
        manager.update_stage("Silence Removal", 10)
        
        state = manager.get_state()
        self.assertEqual(state.stage, "Silence Removal")
        self.assertEqual(state.percent, 10)

    def test_update_progress(self):
        """Test updating progress."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        manager.update_stage("Silence Removal", 10)
        
        manager.update_progress(25)
        
        state = manager.get_state()
        self.assertEqual(state.percent, 25)
        self.assertEqual(state.stage, "Silence Removal")  # Stage should remain unchanged

    def test_complete_job(self):
        """Test completing a job."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        
        manager.complete_job()
        
        state = manager.get_state()
        self.assertEqual(state.stage, "Completed")
        self.assertEqual(state.percent, 100)
        self.assertFalse(state.is_running)

    def test_fail_job(self):
        """Test failing a job."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        manager.update_stage("Processing", 50)
        
        manager.fail_job("Test error message")
        
        state = manager.get_state()
        self.assertEqual(state.stage, "Failed")
        self.assertEqual(state.error_message, "Test error message")
        self.assertFalse(state.is_running)

    def test_reset_to_idle(self):
        """Test resetting to idle state."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        manager.update_stage("Processing", 50)
        
        manager.reset_to_idle()
        
        state = manager.get_state()
        self.assertIsNone(state.job_id)
        self.assertIsNone(state.file_name)
        self.assertEqual(state.stage, "Idle")
        self.assertEqual(state.percent, 0)
        self.assertFalse(state.is_running)
        self.assertIsNone(state.error_message)

    def test_thread_safety(self):
        """Test that state manager is thread-safe."""
        manager = JobStateManager()
        manager.start_job("test-id", "test.mp4")
        
        def update_progress():
            for i in range(100):
                manager.update_progress(i)
                time.sleep(0.001)
        
        def update_stage():
            stages = ["Stage 1", "Stage 2", "Stage 3"]
            for stage in stages:
                for i in range(33):
                    manager.update_stage(stage, i)
                    time.sleep(0.001)
        
        # Run multiple threads updating state
        threads = [
            threading.Thread(target=update_progress),
            threading.Thread(target=update_stage)
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Should not crash and state should be valid
        state = manager.get_state()
        self.assertIsInstance(state, JobState)
        self.assertTrue(state.is_running)


if __name__ == '__main__':
    unittest.main()
