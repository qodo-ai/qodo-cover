import datetime
import os
import tempfile

from unittest.mock import MagicMock, mock_open, patch

import pytest

from cover_agent.coverage_processor import CoverageProcessor
from cover_agent.runner import Runner
from cover_agent.settings.config_schema import CoverageType
from cover_agent.unit_test_validator import UnitTestValidator


class TestUnitValidator:
    """Test suite for the UnitTestValidator class."""

    def test_extract_error_message_exception_handling(self):
        """
        Test the `extract_error_message` method of the `UnitTestValidator` class.

        This test ensures that when the `analyze_test_failure` method of the
        `agent_completion` object raises an exception, the `extract_error_message`
        method handles it gracefully and returns an empty string.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters.
        3. Simulate an exception being raised by the `analyze_test_failure` method.
        4. Call the `extract_error_message` method with mock failure details.
        5. Assert that the returned error message is an empty string.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            mock_agent_completion = MagicMock()
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=mock_agent_completion,
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
            )

            # Simulate agent_completion raising an exception
            mock_agent_completion.analyze_test_failure.side_effect = Exception("Mock exception")

            fail_details = {
                "stderr": "stderr content",
                "stdout": "stdout content",
                "processed_test_file": "",
            }
            error_message = generator.extract_error_message(fail_details)

            # Should return an empty string on failure
            assert error_message == ""

    def test_run_coverage_with_report_coverage_flag(self):
        """
        Test the `run_coverage` method of the `UnitTestValidator` class when the
        `use_report_coverage_feature_flag` is enabled.

        This test ensures that the `run_coverage` method correctly processes the
        coverage report and updates the `current_coverage` attribute when the
        feature flag is enabled.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters,
           including enabling the `use_report_coverage_feature_flag`.
        3. Mock the `run_command` method of the `Runner` class to simulate a successful
           command execution.
        4. Mock the `process_coverage_report` method of the `CoverageProcessor` class
           to return a predefined coverage report.
        5. Call the `run_coverage` method of the `UnitTestValidator` instance.
        6. Assert that the `current_coverage` attribute is updated correctly.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                use_report_coverage_feature_flag=True,
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
            )
            with patch.object(Runner, "run_command", return_value=("", "", 0, datetime.datetime.now())):
                with patch.object(
                    CoverageProcessor,
                    "process_coverage_report",
                    return_value={"test.py": ([], [], 1.0)},
                ):
                    generator.run_coverage()
                    # Dividing by zero so we're expecting a logged error and a return of 0
                    assert generator.current_coverage == 0

    def test_extract_error_message_with_prompt_builder(self):
        """
        Test the `extract_error_message` method of the `UnitTestValidator` class with a prompt builder.

        This test ensures that the method correctly extracts an error message from the provided
        failure details and verifies that the `analyze_test_failure` method of the `agent_completion`
        object is called with the correct arguments.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters.
        3. Mock the `analyze_test_failure` method of the `agent_completion` object to return a predefined response.
        4. Define mock failure details to simulate a test failure scenario.
        5. Call the `extract_error_message` method with the mock failure details.
        6. Assert that the returned error message matches the expected value.
        7. Verify that the `analyze_test_failure` method was called with the correct arguments.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            mock_agent_completion = MagicMock()
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=mock_agent_completion,
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
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

            assert error_message.strip() == "error_summary: Test failed due to assertion error in test_example"
            mock_agent_completion_call_args = mock_agent_completion.analyze_test_failure.call_args[1]
            assert fail_details["stderr"] == mock_agent_completion_call_args["stderr"]
            assert fail_details["stdout"] == mock_agent_completion_call_args["stdout"]
            assert fail_details["processed_test_file"] == mock_agent_completion_call_args["processed_test_file"]
            assert fail_details["test_file_name"] == mock_agent_completion_call_args["test_file_name"]
            assert fail_details["source_file_name"] in mock_agent_completion_call_args["source_file_name"]
            assert fail_details["source_file"] == mock_agent_completion_call_args["source_file"]

    def test_validate_test_pass_no_coverage_increase_with_prompt(self):
        """
        Test the `validate_test` method of the `UnitTestValidator` class when the test passes
        but the code coverage does not increase.

        This test ensures that the method correctly identifies the lack of coverage increase
        and returns the appropriate failure status and reason.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters.
        3. Set up the initial state of the `UnitTestValidator` instance, including current coverage,
           test headers indentation, and relevant line numbers.
        4. Define a test to validate with mock test code and imports.
        5. Mock file operations and external method calls (`run_command` and `process_coverage_report`).
        6. Call the `validate_test` method with the test to validate.
        7. Assert that the method returns a failure status with the correct reason and exit code.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
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

            with (
                patch("builtins.open", mock_file),
                patch.object(Runner, "run_command", return_value=("", "", 0, datetime.datetime.now())),
                patch.object(CoverageProcessor, "process_coverage_report", return_value=([], [], 0.4)),
            ):

                result = generator.validate_test(test_to_validate)

                assert result["status"] == "FAIL"
                assert "Coverage did not increase" in result["reason"]
                assert result["exit_code"] == 0

    def test_initial_test_suite_analysis_with_agent_completion(self):
        """
        Test the `initial_test_suite_analysis` method of the `UnitTestValidator` class.

        This test ensures that the `initial_test_suite_analysis` method correctly initializes
        the test suite analysis by setting the appropriate attributes based on the responses
        from the `agent_completion` object.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters.
        3. Mock the responses of the `analyze_suite_test_headers_indentation` and
           `analyze_test_insert_line` methods of the `agent_completion` object.
        4. Call the `initial_test_suite_analysis` method.
        5. Assert that the attributes `test_headers_indentation`,
           `relevant_line_number_to_insert_tests_after`, `relevant_line_number_to_insert_imports_after`,
           and `testing_framework` are set correctly.
        6. Verify that the mocked methods of the `agent_completion` object were called once.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            mock_agent_completion = MagicMock()
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=mock_agent_completion,
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
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
        """
        Test the `post_process_coverage_report` method of the `UnitTestValidator` class
        when the `use_report_coverage_feature_flag` is enabled.

        This test ensures that the method correctly processes the coverage report
        and calculates the percentage of code covered and the coverage percentages
        for individual files.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters,
           including enabling the `use_report_coverage_feature_flag`.
        3. Mock the `process_coverage_report` method of the `CoverageProcessor` class
           to return a predefined coverage report.
        4. Call the `post_process_coverage_report` method with the current timestamp.
        5. Assert that the returned percentage covered and coverage percentages
           match the expected values.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                use_report_coverage_feature_flag=True,
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
            )
            with patch.object(
                CoverageProcessor,
                "process_coverage_report",
                return_value={"test.py": ([1], [1], 1.0)},
            ):
                percentage_covered, coverage_percentages = generator.post_process_coverage_report(
                    datetime.datetime.now()
                )
                assert percentage_covered == 0.5
                assert coverage_percentages == {"test.py": 1.0}

    def test_post_process_coverage_report_with_diff_coverage(self):
        """
        Test the `post_process_coverage_report` method of the `UnitTestValidator` class
        when the `diff_coverage` flag is enabled.

        This test ensures that the method correctly processes the coverage report
        and calculates the percentage of code covered when the `diff_coverage` feature
        is used.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters,
           including enabling the `diff_coverage` flag.
        3. Mock the `generate_diff_coverage_report` method to simulate its behavior.
        4. Mock the `process_coverage_report` method of the `CoverageProcessor` class
           to return a predefined coverage report.
        5. Call the `post_process_coverage_report` method with the current timestamp.
        6. Assert that the returned percentage covered matches the expected value.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                diff_coverage=True,
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
            )
            with (
                patch.object(generator, "generate_diff_coverage_report"),
                patch.object(CoverageProcessor, "process_coverage_report", return_value=([], [], 0.8)),
            ):
                percentage_covered, coverage_percentages = generator.post_process_coverage_report(
                    datetime.datetime.now()
                )
                assert percentage_covered == 0.8

    def test_post_process_coverage_report_without_flags(self):
        """
        Test the `post_process_coverage_report` method of the `UnitTestValidator` class
        when no feature flags are enabled.

        This test ensures that the method correctly processes the coverage report
        and calculates the percentage of code covered when neither the `diff_coverage`
        nor the `use_report_coverage_feature_flag` is enabled.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters,
           ensuring that both `diff_coverage` and `use_report_coverage_feature_flag` are disabled.
        3. Mock the `process_coverage_report` method of the `CoverageProcessor` class
           to return a predefined coverage report.
        4. Call the `post_process_coverage_report` method with the current timestamp.
        5. Assert that the returned percentage covered matches the expected value.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                max_run_time_sec=30,
                desired_coverage=90,
                comparison_branch="main",
                coverage_type=CoverageType.COBERTURA,
                diff_coverage=False,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
            )
            with patch.object(CoverageProcessor, "process_coverage_report", return_value=([], [], 0.7)):
                percentage_covered, coverage_percentages = generator.post_process_coverage_report(
                    datetime.datetime.now()
                )
                assert percentage_covered == 0.7

    def test_generate_diff_coverage_report_success(self):
        """
        Test the `generate_diff_coverage_report` method of the `UnitTestValidator` class.

        This test ensures that the `generate_diff_coverage_report` method correctly calls
        the `diff_cover_main` function with the expected arguments to generate a diff coverage report.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters, including enabling the `diff_coverage` flag.
        3. Mock the `diff_cover_main` function to verify it is called with the correct arguments.
        4. Call the `generate_diff_coverage_report` method.
        5. Assert that the `diff_cover_main` function is called once with the expected arguments.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                diff_coverage=True,
                comparison_branch="main",
                max_run_time_sec=30,
                desired_coverage=90,
                coverage_type=CoverageType.COBERTURA,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
            )
            with patch("cover_agent.unit_test_validator.diff_cover_main") as mock_diff_cover_main:
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
        """
        Test the `generate_diff_coverage_report` method of the `UnitTestValidator` class
        when an exception is raised during the execution of the `diff_cover_main` function.

        This test ensures that the method handles exceptions gracefully and logs the error
        message appropriately.

        Steps:
        1. Create a temporary source file to simulate the source file path.
        2. Initialize a `UnitTestValidator` instance with the required parameters, including enabling the `diff_coverage` flag.
        3. Mock the `diff_cover_main` function to raise an exception.
        4. Mock the logger's `error` method to verify that the error is logged correctly.
        5. Call the `generate_diff_coverage_report` method.
        6. Assert that the logger's `error` method is called with the expected error message.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                test_command_dir=os.getcwd(),
                llm_model="gpt-3",
                agent_completion=MagicMock(),
                diff_coverage=True,
                comparison_branch="main",
                max_run_time_sec=30,
                desired_coverage=90,
                coverage_type=CoverageType.COBERTURA,
                num_attempts=1,
                additional_instructions="",
                included_files=[],
                use_report_coverage_feature_flag=False,
            )
            with (
                patch(
                    "cover_agent.unit_test_validator.diff_cover_main",
                    side_effect=Exception("Mock exception"),
                ),
                patch.object(generator.logger, "error") as mock_logger_error,
            ):
                generator.generate_diff_coverage_report()
                mock_logger_error.assert_called_once_with("Error running diff-cover: Mock exception")
