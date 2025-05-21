import os

from unittest.mock import mock_open, patch

import pytest

# Import the get_version function from version.py
from cover_agent.version import get_version


# File location of version file is one directory up from this file's location. Use os.path to find this
VERSION_FILE_LOCATION = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover_agent/version.txt")


class TestGetVersion:
    """
    Test suite for the get_version function.
    """

    @patch("builtins.open", new_callable=mock_open, read_data="1.2.3")
    def test_get_version_happy_path(self, mock_file):
        """
        Test that get_version returns the correct version string when the version file is present and contains valid data.
        """
        assert get_version() == "1.2.3"

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_get_version_file_missing(self, mock_file):
        """
        Test that get_version raises a FileNotFoundError when the version file is missing.
        """
        with pytest.raises(FileNotFoundError):
            get_version()

    @patch("builtins.open", new_callable=mock_open, read_data="   ")
    def test_get_version_empty_or_whitespace_file(self, mock_file):
        """
        Test that get_version returns an empty string when the version file is empty or contains only whitespace.
        """
        assert get_version() == ""

    @patch("cover_agent.version.sys")
    @patch("builtins.open", new_callable=mock_open, read_data="1.2.3")
    def test_get_version_frozen_application(self, mock_open, mock_sys):
        """
        Test that get_version works correctly when the application is frozen (e.g., packaged with PyInstaller).
        """
        mock_sys.frozen = True
        mock_sys._MEIPASS = os.path.dirname(__file__)
        assert get_version() == "1.2.3"
