from dataclasses import dataclass
from typing import List, Optional
import argparse
from cover_agent.settings.config_loader import get_settings


@dataclass
class CoverAgentConfig:
    """Configuration dataclass for Cover Agent settings"""
    
    # Required file paths
    source_file_path: str
    test_file_path: str
    code_coverage_report_path: str
    
    # Test execution settings
    test_command: str
    test_command_dir: str
    
    # Project settings
    project_root: str
    test_file_output_path: str
    
    # Coverage settings
    included_files: Optional[List[str]]
    coverage_type: str
    report_filepath: str
    desired_coverage: int
    
    # Execution limits
    max_iterations: int
    max_run_time: int
    
    # LLM model configuration
    model: str
    api_base: str
    additional_instructions: str
    
    # Test execution options
    strict_coverage: bool
    run_tests_multiple_times: int
    run_each_test_separately: bool
    
    # Coverage evaluation modes (mutually exclusive)
    use_report_coverage_feature_flag: bool
    diff_coverage: bool
    
    # Git branch for diff coverage
    branch: str
    
    # Logging settings
    log_db_path: str
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'CoverAgentConfig':
        """
        Create a CoverAgentConfig instance from command line arguments. No defaults are applied.
        This method is used when all required parameters are provided via command line.
        
        Parameters:
            args (argparse.Namespace): Command line arguments parsed from main.py
            
        Returns:
            CoverAgentConfig: An initialized configuration object
        """
        return cls(
            source_file_path=args.source_file_path,
            test_file_path=args.test_file_path,
            code_coverage_report_path=args.code_coverage_report_path,
            test_command=args.test_command,
            test_command_dir=args.test_command_dir,
            project_root=args.project_root,
            test_file_output_path=args.test_file_output_path,
            included_files=args.included_files,
            coverage_type=args.coverage_type,
            report_filepath=args.report_filepath,
            desired_coverage=args.desired_coverage,
            max_iterations=args.max_iterations,
            max_run_time=args.max_run_time,
            model=args.model,
            api_base=args.api_base,
            additional_instructions=args.additional_instructions,
            strict_coverage=args.strict_coverage,
            run_tests_multiple_times=args.run_tests_multiple_times,
            run_each_test_separately=args.run_each_test_separately,
            use_report_coverage_feature_flag=args.use_report_coverage_feature_flag,
            diff_coverage=args.diff_coverage,
            branch=args.branch,
            log_db_path=args.log_db_path
        )
    
    @classmethod
    def from_args_with_defaults(cls, args: argparse.Namespace) -> 'CoverAgentConfig':
        """
        Create a CoverAgentConfig instance using TOML defaults for missing values.
        
        This method prioritizes command-line arguments when available, but falls
        back to configuration.toml defaults for any missing values.
        
        Parameters:
            args (argparse.Namespace): Command line arguments parsed from main.py
            
        Returns:
            CoverAgentConfig: A configuration object with values from both sources
        """
        # First load defaults from TOML
        toml_config = get_settings().get('default')
        
        # Create a dictionary from the args Namespace
        args_dict = vars(args)
        
        # Create a dictionary from the TOML defaults
        toml_dict = {
            'source_file_path': toml_config.source_file_path,
            'test_file_path': toml_config.test_file_path,
            'code_coverage_report_path': toml_config.code_coverage_report_path,
            'test_command': toml_config.test_command,
            'test_command_dir': toml_config.test_command_dir,
            'project_root': toml_config.project_root,
            'test_file_output_path': toml_config.test_file_output_path,
            'included_files': toml_config.included_files,
            'coverage_type': toml_config.coverage_type,
            'report_filepath': toml_config.report_filepath,
            'desired_coverage': toml_config.desired_coverage,
            'max_iterations': toml_config.max_iterations,
            'max_run_time': toml_config.max_run_time,
            'model': toml_config.model,
            'api_base': toml_config.api_base,
            'additional_instructions': toml_config.additional_instructions,
            'strict_coverage': toml_config.strict_coverage,
            'run_tests_multiple_times': toml_config.run_tests_multiple_times,
            'run_each_test_separately': toml_config.run_each_test_separately,
            'use_report_coverage_feature_flag': toml_config.use_report_coverage_feature_flag,
            'diff_coverage': toml_config.diff_coverage,
            'branch': toml_config.branch,
            'log_db_path': toml_config.log_db_path
        }
        
        # Merge the two dictionaries, prioritizing args values when they exist
        merged_dict = toml_dict.copy()
        for k, v in args_dict.items():
            if v is not None and hasattr(args, k):
                merged_dict[k] = v
        
        # Create config from the merged dictionary
        return cls(**merged_dict)