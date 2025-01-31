import os
import pytest
import tempfile
from unittest.mock import patch, mock_open
from cover_agent.PromptBuilder import PromptBuilder


class TestPromptBuilder:
    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch):
        mock_open_obj = mock_open(read_data="dummy content")
        monkeypatch.setattr("builtins.open", mock_open_obj)
        self.mock_open_obj = mock_open_obj

    def test_initialization_reads_file_contents(self):
        builder = PromptBuilder(
            "source_path",
            "test_path",
            "dummy content",
        )
        assert builder.source_file == "dummy content"
        assert builder.test_file == "dummy content"
        assert builder.code_coverage_report == "dummy content"
        assert builder.included_files == ""  # Updated expected value

    def test_initialization_handles_file_read_errors(self, monkeypatch):
        def mock_open_raise(*args, **kwargs):
            raise IOError("File not found")

        monkeypatch.setattr("builtins.open", mock_open_raise)

        builder = PromptBuilder(
            "source_path",
            "test_path",
            "coverage_report",
        )
        assert "Error reading source_path" in builder.source_file
        assert "Error reading test_path" in builder.test_file

    def test_empty_included_files_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )
        # Directly read the real file content for the prompt template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"
        builder.included_files = ""

        result = builder.build_prompt(file="test_generation_prompt")
        assert "## Additional Includes" not in result["user"]

    def test_non_empty_included_files_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )

        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt(file="test_generation_prompt")
        assert "## Additional Includes" in result["user"]
        assert "Included Files Content" in result["user"]

    def test_empty_additional_instructions_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt(file="test_generation_prompt")
        assert "## Additional Instructions" not in result["user"]

    def test_empty_failed_test_runs_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt(file="test_generation_prompt")
        assert "## Previous Iterations Failed Tests" not in result["user"]

    def test_non_empty_additional_instructions_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="Additional Instructions Content",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt(file="test_generation_prompt")
        assert "## Additional Instructions" in result["user"]
        assert "Additional Instructions Content" in result["user"]

    # we currently disabled the logic to add failed test runs to the prompt
    def test_non_empty_failed_test_runs_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="Failed Test Runs Content",
        )
        # Directly read the real file content for the prompt template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt(file="test_generation_prompt")
        assert "## Previous Iterations Failed Tests" in result["user"]
        assert "Failed Test Runs Content" in result["user"]

    def test_build_prompt_handles_rendering_exception(self, monkeypatch):
        def mock_render(*args, **kwargs):
            raise Exception("Rendering error")

        monkeypatch.setattr(
            "jinja2.Environment.from_string",
            lambda *args, **kwargs: type("", (), {"render": mock_render})(),
        )

        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
        )
        result = builder.build_prompt("custom_file")
        assert result == {"system": "", "user": ""}

    def test_build_prompt_handles_rendering_exception(self, monkeypatch):
        def mock_render(*args, **kwargs):
            raise Exception("Rendering error")

        monkeypatch.setattr(
            "jinja2.Environment.from_string",
            lambda *args, **kwargs: type("", (), {"render": mock_render})(),
        )

        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
        )
        result = builder.build_prompt(file="test_generation_prompt")
        assert result == {"system": "", "user": ""}

class TestPromptBuilderEndToEnd:
    def test_custom_analyze_test_run_failure(self):
        # Create fake source and test files and tmp files and pass in the paths
        source_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        source_file.write("def foo():\n    pass")
        source_file.close()
        test_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        test_file.write("def test_foo():\n    pass")
        test_file.close()
        tmp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        tmp_file.write("tmp file content")
        tmp_file.close()

        builder = PromptBuilder(
            source_file_path=source_file.name,
            test_file_path=test_file.name,
            code_coverage_report=tmp_file.name,
        )

        builder.stderr_from_run = "stderr content"
        builder.stdout_from_run = "stdout content"
        builder.processed_test_file = "processed test file content"

        result = builder.build_prompt("analyze_test_run_failure")
        assert "stderr content" in result["user"]
        assert "stdout content" in result["user"]

        # Clean up
        os.remove(source_file.name)
        os.remove(test_file.name)
        os.remove(tmp_file.name)

    def test_build_prompt_missing_settings(self, monkeypatch):
        # Mock get_settings to return None for the file
        def mock_get_settings():
            return type('Settings', (), {'get': lambda x: None})()
        
        monkeypatch.setattr('cover_agent.PromptBuilder.get_settings', mock_get_settings)
        
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report"
        )
        
        result = builder.build_prompt("nonexistent_file")
        assert result == {"system": "", "user": ""}

