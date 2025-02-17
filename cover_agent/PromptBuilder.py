import logging
import os

from jinja2 import Environment, StrictUndefined

from cover_agent.AICaller import AICaller
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import load_yaml

MAX_TESTS_PER_RUN = 4


class PromptBuilder:
    """
    Builds formatted prompts for AI model interaction by combining source code, test files,
    and coverage reports.

    The PromptBuilder class handles the construction of prompts by reading files,
    formatting content, and replacing placeholders with actual content to generate
    system and user prompts for AI interaction.

    Attributes:
        project_root (str): Root directory of the project
        source_file_path (str): Path to source code file
        test_file_path (str): Path to test file
        source_file_name_rel (str): Relative path to source file from project root
        test_file_name_rel (str): Relative path to test file from project root
        source_file (str): Content of source file
        test_file (str): Content of test file
        source_file_numbered (str): Source file content with line numbers
        test_file_numbered (str): Test file content with line numbers
        code_coverage_report (str): Code coverage report content
        included_files (str): Additional included files content (raw, no extra formatting)
        additional_instructions (str): Additional instructions (raw, no extra formatting)
        failed_test_runs (str): Failed test runs history (raw, no extra formatting)
        language (str): Programming language being used
        testing_framework (str): Testing framework being used
        stdout_from_run (str): Standard output from test runs
        stderr_from_run (str): Standard error from test runs
        processed_test_file (str): Processed test file content

    Methods:
        __init__(source_file_path: str, test_file_path: str, code_coverage_report: str,
                 included_files: str = "", additional_instructions: str = "",
                 failed_test_runs: str = "", language: str = "python",
                 testing_framework: str = "NOT KNOWN", project_root: str = ""):
            Initializes the PromptBuilder with file paths, settings, and raw content.

        _read_file(file_path: str) -> str:
            Reads and returns contents of a file.

        build_prompt(file: str, source_file_name: str = None, test_file_name: str = None,
                     source_file_numbered: str = None, test_file_numbered: str = None,
                     source_file: str = None, test_file: str = None,
                     code_coverage_report: str = None, additional_includes_section: str = None,
                     failed_tests_section: str = None, additional_instructions_text: str = None,
                     language: str = None, max_tests: int = MAX_TESTS_PER_RUN,
                     testing_framework: str = None, stdout: str = None,
                     stderr: str = None, processed_test_file: str = None) -> dict:
            Builds and returns a dictionary containing system and user prompts.
    """

    def __init__(
        self,
        source_file_path: str,
        test_file_path: str,
        code_coverage_report: str,
        included_files: str = "",
        additional_instructions: str = "",
        failed_test_runs: str = "",
        language: str = "python",
        testing_framework: str = "NOT KNOWN",
        project_root: str = "",
    ):
        """
        Initialize a new PromptBuilder instance.

        Processes file paths and content, adds line numbers, and stores optional
        sections as raw strings.

        Args:
            source_file_path (str): Path to the source code file
            test_file_path (str): Path to the test file
            code_coverage_report (str): Coverage report content
            included_files (str, optional): Additional files to include (raw). Defaults to ""
            additional_instructions (str, optional): Extra instructions for the prompt (raw). Defaults to ""
            failed_test_runs (str, optional): History of failed test runs (raw). Defaults to ""
            language (str, optional): Programming language being used. Defaults to "python"
            testing_framework (str, optional): Testing framework being used. Defaults to "NOT KNOWN"
            project_root (str, optional): Root directory of the project. Defaults to ""
        """
        self.project_root = project_root
        self.source_file_path = source_file_path
        self.test_file_path = test_file_path
        self.source_file_name_rel = os.path.relpath(source_file_path, project_root)
        self.test_file_name_rel = os.path.relpath(test_file_path, project_root)
        self.source_file = self._read_file(source_file_path)
        self.test_file = self._read_file(test_file_path)
        self.code_coverage_report = code_coverage_report
        self.language = language
        self.testing_framework = testing_framework

        # Add line numbers to each line in 'source_file' and 'test_file'.
        self.source_file_numbered = "\n".join(
            f"{i + 1} {line}" for i, line in enumerate(self.source_file.split("\n"))
        )
        self.test_file_numbered = "\n".join(
            f"{i + 1} {line}" for i, line in enumerate(self.test_file.split("\n"))
        )

        # Store optional sections directly as raw strings
        self.included_files = included_files
        self.additional_instructions = additional_instructions
        self.failed_test_runs = failed_test_runs

        # Defaults for run outputs / processed tests
        self.stdout_from_run = ""
        self.stderr_from_run = ""
        self.processed_test_file = ""

    def _read_file(self, file_path: str) -> str:
        """
        Helper method to read file contents.

        Args:
            file_path (str): Path to the file to be read.

        Returns:
            str: The content of the file, or an error message if reading fails.
        """
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    def build_prompt(
        self,
        file: str,
        source_file_name: str = None,
        test_file_name: str = None,
        source_file_numbered: str = None,
        test_file_numbered: str = None,
        source_file: str = None,
        test_file: str = None,
        code_coverage_report: str = None,
        additional_includes_section: str = None,
        failed_tests_section: str = None,
        additional_instructions_text: str = None,
        language: str = None,
        max_tests: int = MAX_TESTS_PER_RUN,
        testing_framework: str = None,
        stdout: str = None,
        stderr: str = None,
        processed_test_file: str = None,
    ) -> dict:
        """
        Builds a custom prompt by replacing placeholders with actual content from files and settings.

        Args:
            file (str): The TOML key to retrieve system and user prompt templates.
            source_file_name (str, optional): Override for the source file name.
            test_file_name (str, optional): Override for the test file name.
            source_file_numbered (str, optional): Override for line-numbered source code.
            test_file_numbered (str, optional): Override for line-numbered test code.
            source_file (str, optional): Override for raw source code.
            test_file (str, optional): Override for raw test file.
            code_coverage_report (str, optional): Override for coverage data.
            additional_includes_section (str, optional): Override for any included files section.
            failed_tests_section (str, optional): Override for any failed tests data.
            additional_instructions_text (str, optional): Override for extra instructions text.
            language (str, optional): Override for the programming language.
            max_tests (int, optional): Override for the max tests to generate.
            testing_framework (str, optional): Override for the testing framework used.
            stdout (str, optional): Override for STDOUT from a test run.
            stderr (str, optional): Override for STDERR from a test run.
            processed_test_file (str, optional): Override for processed test file content.

        Returns:
            dict: A dictionary containing the rendered system and user prompts.
        """

        # Use provided values or fallback to instance attributes
        variables = {
            "source_file_name": source_file_name or self.source_file_name_rel,
            "test_file_name": test_file_name or self.test_file_name_rel,
            "source_file_numbered": source_file_numbered or self.source_file_numbered,
            "test_file_numbered": test_file_numbered or self.test_file_numbered,
            "source_file": source_file or self.source_file,
            "test_file": test_file or self.test_file,
            "code_coverage_report": code_coverage_report or self.code_coverage_report,
            "additional_includes_section": (
                additional_includes_section
                if additional_includes_section
                else self.included_files
            ),
            "failed_tests_section": (
                failed_tests_section if failed_tests_section else self.failed_test_runs
            ),
            "additional_instructions_text": (
                additional_instructions_text
                if additional_instructions_text
                else self.additional_instructions
            ),
            "language": language or self.language,
            "max_tests": max_tests,
            "testing_framework": testing_framework or self.testing_framework,
            "stdout": stdout or self.stdout_from_run,
            "stderr": stderr or self.stderr_from_run,
            "processed_test_file": processed_test_file or self.processed_test_file,
        }

        environment = Environment(undefined=StrictUndefined)
        try:
            settings = get_settings().get(file)
            if (
                not settings
                or not hasattr(settings, "system")
                or not hasattr(settings, "user")
            ):
                logging.error(f"Could not find settings for prompt file: {file}")
                return {"system": "", "user": ""}

            system_prompt = environment.from_string(settings.system).render(variables)
            user_prompt = environment.from_string(settings.user).render(variables)
        except Exception as e:
            logging.error(f"Error rendering prompt: {e}")
            return {"system": "", "user": ""}

        return {"system": system_prompt, "user": user_prompt}


