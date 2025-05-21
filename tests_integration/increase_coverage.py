import os
import sys


# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cover_agent.cover_agent import CoverAgent


# List of source/test files to iterate over:
SOURCE_TEST_FILE_LIST = [
    # ["cover_agent/agent_completion_abc.py", "tests/test_agent_completion_abc.py"],
    # ["cover_agent/ai_caller.py", "tests/test_ai_caller.py"],
    # ["cover_agent/cover_agent.py", "tests/test_cover_agent.py"],
    ["cover_agent/coverage_processor.py", "tests/test_coverage_processor.py"],
    # ["cover_agent/custom_logger.py", ""],
    # ["cover_agent/default_agent_completion.py", "tests/test_default_agent_completion.py"],
    # ["cover_agent/file_preprocessor.py", "tests/test_file_preprocessor.py"],
    # ["cover_agent/main.py", "tests/test_main.py"],
    # ["cover_agent/report_generator.py", "tests/test_report_generator.py"],
    # ["cover_agent/runner.py", "tests/test_runner.py"],
    # ["cover_agent/settings/config_loader.py", ""],
    # ["cover_agent/unit_test_db.py", "tests/test_unit_test_db.py"],
    ["cover_agent/unit_test_generator.py", "tests/test_unit_test_generator.py"],
    ["cover_agent/unit_test_validator.py", "tests/test_unit_test_validator.py"],
    # ["cover_agent/utils.py", "tests/test_load_yaml.py"],
    # ["cover_agent/version.py", "tests/test_version.py"],
]


class Args:
    def __init__(self, source_file_path, test_file_path):
        self.source_file_path = source_file_path
        self.test_file_path = test_file_path
        self.test_file_output_path = ""
        self.code_coverage_report_path = "coverage.xml"
        self.test_command = f"poetry run pytest --cov=cover_agent --cov-report=xml  --timeout=30 --disable-warnings"
        self.test_command_dir = os.getcwd()
        self.included_files = None
        self.coverage_type = "cobertura"
        self.report_filepath = "test_results.html"
        self.desired_coverage = 100
        self.max_iterations = 3
        self.additional_instructions = ""
        self.model = "claude-3-7-sonnet-20250219"
        # self.model = "o1-mini"
        self.api_base = "http://localhost:11434"
        self.prompt_only = False
        self.strict_coverage = False
        self.run_tests_multiple_times = 1
        self.use_report_coverage_feature_flag = False
        self.log_db_path = "increase_project_coverage.db"
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.branch = "main"
        self.diff_coverage = False
        self.run_each_test_separately = False
        self.max_run_time_sec = 30


if __name__ == "__main__":
    # Iterate through list of source and test files to run Cover Agent
    for source_file, test_file in SOURCE_TEST_FILE_LIST:
        # Print a banner for the current source file
        banner = f"Testing source file: {source_file}"
        print("\n" + "*" * len(banner))
        print(banner)
        print("*" * len(banner) + "\n")

        args = Args(source_file, test_file)
        agent = CoverAgent(args)
        agent.run()
