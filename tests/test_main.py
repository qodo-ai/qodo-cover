import os
import argparse
from unittest.mock import patch, MagicMock
import pytest
from cover_agent.main import parse_args, main


class TestMain:
    def test_parse_args(self):
        with patch(
            "sys.argv",
            [
                "program.py",
                "--source-file-path",
                "test_source.py",
                "--test-file-path",
                "test_file.py",
                "--code-coverage-report-path",
                "coverage_report.xml",
                "--test-command",
                "pytest",
                "--max-iterations",
                "10",
            ],
        ):
            args = parse_args()
            assert args.source_file_path == "test_source.py"
            assert args.test_file_path == "test_file.py"
            assert args.code_coverage_report_path == "coverage_report.xml"
            assert args.test_command == "pytest"
            assert args.test_command_dir == os.getcwd()
            assert args.included_files is None
            assert args.coverage_type == "cobertura"
            assert args.report_filepath == "test_results.html"
            assert args.desired_coverage == 90
            assert args.max_iterations == 10

    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    def test_main_source_file_not_found(
        self, mock_isfile, mock_unit_cover_agent
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
        )
        parse_args = lambda: args  # Mocking parse_args function
        mock_isfile.return_value = False  # Simulate source file not found

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                main()

        assert (
            str(exc_info.value) == f"Source file not found at {args.source_file_path}"
        )
        mock_unit_cover_agent.assert_not_called()

    @patch("cover_agent.CoverAgent.os.path.exists")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    def test_main_test_file_not_found(
        self, mock_unit_cover_agent, mock_isfile, mock_exists
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            prompt_only=False,
        )
        parse_args = lambda: args  # Mocking parse_args function
        mock_isfile.side_effect = [True, False]
        mock_exists.return_value = True

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                main()

        assert str(exc_info.value) == f"Test file not found at {args.test_file_path}"

    @patch("cover_agent.main.CoverAgent")
    @patch("cover_agent.main.parse_args")
    @patch("cover_agent.main.os.path.isfile")
    def test_main_calls_agent_run(
        self, mock_isfile, mock_parse_args, mock_cover_agent
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            test_file_output_path="",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            additional_instructions="",
            model="gpt-4o",
            api_base="http://localhost:11434",
            strict_coverage=False,
            run_tests_multiple_times=1,
            use_report_coverage_feature_flag=False,
            log_db_path="",
        )
        mock_parse_args.return_value = args
        # Mock os.path.isfile to return True for both source and test file paths
        mock_isfile.side_effect = lambda path: path in [args.source_file_path, args.test_file_path]
        mock_agent_instance = MagicMock()
        mock_cover_agent.return_value = mock_agent_instance
    
        main()
    
        mock_cover_agent.assert_called_once_with(args)
        mock_agent_instance.run.assert_called_once()