def adapt_test_command_for_a_single_test_via_ai(
    args, test_file_relative_path, test_command
):
    """
    Modifies a test command so that it targets only a single test file.

    Args:
        args: Command-line arguments or object with necessary attributes.
        test_file_relative_path (str): The relative path to the test file.
        test_command (str): The command line that runs all tests.

    Returns:
        str or None: A modified command line that runs only one test, or None on error.
    """
    try:
        variables = {
            "project_root_dir": args.test_command_dir,
            "test_file_relative_path": test_file_relative_path,
            "test_command": test_command,
        }
        ai_caller = AICaller(model=args.model)
        environment = Environment(undefined=StrictUndefined)

        system_prompt = environment.from_string(
            get_settings().adapt_test_command_for_a_single_test_via_ai.system
        ).render(variables)

        user_prompt = environment.from_string(
            get_settings().adapt_test_command_for_a_single_test_via_ai.user
        ).render(variables)

        response, prompt_token_count, response_token_count = ai_caller.call_model(
            prompt={"system": system_prompt, "user": user_prompt}, stream=False
        )
        response_yaml = load_yaml(response)
        new_command_line = response_yaml["new_command_line"].strip()
        return new_command_line
    except Exception as e:
        logging.error(f"Error adapting test command: {e}")
        return None
