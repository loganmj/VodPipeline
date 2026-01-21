"""Unit tests for configuration module."""
import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bin.config import (
    SILENCE_NOISE_DB,
    SILENCE_MIN_DURATION,
    MAX_HIGHLIGHTS,
    MIN_HIGHLIGHT_DURATION,
    MAX_HIGHLIGHT_DURATION,
    FFMPEG_BIN,
    SCENEDETECT_BIN,
)


class TestConfig(unittest.TestCase):
    """Test configuration values are valid."""

    def test_silence_detection_params(self):
        """Test silence detection parameters are within valid ranges."""
        self.assertIsInstance(SILENCE_NOISE_DB, (int, float))
        self.assertLess(SILENCE_NOISE_DB, 0, "Silence noise threshold should be negative")
        self.assertGreater(SILENCE_MIN_DURATION, 0, "Minimum duration should be positive")

    def test_highlight_extraction_params(self):
        """Test highlight extraction parameters are valid."""
        self.assertIsInstance(MAX_HIGHLIGHTS, int)
        self.assertGreater(MAX_HIGHLIGHTS, 0, "Maximum highlights should be positive")
        self.assertGreater(MIN_HIGHLIGHT_DURATION, 0, "Min highlight duration should be positive")
        self.assertGreater(MAX_HIGHLIGHT_DURATION, MIN_HIGHLIGHT_DURATION, 
                          "Max duration should be greater than min duration")

    def test_tool_binaries_defined(self):
        """Test that tool binaries are defined."""
        self.assertIsInstance(FFMPEG_BIN, str)
        self.assertIsInstance(SCENEDETECT_BIN, str)
        self.assertTrue(len(FFMPEG_BIN) > 0, "FFmpeg binary should be defined")
        self.assertTrue(len(SCENEDETECT_BIN) > 0, "SceneDetect binary should be defined")


if __name__ == '__main__':
    unittest.main()
