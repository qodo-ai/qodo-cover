import pytest
import argparse
from unittest.mock import patch, MagicMock
from dataclasses import FrozenInstanceError

from cover_agent.settings.config_schema import CoverAgentConfig


class TestCoverAgentConfig:
    """Test suite for CoverAgentConfig class."""

    def test_init_with_required_args(self):
        """Test basic initialization with required arguments."""
        config = CoverAgentConfig(
            source_file_path="source.py",
            test_file_path="test.py",
            code_coverage_report_path="coverage.xml",
            test_command="pytest",
            test_command_dir="/project",
            project_root="/project",
            test_file_output_path="test_output.py",
            included_files=["file1.py", "file2.py"],
            coverage_type="cobertura",
            report_filepath="report.html",
            desired_coverage=90,
            max_iterations=10,
            max_run_time=30,
            model="gpt-4o",
            api_base="http://localhost:11434",
            additional_instructions="",
            strict_coverage=False,
            run_tests_multiple_times=1,
            run_each_test_separately=False,
            use_report_coverage_feature_flag=False,
            diff_coverage=False,
            branch="main",
            log_db_path="test.db"
        )

        # Verify all attributes are correctly set
        assert config.source_file_path == "source.py"
        assert config.test_file_path == "test.py"
        assert config.code_coverage_report_path == "coverage.xml"
        assert config.test_command == "pytest"
        assert config.test_command_dir == "/project"
        assert config.project_root == "/project"
        assert config.test_file_output_path == "test_output.py"
        assert config.included_files == ["file1.py", "file2.py"]
        assert config.coverage_type == "cobertura"
        assert config.report_filepath == "report.html"
        assert config.desired_coverage == 90
        assert config.max_iterations == 10
        assert config.max_run_time == 30
        assert config.model == "gpt-4o"
        assert config.api_base == "http://localhost:11434"
        assert config.additional_instructions == ""
        assert config.strict_coverage is False
        assert config.run_tests_multiple_times == 1
        assert config.run_each_test_separately is False
        assert config.use_report_coverage_feature_flag is False
        assert config.diff_coverage is False
        assert config.branch == "main"
        assert config.log_db_path == "test.db"

    def test_init_with_missing_required_args(self):
        """Test initialization fails when required arguments are missing."""
        with pytest.raises(TypeError):
            CoverAgentConfig(
                # Missing required fields
                source_file_path="source.py",
                # Missing test_file_path and other required fields
            )

    def test_from_args(self):
        """Test creating config from command-line arguments."""
        args = argparse.Namespace(
            source_file_path="source.py",
            test_file_path="test.py",
            code_coverage_report_path="coverage.xml",
            test_command="pytest",
            test_command_dir="/project",
            project_root="/project",
            test_file_output_path="test_output.py",
            included_files=["file1.py", "file2.py"],
            coverage_type="cobertura",
            report_filepath="report.html",
            desired_coverage=90,
            max_iterations=10,
            max_run_time=30,
            model="gpt-4o",
            api_base="http://localhost:11434",
            additional_instructions="",
            strict_coverage=False,
            run_tests_multiple_times=1,
            run_each_test_separately=False,
            use_report_coverage_feature_flag=False,
            diff_coverage=False,
            branch="main",
            log_db_path="test.db"
        )

        config = CoverAgentConfig.from_args(args)

        # Verify all attributes match args
        assert config.source_file_path == args.source_file_path
        assert config.test_file_path == args.test_file_path
        assert config.code_coverage_report_path == args.code_coverage_report_path
        assert config.test_command == args.test_command
        assert config.test_command_dir == args.test_command_dir
        assert config.project_root == args.project_root
        assert config.test_file_output_path == args.test_file_output_path
        assert config.included_files == args.included_files
        assert config.coverage_type == args.coverage_type
        assert config.report_filepath == args.report_filepath
        assert config.desired_coverage == args.desired_coverage
        assert config.max_iterations == args.max_iterations
        assert config.max_run_time == args.max_run_time
        assert config.model == args.model
        assert config.api_base == args.api_base
        assert config.additional_instructions == args.additional_instructions
        assert config.strict_coverage == args.strict_coverage
        assert config.run_tests_multiple_times == args.run_tests_multiple_times
        assert config.run_each_test_separately == args.run_each_test_separately
        assert config.use_report_coverage_feature_flag == args.use_report_coverage_feature_flag
        assert config.diff_coverage == args.diff_coverage
        assert config.branch == args.branch
        assert config.log_db_path == args.log_db_path

    @patch("cover_agent.settings.config_schema.get_settings")
    def test_from_args_with_defaults(self, mock_get_settings):
        """Test creating config from args with TOML defaults for missing values."""
        # Create mock settings
        mock_settings = MagicMock()
        mock_toml_config = MagicMock()
        
        # Define TOML default values
        toml_defaults = {
            'source_file_path': 'default_source.py',
            'test_file_path': 'default_test.py',
            'code_coverage_report_path': 'default_coverage.xml',
            'test_command': 'default_pytest',
            'test_command_dir': '/default_project',
            'project_root': '/default_project',
            'test_file_output_path': 'default_output.py',
            'included_files': ['default1.py', 'default2.py'],
            'coverage_type': 'default_cobertura',
            'report_filepath': 'default_report.html',
            'desired_coverage': 85,
            'max_iterations': 5,
            'max_run_time': 45,
            'model': 'default-gpt-4o',
            'api_base': 'http://default:11434',
            'additional_instructions': 'default_instructions',
            'strict_coverage': True,
            'run_tests_multiple_times': 2,
            'run_each_test_separately': True,
            'use_report_coverage_feature_flag': True,
            'diff_coverage': True,
            'branch': 'default_main',
            'log_db_path': 'default_test.db'
        }
        
        # Set up the mocks to return our default values
        for key, value in toml_defaults.items():
            setattr(mock_toml_config, key, value)
        
        mock_settings.get.return_value = mock_toml_config
        mock_get_settings.return_value = mock_settings
        
        # Create args with only some parameters specified (others will use defaults)
        args = argparse.Namespace(
            source_file_path="source.py",
            test_file_path="test.py",
            code_coverage_report_path=None,  # Will use default
            test_command="pytest",
            test_command_dir=None,  # Will use default
            project_root=None,  # Will use default
            test_file_output_path=None,  # Will use default
            included_files=None,  # Will use default
            coverage_type=None,  # Will use default
            report_filepath=None,  # Will use default
            desired_coverage=90,
            max_iterations=None,  # Will use default
            max_run_time=None,  # Will use default
            model=None,  # Will use default
            api_base=None,  # Will use default
            additional_instructions=None,  # Will use default
            strict_coverage=None,  # Will use default
            run_tests_multiple_times=None,  # Will use default
            run_each_test_separately=None,  # Will use default
            use_report_coverage_feature_flag=None,  # Will use default
            diff_coverage=None,  # Will use default
            branch=None,  # Will use default
            log_db_path=None,  # Will use default
        )
        
        # Create config using from_args_with_defaults
        config = CoverAgentConfig.from_args_with_defaults(args)
        
        # Verify overridden values from args
        assert config.source_file_path == "source.py"
        assert config.test_file_path == "test.py"
        assert config.test_command == "pytest"
        assert config.desired_coverage == 90
        
        # Verify default values from TOML
        assert config.code_coverage_report_path == toml_defaults['code_coverage_report_path']
        assert config.test_command_dir == toml_defaults['test_command_dir']
        assert config.project_root == toml_defaults['project_root']
        assert config.test_file_output_path == toml_defaults['test_file_output_path']
        assert config.included_files == toml_defaults['included_files']
        assert config.coverage_type == toml_defaults['coverage_type']
        assert config.report_filepath == toml_defaults['report_filepath']
        assert config.max_iterations == toml_defaults['max_iterations']
        assert config.max_run_time == toml_defaults['max_run_time']
        assert config.model == toml_defaults['model']
        assert config.api_base == toml_defaults['api_base']
        assert config.additional_instructions == toml_defaults['additional_instructions']
        assert config.strict_coverage == toml_defaults['strict_coverage']
        assert config.run_tests_multiple_times == toml_defaults['run_tests_multiple_times']
        assert config.run_each_test_separately == toml_defaults['run_each_test_separately']
        assert config.use_report_coverage_feature_flag == toml_defaults['use_report_coverage_feature_flag']
        assert config.diff_coverage == toml_defaults['diff_coverage']
        assert config.branch == toml_defaults['branch']
        assert config.log_db_path == toml_defaults['log_db_path']

    @patch("cover_agent.settings.config_schema.get_settings")
    def test_args_override_defaults(self, mock_get_settings):
        """Test that args properly override defaults when both are present."""
        # Create mock settings
        mock_settings = MagicMock()
        mock_toml_config = MagicMock()
        
        # Define TOML default values (use a different set than the test_from_args_with_defaults test)
        toml_defaults = {
            'source_file_path': 'default_source.py',
            'test_file_path': 'default_test.py',
            'code_coverage_report_path': 'default_coverage.xml',
            'test_command': 'default_pytest',
            'test_command_dir': '/default_project',
            'project_root': '/default_project',
            'test_file_output_path': 'default_output.py',
            'included_files': ['default1.py', 'default2.py'],
            'coverage_type': 'default_cobertura',
            'report_filepath': 'default_report.html',
            'desired_coverage': 85,
            'max_iterations': 5,
            'max_run_time': 45,
            'model': 'default-gpt-4o',
            'api_base': 'http://default:11434',
            'additional_instructions': 'default_instructions',
            'strict_coverage': True,
            'run_tests_multiple_times': 2,
            'run_each_test_separately': True,
            'use_report_coverage_feature_flag': True,
            'diff_coverage': True,
            'branch': 'default_main',
            'log_db_path': 'default_test.db'
        }
        
        # Set up the mocks to return our default values
        for key, value in toml_defaults.items():
            setattr(mock_toml_config, key, value)
        
        mock_settings.get.return_value = mock_toml_config
        mock_get_settings.return_value = mock_settings
        
        # Create args with all parameters specified (all should override defaults)
        args = argparse.Namespace(
            source_file_path="override_source.py",
            test_file_path="override_test.py",
            code_coverage_report_path="override_coverage.xml",
            test_command="override_pytest",
            test_command_dir="/override_project",
            project_root="/override_project",
            test_file_output_path="override_output.py",
            included_files=["override1.py", "override2.py"],
            coverage_type="override_cobertura",
            report_filepath="override_report.html",
            desired_coverage=95,
            max_iterations=15,
            max_run_time=60,
            model="override-gpt-4o",
            api_base="http://override:11434",
            additional_instructions="override_instructions",
            strict_coverage=False,
            run_tests_multiple_times=3,
            run_each_test_separately=False,
            use_report_coverage_feature_flag=False,
            diff_coverage=False,
            branch="override_main",
            log_db_path="override_test.db",
        )
        
        # Create config using from_args_with_defaults
        config = CoverAgentConfig.from_args_with_defaults(args)
        
        # Verify all values come from args, not defaults
        assert config.source_file_path == "override_source.py"
        assert config.test_file_path == "override_test.py"
        assert config.code_coverage_report_path == "override_coverage.xml"
        assert config.test_command == "override_pytest"
        assert config.test_command_dir == "/override_project"
        assert config.project_root == "/override_project"
        assert config.test_file_output_path == "override_output.py"
        assert config.included_files == ["override1.py", "override2.py"]
        assert config.coverage_type == "override_cobertura"
        assert config.report_filepath == "override_report.html"
        assert config.desired_coverage == 95
        assert config.max_iterations == 15
        assert config.max_run_time == 60
        assert config.model == "override-gpt-4o"
        assert config.api_base == "http://override:11434"
        assert config.additional_instructions == "override_instructions"
        assert config.strict_coverage is False
        assert config.run_tests_multiple_times == 3
        assert config.run_each_test_separately is False
        assert config.use_report_coverage_feature_flag is False
        assert config.diff_coverage is False
        assert config.branch == "override_main"
        assert config.log_db_path == "override_test.db"

    @patch("cover_agent.settings.config_schema.get_settings")
    def test_handle_none_values(self, mock_get_settings):
        """Test how None values are handled in from_args_with_defaults."""
        # Create mock settings
        mock_settings = MagicMock()
        mock_toml_config = MagicMock()
        
        # Define TOML default values
        toml_defaults = {
            'source_file_path': 'default_source.py',
            'test_file_path': 'default_test.py',
            'code_coverage_report_path': 'default_coverage.xml',
            'test_command': 'default_pytest',
            'test_command_dir': '/default_project',
            'project_root': '/default_project',
            'test_file_output_path': 'default_output.py',
            'included_files': ['default1.py', 'default2.py'],
            'coverage_type': 'default_cobertura',
            'report_filepath': 'default_report.html',
            'desired_coverage': 85,
            'max_iterations': 5,
            'max_run_time': 45,
            'model': 'default-gpt-4o',
            'api_base': 'http://default:11434',
            'additional_instructions': 'default_instructions',
            'strict_coverage': True,
            'run_tests_multiple_times': 2,
            'run_each_test_separately': True,
            'use_report_coverage_feature_flag': True,
            'diff_coverage': True,
            'branch': 'default_main',
            'log_db_path': 'default_test.db'
        }
        
        # Set up the mocks to return our default values
        for key, value in toml_defaults.items():
            setattr(mock_toml_config, key, value)
        
        mock_settings.get.return_value = mock_toml_config
        mock_get_settings.return_value = mock_settings
        
        # Create args with some None values
        args = argparse.Namespace(
            source_file_path=None,  # None value should use default
            test_file_path="test.py",
            code_coverage_report_path="coverage.xml",
            test_command=None,  # None value should use default
            test_command_dir="/project",
            project_root="/project",
            test_file_output_path="test_output.py",
            included_files=None,  # None value should use default
            coverage_type="cobertura",
            report_filepath="report.html",
            desired_coverage=90,
            max_iterations=10,
            max_run_time=30,
            model="gpt-4o",
            api_base="http://localhost:11434",
            additional_instructions="",
            strict_coverage=False,
            run_tests_multiple_times=1,
            run_each_test_separately=False,
            use_report_coverage_feature_flag=False,
            diff_coverage=False,
            branch="main",
            log_db_path="test.db"
        )
        
        # Create config using from_args_with_defaults
        config = CoverAgentConfig.from_args_with_defaults(args)
        
        # Verify None values were replaced with defaults
        assert config.source_file_path == toml_defaults['source_file_path']
        assert config.test_command == toml_defaults['test_command']
        assert config.included_files == toml_defaults['included_files']
        
        # Verify other values came from args
        assert config.test_file_path == "test.py"
        assert config.code_coverage_report_path == "coverage.xml"
        assert config.test_command_dir == "/project"
        assert config.project_root == "/project"
        assert config.test_file_output_path == "test_output.py"
        assert config.coverage_type == "cobertura"
        assert config.report_filepath == "report.html"
        assert config.desired_coverage == 90
        assert config.max_iterations == 10
        assert config.max_run_time == 30
        assert config.model == "gpt-4o"
        assert config.api_base == "http://localhost:11434"
        assert config.additional_instructions == ""
        assert config.strict_coverage is False
        assert config.run_tests_multiple_times == 1
        assert config.run_each_test_separately is False
        assert config.use_report_coverage_feature_flag is False
        assert config.diff_coverage is False
        assert config.branch == "main"
        assert config.log_db_path == "test.db"