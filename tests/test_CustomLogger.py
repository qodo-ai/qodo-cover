import logging
import os

import pytest

from unittest.mock import patch

from cover_agent.CustomLogger import CustomLogger


class TestCustomLogger:

    @pytest.mark.parametrize("generate_logs,should_exist", [
        (True, True),
        (False, False),
    ])
    def test_logger_file_creation(self, generate_logs, should_exist):
        """
        Test that log files are only created when generate_logs=True.

        This test mocks the FileHandler to verify whether it is called
        based on the generate_logs flag.

        Args:
            generate_logs (bool): Flag indicating whether logs should be generated.
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
            logger = CustomLogger.get_logger("test_logger", generate_logs=generate_logs)
            logger.info("Test message")

            # Check if FileHandler was called as expected
            if should_exist:
                mock_handler.assert_called_once()
            else:
                mock_handler.assert_not_called()

    @pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    def test_valid_log_levels(self, log_level):
        """
        Test that valid log levels are correctly set for the logger.

        This test uses parameterization to check multiple valid log levels.
        It sets the LOG_LEVEL environment variable to each valid level and
        verifies that the logger's level matches the expected value.

        Args:
            log_level (str): The log level to test (e.g., "DEBUG", "INFO", etc.).
        """
        with patch.dict(os.environ, {"LOG_LEVEL": log_level}):
            logger = CustomLogger.get_logger("test_logger", generate_logs=False)
            assert logger.level == CustomLogger.VALID_LOG_LEVELS[log_level]

    def test_invalid_log_level(self):
        """
        Test that an invalid LOG_LEVEL environment variable raises a ValueError.

        This test sets the LOG_LEVEL environment variable to an invalid value
        and verifies that the `get_logger` method raises a ValueError with the
        appropriate error message.

        Steps:
        1. Mock the LOG_LEVEL environment variable with an invalid value.
        2. Call the `get_logger` method and expect a ValueError to be raised.
        3. Assert that the error message contains the invalid value and the list
           of valid log levels.

        Raises:
            ValueError: If the LOG_LEVEL environment variable contains an invalid value.
        """
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBU"}):
            with pytest.raises(ValueError) as exc_info:
                CustomLogger.get_logger("test_logger")
            assert "Invalid LOG_LEVEL: DEBU" in str(exc_info.value)
            assert "Valid levels are:" in str(exc_info.value)

    def test_empty_log_level_defaults_to_debug(self):
        """
        Test that an empty or missing LOG_LEVEL environment variable defaults to DEBUG.

        This test clears the LOG_LEVEL environment variable and verifies that
        the logger's level is set to DEBUG, which is the default behavior.

        Steps:
        1. Clear the LOG_LEVEL environment variable using `patch.dict`.
        2. Call the `get_logger` method to create a logger instance.
        3. Assert that the logger's level is set to DEBUG.

        Expected Behavior:
            The logger should default to DEBUG level when LOG_LEVEL is not set.
        """
        with patch.dict(os.environ, {}, clear=True):
            logger = CustomLogger.get_logger("test_logger", generate_logs=False)
            assert logger.level == logging.DEBUG
