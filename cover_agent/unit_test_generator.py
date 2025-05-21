import json
import os

from typing import Optional

from cover_agent.agent_completion_abc import AgentCompletionABC
from cover_agent.custom_logger import CustomLogger
from cover_agent.file_preprocessor import FilePreprocessor
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import load_yaml


class UnitTestGenerator:
    def __init__(
        self,
        source_file_path: str,
        test_file_path: str,
        code_coverage_report_path: str,
        test_command: str,
        llm_model: str,
        agent_completion: AgentCompletionABC,
        test_command_dir: str = os.getcwd(),
        included_files: list = None,
        coverage_type="cobertura",
        additional_instructions: str = "",
        use_report_coverage_feature_flag: bool = False,
        project_root: str = "",
        logger: Optional[CustomLogger] = None,
        generate_log_files: bool = True,
    ):
        """
        Initialize the UnitTestGenerator class with the provided parameters.

        Parameters:
            source_file_path (str): The path to the source file being tested.
            test_file_path (str): The path to the test file where generated tests will be written.
            code_coverage_report_path (str): The path to the code coverage report file.
            test_command (str): The command to run tests.
            llm_model (str): The language model to be used for test generation.
            agent_completion (AgentCompletionABC): The agent completion object to be used for test generation.
            api_base (str, optional): The base API url to use in case model is set to Ollama or Hugging Face. Defaults to an empty string.
            test_command_dir (str, optional): The directory where the test command should be executed. Defaults to the current working directory.
            included_files (str, optional): Additional files to include (raw). Defaults to ""
            coverage_type (str, optional): The type of coverage report. Defaults to "cobertura".
            desired_coverage (int, optional): The desired coverage percentage. Defaults to 90.
            additional_instructions (str, optional): Additional instructions for test generation. Defaults to an empty string.
            use_report_coverage_feature_flag (bool, optional): Setting this to True considers the coverage of all the files in the coverage report.
                                                               This means we consider a test as good if it increases coverage for a different
                                                               file other than the source file. Defaults to False.
            logger (CustomLogger, optional): The logger object for logging messages.
            generate_log_files (bool): Whether or not to generate logs.

        Returns:
            None
        """
        # Class variables
        self.project_root = project_root
        self.source_file_path = source_file_path
        self.test_file_path = test_file_path
        self.code_coverage_report_path = code_coverage_report_path
        self.test_command = test_command
        self.test_command_dir = test_command_dir
        self.included_files = included_files
        self.coverage_type = coverage_type
        self.additional_instructions = additional_instructions
        self.language = self.get_code_language(source_file_path)
        self.use_report_coverage_feature_flag = use_report_coverage_feature_flag
        self.last_coverage_percentages = {}
        self.llm_model = llm_model
        self.agent_completion = agent_completion
        self.generate_log_files = generate_log_files

        # Get the logger instance from CustomLogger
        self.logger = logger or CustomLogger.get_logger(__name__, generate_log_files=self.generate_log_files)

        # States to maintain within this class
        self.preprocessor = FilePreprocessor(self.test_file_path)
        self.total_input_token_count = 0
        self.total_output_token_count = 0
        self.testing_framework = "Unknown"
        self.code_coverage_report = ""

        # Read self.source_file_path into a string
        with open(self.source_file_path, "r") as f:
            self.source_code = f.read()

        with open(self.test_file_path, "r") as f:
            self.test_code = f.read()

    def get_code_language(self, source_file_path):
        """
        Get the programming language based on the file extension of the provided source file path.

        Parameters:
            source_file_path (str): The path to the source file for which the programming language needs to be determined.

        Returns:
            str: The programming language inferred from the file extension of the provided source file path. Defaults to 'unknown' if the language cannot be determined.
        """
        # Retrieve the mapping of languages to their file extensions from settings
        language_extension_map_org = get_settings().language_extension_map_org

        # Initialize a dictionary to map file extensions to their corresponding languages
        extension_to_language = {}

        # Populate the extension_to_language dictionary
        for language, extensions in language_extension_map_org.items():
            for ext in extensions:
                extension_to_language[ext] = language

        # Extract the file extension from the source file path
        extension_s = "." + source_file_path.rsplit(".")[-1]

        # Initialize the default language name as 'unknown'
        language_name = "unknown"

        # Check if the extracted file extension is in the dictionary
        if extension_s and (extension_s in extension_to_language):
            # Set the language name based on the file extension
            language_name = extension_to_language[extension_s]

        # Return the language name in lowercase
        return language_name.lower()

    def check_for_failed_test_runs(self, failed_test_runs):
        """
        Processes the failed test runs and returns a formatted string with details of the failed tests.

        Args:
            failed_test_runs (list): A list of dictionaries containing information about failed test runs.

        Returns:
            str: A formatted string with details of the failed tests.
        """
        if not failed_test_runs:
            failed_test_runs_value = ""
        else:
            failed_test_runs_value = ""
            try:
                for failed_test in failed_test_runs:
                    failed_test_dict = failed_test.get("code", {})
                    if not failed_test_dict:
                        continue
                    # dump dict to str
                    code = json.dumps(failed_test_dict)
                    error_message = failed_test.get("error_message", None)
                    failed_test_runs_value += f"Failed Test:\n```\n{code}\n```\n"
                    if error_message:
                        failed_test_runs_value += f"Test execution error analysis:\n{error_message}\n\n\n"
                    else:
                        failed_test_runs_value += "\n\n"
            except Exception as e:
                self.logger.error(f"Error processing failed test runs: {e}")
                failed_test_runs_value = ""

        return failed_test_runs_value

    def generate_tests(self, failed_test_runs, language, testing_framework, code_coverage_report):
        """
        Generate tests using the AI model based on the constructed prompt.

        This method generates tests by calling the AI model with the constructed prompt.
        It handles both dry run and actual test generation scenarios. In a dry run, it returns canned test responses.
        In the actual run, it calls the AI model with the prompt and processes the response to extract test
        information such as test tags, test code, test name, and test behavior.

        Parameters:
            max_tokens (int, optional): The maximum number of tokens to use for generating tests. Defaults to 4096.

        Returns:
            dict: A dictionary containing the generated tests with test tags, test code, test name, and test behavior. If an error occurs during test generation, an empty dictionary is returned.

        Raises:
            Exception: If there is an error during test generation, such as a parsing error while processing the AI model response.
        """
        failed_test_runs_value = self.check_for_failed_test_runs(failed_test_runs)

        max_tests_per_run = get_settings().get("default").get("max_tests_per_run", 4)
        response, prompt_token_count, response_token_count, self.prompt = self.agent_completion.generate_tests(
            source_file_name=os.path.relpath(self.source_file_path, self.project_root),
            max_tests=max_tests_per_run,
            source_file_numbered="\n".join(f"{i + 1} {line}" for i, line in enumerate(self.source_code.split("\n"))),
            code_coverage_report=code_coverage_report,
            additional_instructions_text=self.additional_instructions,
            additional_includes_section=self.included_files,
            language=language,
            test_file=self.test_code,
            failed_tests_section=failed_test_runs_value,
            test_file_name=os.path.relpath(self.test_file_path, self.project_root),
            testing_framework=testing_framework,
        )

        self.total_input_token_count += prompt_token_count
        self.total_output_token_count += response_token_count
        try:
            tests_dict = load_yaml(
                response,
                keys_fix_yaml=["test_tags", "test_code", "test_name", "test_behavior"],
            )
            if tests_dict is None:
                return {}
        except Exception as e:
            self.logger.error(f"Error during test generation: {e}")
            # Record the error as a failed test attempt
            fail_details = {
                "status": "FAIL",
                "reason": f"Parsing error: {e}",
                "exit_code": None,  # No exit code as it's a parsing issue
                "stderr": str(e),
                "stdout": "",  # No output expected from a parsing error
                "test": response,  # Use the response that led to the error
            }
            # self.failed_test_runs.append(fail_details)
            tests_dict = []

        return tests_dict
