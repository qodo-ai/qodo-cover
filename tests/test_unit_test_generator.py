import tempfile

from unittest.mock import MagicMock, mock_open, patch

import pytest

import cover_agent.utils

from cover_agent.unit_test_generator import UnitTestGenerator


class TestUnitTestGenerator:
    """
    Test cases for the UnitTestGenerator class.
    """

    def test_get_included_files_mixed_paths(self):
        """
        Test get_included_files with a mix of valid and invalid file paths.
        This test ensures that the function correctly handles IOError for invalid files
        and processes valid files as expected.
        """
        with patch("builtins.open", mock_open(read_data="file content")) as mock_file:
            # Simulate IOError for the first file and valid read for the second file
            mock_file.side_effect = [
                IOError("File not found"),
                mock_open(read_data="file content").return_value,
            ]
            included_files = ["invalid_file1.txt", "valid_file2.txt"]
            result = cover_agent.utils.get_included_files(included_files, disable_tokens=True)
            # Assert that only the valid file content is returned
            assert result == "file_path: `valid_file2.txt`\ncontent:\n```\nfile content\n```"

    def test_get_included_files_valid_paths(self):
        """
        Test get_included_files with all valid file paths.
        This test ensures that the function correctly reads and processes multiple valid files.
        """
        with patch("builtins.open", mock_open(read_data="file content")):
            included_files = ["file1.txt", "file2.txt"]
            result = cover_agent.utils.get_included_files(included_files, disable_tokens=True)
            # Assert that the content of both files is returned correctly
            assert (
                result
                == "file_path: `file1.txt`\ncontent:\n```\nfile content\n```\n\n\nfile_path: `file2.txt`\ncontent:\n```\nfile content\n```"
            )

    def test_get_code_language_no_extension(self):
        """
        Test get_code_language with a filename that has no extension.
        This test ensures that the function returns 'unknown' for files without an extension.
        """
        with (
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file,
            tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file,
        ):
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path=temp_test_file.name,
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
            )
            # Test with a filename that has no extension
            language = generator.get_code_language("filename")
            assert language == "unknown"
