from cover_agent.coverage.processor import process_coverage, CoverageProcessor, CoverageReport, CoverageData
from cover_agent.Runner import Runner
from cover_agent.UnitTestValidator import UnitTestValidator
from unittest.mock import patch, mock_open
from unittest.mock import MagicMock

import datetime
import tempfile

class TestUnitValidator:
    def test_extract_error_message_exception_handling(self):
            # PromptBuilder will not instantiate so we're expecting an empty error_message.
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
                generator = UnitTestValidator(
                    source_file_path=temp_source_file.name,
                    test_file_path="test_test.py",
                    code_coverage_report_path="coverage.xml",
                    test_command="pytest",
                    llm_model="gpt-3"
                )
                with patch.object(generator, 'ai_caller') as mock_ai_caller:
                    mock_ai_caller.call_model.side_effect = Exception("Mock exception")
                    fail_details = {"stderr": "stderr content", "stdout": "stdout content", "processed_test_file": ""}
                    error_message = generator.extract_error_message(fail_details)
                    assert '' in error_message

    # TODO: Is this still valid test?
    def test_run_coverage_with_report_coverage_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                use_report_coverage_feature_flag=True
            )
            with patch.object(Runner, 'run_command', return_value=("", "", 0, datetime.datetime.now())):
                with patch.object(CoverageProcessor, 'process_coverage_report', return_value=CoverageReport(total_coverage=1.0, file_coverage={'test.py': CoverageData([], 0, [], 0, 1.0)})):
                    generator.run_coverage()
                    # Dividing by zero so we're expecting a logged error and a return of 0
                    assert generator.current_coverage_report.total_coverage == 1.0


    def test_extract_error_message_with_prompt_builder(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            
            # Mock the prompt builder
            mock_prompt_builder = MagicMock()
            generator.prompt_builder = mock_prompt_builder
            mock_prompt_builder.build_prompt_custom.return_value = "test prompt"
            
            mock_response = """
            error_summary: Test failed due to assertion error in test_example
            """
            
            with patch.object(generator.ai_caller, 'call_model', return_value=(mock_response, 10, 10)):
                fail_details = {"stderr": "AssertionError: assert False", "stdout": "test_example failed", "processed_test_file": ""}
                error_message = generator.extract_error_message(fail_details)
                
                assert error_message == 'error_summary: Test failed due to assertion error in test_example'
                mock_prompt_builder.build_prompt_custom.assert_called_once_with(file="analyze_test_run_failure")


    def test_validate_test_pass_no_coverage_increase_with_prompt(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            
            # Setup initial state
            generator.current_coverage_report = CoverageReport(total_coverage=0.5, file_coverage={'test.py': CoverageData([], 0, [], 0, 0.0)})
            generator.test_headers_indentation = 4
            generator.relevant_line_number_to_insert_tests_after = 100
            generator.relevant_line_number_to_insert_imports_after = 10
            generator.prompt = {'user': 'test prompt'}
            
            test_to_validate = {
                "test_code": "def test_example(): assert True",
                "new_imports_code": ""
            }
            
            # Mock file operations
            mock_content = "original content"
            mock_file = mock_open(read_data=mock_content)
            
            with patch("builtins.open", mock_file), \
                    patch.object(Runner, 'run_command', return_value=("", "", 0, datetime.datetime.now())), \
                    patch.object(CoverageProcessor, 'process_coverage_report', return_value=CoverageReport(total_coverage=0.4, file_coverage={'test.py': CoverageData([], 0, [], 0, 0.0)})):
                
                result = generator.validate_test(test_to_validate)
                
                assert result["status"] == "FAIL"
                assert result["reason"] == "Coverage did not increase. Maybe the test did run but did not increase coverage, or maybe the test execution was skipped due to some problem"
                assert result["exit_code"] == 0

    def test_initial_test_suite_analysis_with_prompt_builder(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )

            # Mock the prompt builder
            mock_prompt_builder = MagicMock()
            generator.prompt_builder = mock_prompt_builder
            mock_prompt_builder.build_prompt_custom.side_effect = [
                "test_headers_indentation: 4",
                "relevant_line_number_to_insert_tests_after: 100\nrelevant_line_number_to_insert_imports_after: 10\ntesting_framework: pytest"
            ]

            # Mock the AI caller responses
            with patch.object(generator.ai_caller, 'call_model') as mock_call:
                mock_call.side_effect = [
                    ("test_headers_indentation: 4", 10, 10),
                    ("relevant_line_number_to_insert_tests_after: 100\nrelevant_line_number_to_insert_imports_after: 10\ntesting_framework: pytest", 10, 10)
                ]

                generator.initial_test_suite_analysis()

                assert generator.test_headers_indentation == 4
                assert generator.relevant_line_number_to_insert_tests_after == 100
                assert generator.relevant_line_number_to_insert_imports_after == 10
                assert generator.testing_framework == "pytest"

    # TODO: Is this still valid test?
    def test_post_process_coverage_report_with_report_coverage_flag(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                use_report_coverage_feature_flag=True
            )
            # patch.object(CoverageProcessor, 'process_coverage_report', return_value=CoverageReport(total_coverage=0.4, file_coverage={'test.py': CoverageData([], 0, [], 0, 0.0)})):
            with patch.object(CoverageProcessor, 'process_coverage_report', return_value=CoverageReport(total_coverage=1.0, file_coverage={'test.py': CoverageData([1], 1, [1], 1, 1.0)})):
                coverage_report = generator.post_process_coverage_report(datetime.datetime.now())
                assert coverage_report.total_coverage == 1.0
                assert coverage_report.file_coverage == {'test.py': CoverageData([1], 1, [1], 1, 1.0)}

    def test_post_process_coverage_report_with_diff_coverage(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                diff_coverage=True
            )
            with patch.object(generator, 'generate_diff_coverage_report'), \
                    patch.object(CoverageProcessor, 'process_coverage_report', return_value=CoverageReport(total_coverage=0.8, file_coverage={'test.py': CoverageData([1], 1, [1], 1, 1.0)})):
                coverage_report = generator.post_process_coverage_report(datetime.datetime.now())
                assert coverage_report.total_coverage == 0.8

    def test_post_process_coverage_report_without_flags(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3"
            )
            with patch.object(CoverageProcessor, 'process_coverage_report', return_value=CoverageReport(total_coverage=0.7, file_coverage={'test.py': CoverageData([1], 1, [1], 1, 1.0)})):
                coverage_report = generator.post_process_coverage_report(datetime.datetime.now())
                assert coverage_report.total_coverage == 0.7

    def test_generate_diff_coverage_report(self):
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_source_file:
            generator = UnitTestValidator(
                source_file_path=temp_source_file.name,
                test_file_path="test_test.py",
                code_coverage_report_path="coverage.xml",
                test_command="pytest",
                llm_model="gpt-3",
                diff_coverage=True
            )
            with patch.object(Runner, 'run_command', return_value=("", "", 0, datetime.datetime.now())):
                generator.generate_diff_coverage_report()
                assert generator.diff_cover_report_path.endswith("diff-cover-report.json")