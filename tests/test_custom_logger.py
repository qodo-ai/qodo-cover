import logging

from unittest.mock import patch

import pytest

from cover_agent.custom_logger import CustomLogger


class TestCustomLogger:

    @pytest.mark.parametrize(
        "generate_log_files,should_exist",
        [
            (True, True),
            (False, False),
        ],
    )
    def test_logger_file_creation(self, generate_log_files, should_exist):
        """
        Test that log files are only created when generate_log_files=True.

        This test mocks the FileHandler to verify whether it is called
        based on the generate_log_files flag.

        Args:
            generate_log_files (bool): Flag indicating whether logs should be generated.
            should_exist (bool): Expected outcome for whether the file handler should be created.
        """
        with patch("logging.FileHandler") as mock_handler:
            # Configure mock handler with required attributes
            mock_instance = mock_handler.return_value
            mock_instance.level = logging.INFO
            mock_instance.formatter = None

            # Remove any existing logger to ensure clean state
            logging.Logger.manager.loggerDict.pop("test_logger", None)

            # Create logger and write a test message
            logger = CustomLogger.get_logger("test_logger", generate_log_files=generate_log_files)
            logger.info("Test message")

            # Check if FileHandler was called as expected
            if should_exist:
                mock_handler.assert_called_once()
            else:
                mock_handler.assert_not_called()
