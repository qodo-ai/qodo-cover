from cover_agent.CoverageProcessor import CoverageProcessor
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.Runner import Runner
from cover_agent.UnitTestValidator import UnitTestValidator
from unittest.mock import patch, mock_open
from unittest.mock import MagicMock

import datetime
import os
import pytest
import tempfile


class TestUnitValidator:
    def test_extract_error_message_exception_handling(self):
        """Ensure exception handling works when calling agent_completion for error extraction."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            mock_agent_completion = MagicMock()
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=mock_agent_completion,
                max_run_time=30,
            )

            # Simulate agent_completion raising an exception
            mock_agent_completion.analyze_test_failure.side_effect = Exception(
                "Mock exception"
            )

            fail_details = {
                "stderr": "stderr content",
                "stdout": "stdout content",
                "processed_test_file": "",
            }
            error_message = generator.extract_error_message(fail_details)

            assert error_message == ""  # Should return an empty string on failure

    def test_run_coverage_with_report_coverage_flag(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                use_report_coverage_feature_flag=True,
                max_run_time=30,
            )
            with patch.object(
                Runner, "run_command", return_value=("", "", 0, datetime.datetime.now())
            ):
                with patch.object(
                    CoverageProcessor,
                    "process_coverage_report",
                    return_value={"test.py": ([], [], 1.0)},
                ):
                    generator.run_coverage()
                    # Dividing by zero so we're expecting a logged error and a return of 0
                    assert generator.current_coverage == 0

    def test_extract_error_message_with_prompt_builder(self):
        """Ensure error message extraction works properly with agent_completion."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            mock_agent_completion = MagicMock()
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=mock_agent_completion,
                max_run_time=30,
            )

            mock_response = """
            error_summary: Test failed due to assertion error in test_example
            """
            mock_agent_completion.analyze_test_failure.return_value = (
                mock_response,
                10,
                10,
                "test prompt",
            )

            fail_details = {
                "stderr": "AssertionError: assert False",
                "stdout": "test_example failed",
                "processed_test_file": "",
                "test_file_name": "test_test.py",
                "source_file_name": temp_source_file.name,
                "source_file": "",
            }
            error_message = generator.extract_error_message(fail_details)

            assert (
                error_message.strip()
                == "error_summary: Test failed due to assertion error in test_example"
            )
            mock_agent_completion_call_args = (
                mock_agent_completion.analyze_test_failure.call_args[1]
            )
            assert fail_details["stderr"] == mock_agent_completion_call_args["stderr"]
            assert fail_details["stdout"] == mock_agent_completion_call_args["stdout"]
            assert (
                fail_details["processed_test_file"]
                == mock_agent_completion_call_args["processed_test_file"]
            )
            assert (
                fail_details["test_file_name"]
                == mock_agent_completion_call_args["test_file_name"]
            )
            assert (
                fail_details["source_file_name"]
                in mock_agent_completion_call_args["source_file_name"]
            )
            assert (
                fail_details["source_file"]
                == mock_agent_completion_call_args["source_file"]
            )

    def test_validate_test_pass_no_coverage_increase_with_prompt(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                max_run_time=30,
            )

            # Setup initial state
            generator.current_coverage = 0.5
            generator.test_headers_indentation = 4
            generator.relevant_line_number_to_insert_tests_after = 100
            generator.relevant_line_number_to_insert_imports_after = 10
            generator.prompt = {"user": "test prompt"}

            test_to_validate = {
                "test_code": "def test_example(): assert True",
                "new_imports_code": "",
            }

            # Mock file operations
            mock_content = "original content"
            mock_file = mock_open(read_data=mock_content)

            with patch("builtins.open", mock_file), patch.object(
                Runner, "run_command", return_value=("", "", 0, datetime.datetime.now())
            ), patch.object(
                CoverageProcessor, "process_coverage_report", return_value=([], [], 0.4)
            ):

                result = generator.validate_test(test_to_validate)

                assert result["status"] == "FAIL"
                assert "Coverage did not increase" in result["reason"]
                assert result["exit_code"] == 0

    def test_initial_test_suite_analysis_with_agent_completion(self):
        """Ensure the initial test suite analysis properly uses agent_completion."""
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            mock_agent_completion = MagicMock()
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=mock_agent_completion,
                max_run_time=30,
            )

            # Mock responses from agent_completion
            mock_agent_completion.analyze_suite_test_headers_indentation.return_value = (
                "test_headers_indentation: 4",
                10,
                10,
                "test prompt",
            )
            mock_agent_completion.analyze_test_insert_line.return_value = (
                "relevant_line_number_to_insert_tests_after: 100\nrelevant_line_number_to_insert_imports_after: 10\ntesting_framework: pytest",
                10,
                10,
                "test prompt",
            )

            # Run the function (without _init_prompt_builder)
            generator.initial_test_suite_analysis()

            # Assertions to check the expected values
            assert generator.test_headers_indentation == 4
            assert generator.relevant_line_number_to_insert_tests_after == 100
            assert generator.relevant_line_number_to_insert_imports_after == 10
            assert generator.testing_framework == "pytest"

            # Ensure the correct agent_completion methods were called
            mock_agent_completion.analyze_suite_test_headers_indentation.assert_called_once()
            mock_agent_completion.analyze_test_insert_line.assert_called_once()

    def test_post_process_coverage_report_with_report_coverage_flag(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                use_report_coverage_feature_flag=True,
                max_run_time=30,
            )
            with patch.object(
                CoverageProcessor,
                "process_coverage_report",
                return_value={"test.py": ([1], [1], 1.0)},
            ):
                percentage_covered, coverage_percentages = (
                    generator.post_process_coverage_report(datetime.datetime.now())
                )
                assert percentage_covered == 0.5
                assert coverage_percentages == {"test.py": 1.0}

    def test_post_process_coverage_report_with_diff_coverage(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                diff_coverage=True,
                max_run_time=30,
            )
            with patch.object(generator, "generate_diff_coverage_report"), patch.object(
                CoverageProcessor, "process_coverage_report", return_value=([], [], 0.8)
            ):
                percentage_covered, coverage_percentages = (
                    generator.post_process_coverage_report(datetime.datetime.now())
                )
                assert percentage_covered == 0.8

    def test_post_process_coverage_report_without_flags(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                max_run_time=30,
            )
            with patch.object(
                CoverageProcessor, "process_coverage_report", return_value=([], [], 0.7)
            ):
                percentage_covered, coverage_percentages = (
                    generator.post_process_coverage_report(datetime.datetime.now())
                )
                assert percentage_covered == 0.7

    def test_generate_diff_coverage_report_success(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                diff_coverage=True,
                comparison_branch="main",
                max_run_time=30,
            )
            with patch(
                "cover_agent.UnitTestValidator.diff_cover_main"
            ) as mock_diff_cover_main:
                generator.generate_diff_coverage_report()
                mock_diff_cover_main.assert_called_once_with(
                    [
                        "diff-cover",
                        "--json-report",
                        generator.diff_cover_report_path,
                        "--compare-branch=main",
                        "coverage.xml",
                    ]
                )

    def test_generate_diff_coverage_report_failure(self):
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False
        ) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                diff_coverage=True,
                comparison_branch="main",
                max_run_time=30,
            )
            with patch(
                "cover_agent.UnitTestValidator.diff_cover_main",
                side_effect=Exception("Mock exception"),
            ), patch.object(generator.logger, "error") as mock_logger_error:
                generator.generate_diff_coverage_report()
                mock_logger_error.assert_called_once_with(
                    "Error running diff-cover: Mock exception"
                )
