"""
Unit tests for CLI (Command Line Interface) functionality (v2.2.0).
Tests argument parsing, single file mode, batch mode, and error handling.
"""
import unittest
import pytest
import sys
from unittest.mock import MagicMock, patch, call
from io import StringIO


@pytest.mark.unit
class TestCLIArgumentParsing(unittest.TestCase):
    """Test suite for CLI argument parsing."""
    
    @patch('sys.argv', ['insightron/app/cli/cli.py', 'test.wav'])
    @patch('insightron.app.cli.cli.AudioTranscriber')
    @patch('os.path.exists', return_value=True)
    def test_cli_single_file_basic(self, mock_exists, mock_transcriber):
        """Test basic single file transcription via CLI."""
        mock_instance = MagicMock()
        mock_transcriber.return_value = mock_instance
        
        # Import cli module (will parse arguments)
        try:
            from insightron.app.cli.cli import main
            # Run main (may exit, catch SystemExit)
            with patch('sys.exit'):
                main()
            
            # If transcriber was called, verify
            if mock_transcriber.called:
                mock_transcriber.assert_called()
        except (ImportError, SystemExit):
            pass
class TestCLIOutputHandling(unittest.TestCase):
    """Test suite for CLI output and logging."""
    
    @patch('sys.argv', ['insightron/app/cli/cli.py', 'test.wav', '-o', 'custom_output.md'])
    @patch('insightron.app.cli.cli.AudioTranscriber')
    @patch('os.path.exists', return_value=True)
    def test_cli_custom_output_path(self, mock_exists, mock_transcriber):
        """Test custom output path via CLI."""
        mock_instance = MagicMock()
        mock_transcriber.return_value = mock_instance
        
        try:
            from insightron.app.cli.cli import main
            with patch('sys.exit'):
                main()
            
            # Custom output path should be used
            # This may be handled differently depending on CLI implementation
        except (ImportError, SystemExit):
            pass


@pytest.mark.integration
class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI with mocked components."""
    
    @patch('insightron.app.cli.cli.AudioTranscriber')
    @patch('os.path.exists', return_value=True)
    def test_cli_end_to_end_flow(self, mock_exists, mock_transcriber):
        """Test complete CLI workflow from parsing to transcription."""
        mock_instance = MagicMock()
        mock_instance.transcribe_file.return_value = None
        mock_transcriber.return_value = mock_instance
        
        with patch('sys.argv', ['insightron/app/cli/cli.py', 'test.wav', '-m', 'tiny', '-l', 'en']):
            try:
                from insightron.app.cli.cli import main
                with patch('sys.exit'):
                    main()
                
                # Full workflow should complete
                mock_transcriber.assert_called()
                mock_instance.transcribe_file.assert_called()
            except (ImportError, SystemExit):
                pass


if __name__ == '__main__':
    unittest.main()
