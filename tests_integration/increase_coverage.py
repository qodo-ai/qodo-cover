import os
import sys

# Add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cover_agent.CoverAgent import CoverAgent

# List of source/test files to iterate over:
SOURCE_TEST_FILE_LIST = [
    # ["cover_agent/AICaller.py", "tests/test_AICaller.py"],
    # ["cover_agent/CoverAgent.py", "tests/test_CoverAgent.py"],
    # ["cover_agent/CoverageProcessor.py", "tests/test_CoverageProcessor.py"],
    # ["cover_agent/CustomLogger.py", ""],
    # ["cover_agent/FilePreprocessor.py", "tests/test_FilePreprocessor.py"],
    # ["cover_agent/ReportGenerator.py", "tests/test_ReportGenerator.py"],
    # ["cover_agent/Runner.py", "tests/test_Runner.py"],
    # ["cover_agent/UnitTestDB.py", "tests/test_UnitTestDB.py"],
    # ["cover_agent/UnitTestGenerator.py", "tests/test_UnitTestGenerator.py"],
    # ["cover_agent/main.py", "tests/test_main.py"],
    # ["cover_agent/settings/config_loader.py", ""],
    # ["cover_agent/utils.py", "tests/test_load_yaml.py"],
    # ["cover_agent/version.py", "tests/test_version.py"],
    # ["cover_agent/DefaultAgentCompletion.py", "tests/test_DefaultAgentCompletion.py"],
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
        self.max_iterations = 5
        self.additional_instructions = ""
        self.model = "claude-3-5-sonnet-20241022"
        # self.model = "o1-mini"
        self.api_base = "http://localhost:11434"
        self.prompt_only = False
        self.strict_coverage = False
        self.run_tests_multiple_times = 1
        self.use_report_coverage_feature_flag = False
        self.log_db_path = "increase_project_coverage.db"
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        self.branch = "main"
        self.diff_coverage = False
        self.run_each_test_separately = False


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
