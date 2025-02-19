from cover_agent.CoverageProcessor import CoverageProcessor
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.Runner import Runner
from cover_agent.UnitTestGenerator import UnitTestGenerator
import cover_agent.utils
from unittest.mock import patch, mock_open
import datetime
import os
import pytest
import tempfile

from unittest.mock import MagicMock


class TestUnitTestGenerator:
    def test_get_included_files_mixed_paths(self):
        with patch("builtins.open", mock_open(read_data="file content")) as mock_file:
            mock_file.side_effect = [
                IOError("File not found"),
                mock_open(read_data="file content").return_value,
            ]
            included_files = ["invalid_file1.txt", "valid_file2.txt"]
            result = cover_agent.utils.get_included_files(
                included_files, disable_tokens=True
            )
            assert (
                result
                == "file_path: `valid_file2.txt`\ncontent:\n```\nfile content\n```"
            )

    def test_get_included_files_valid_paths(self):
        with patch("builtins.open", mock_open(read_data="file content")):
            included_files = ["file1.txt", "file2.txt"]
            result = cover_agent.utils.get_included_files(
                included_files, disable_tokens=True
            )
            assert (
                result
                == "file_path: `file1.txt`\ncontent:\n```\nfile content\n```\n\n\nfile_path: `file2.txt`\ncontent:\n```\nfile content\n```"
            )

    def test_get_code_language_no_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file, \
             tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_test_file:
            generator = UnitTestGenerator(
                source_file_path=temp_source_file.name,
                test_file_path=temp_test_file.name,
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
            )
            language = generator.get_code_language("filename")
            assert language == "unknown"
