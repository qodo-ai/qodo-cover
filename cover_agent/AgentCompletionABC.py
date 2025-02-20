from abc import ABC, abstractmethod
from typing import Tuple


class AgentCompletionABC(ABC):
    """
    Abstract base class for generating AI-driven prompts and invoking LLM calls
    to perform various test analysis and code completion tasks.
    """

    @abstractmethod
    def generate_tests(
        self,
        source_file_name: str,
        max_tests: int,
        source_file_numbered: str,
        code_coverage_report: str,
        language: str,
        test_file: str,
        test_file_name: str,
        testing_framework: str,
        additional_instructions_text: str = None,
        additional_includes_section: str = None,
        failed_tests_section: str = None,
    ) -> Tuple[str, int, int, str]:
        """
        Generates a prompt and invokes an LLM call to create additional unit tests.

        This function constructs a prompt that provides the AI with existing
        test cases, a source file, and a coverage report to suggest new tests
        that improve coverage. It then sends the prompt to an LLM and retrieves
        generated test cases.

        Args:
            source_file_name (str): The name of the source file under test.
            max_tests (int): The maximum number of new tests to generate.
            source_file_numbered (str): The source file content with line numbers.
            code_coverage_report (str): The report detailing uncovered lines.
            language (str): The programming language of the code.
            test_file (str): The existing test file content.
            test_file_name (str): The name of the test file.
            testing_framework (str): The test framework being used.
            additional_instructions_text (str, optional): Additional user-provided instructions.
            additional_includes_section (str, optional): Additional includes for context.
            failed_tests_section (str, optional): Previously failed test cases.

        Returns:
            Tuple[str, int, int, str]:
                - Generated test cases (YAML string)
                - Input token count
                - Output token count
                - The generated prompt string
        """
        pass

    @abstractmethod
    def analyze_test_failure(
        self,
        source_file_name: str,
        source_file: str,
        processed_test_file: str,
        stdout: str,
        stderr: str,
        test_file_name: str,
    ) -> Tuple[str, int, int, str]:
        """
        Generates a prompt and invokes an LLM call to analyze test failures.

        This function constructs a prompt to identify the root cause of test
        failures based on test outputs, error logs, and source/test file content.
        It then sends the prompt to an LLM and retrieves an analysis of the failure.

        Args:
            source_file_name (str): The name of the source file under test.
            source_file (str): The content of the source file.
            processed_test_file (str): The processed test file content.
            stdout (str): Standard output from the test run.
            stderr (str): Error output from the test run.
            test_file_name (str): The name of the test file.

        Returns:
            Tuple[str, int, int, str]:
                - Failure analysis result (YAML string)
                - Input token count
                - Output token count
                - The generated prompt string
        """
        pass

    @abstractmethod
    def analyze_test_insert_line(
        self,
        language: str,
        test_file_numbered: str,
        test_file_name: str,
        additional_instructions_text: str = None,
    ) -> Tuple[str, int, int, str]:
        """
        Generates a prompt and invokes an LLM call to determine the correct line to insert new test cases.

        This function constructs a prompt that guides the LLM in analyzing an
        existing test file and determining where new test cases should be inserted.

        Args:
            language (str): The programming language of the test file.
            test_file_numbered (str): The test file content with line numbers.
            test_file_name (str): The name of the test file.
            additional_instructions_text (str, optional): Additional user-provided instructions.

        Returns:
            Tuple[str, int, int, str]:
                - Suggested insertion line number (YAML string)
                - Input token count
                - Output token count
                - The generated prompt string
        """
        pass

    @abstractmethod
    def analyze_test_against_context(
        self,
        language: str,
        test_file_content: str,
        test_file_name_rel: str,
        context_files_names_rel: str,
    ) -> Tuple[str, int, int, str]:
        """
        Generates a prompt and invokes an LLM call to validate a test file against context files.

        This function constructs a prompt to determine whether a test file is
        indeed a unit test and which source file it primarily targets.
        It then sends the prompt to an LLM and retrieves an evaluation.

        Args:
            language (str): The programming language of the test file.
            test_file_content (str): The content of the test file.
            test_file_name_rel (str): The relative name of the test file.
            context_files_names_rel (str): The names of context files in the project.

        Returns:
            Tuple[str, int, int, str]:
                - Test validation result (YAML string)
                - Input token count
                - Output token count
                - The generated prompt string
        """
        pass

    @abstractmethod
    def adapt_test_command_for_a_single_test_via_ai(
        self,
        test_file_relative_path: str,
        test_command: str,
        project_root_dir: str,
    ) -> Tuple[str, int, int, str]:
        """
        Generates a prompt and invokes an LLM call to modify a test command to run a single test file.

        This function constructs a prompt that guides an LLM to adapt an
        existing test command so it runs only a specific test file while
        preserving all other parameters. The prompt is then sent to the LLM
        to retrieve the modified command.

        Args:
            test_file_relative_path (str): The relative path to the test file.
            test_command (str): The original test execution command.
            project_root_dir (str): The root directory of the project.

        Returns:
            Tuple[str, int, int, str]:
                - Modified test command (YAML string)
                - Input token count
                - Output token count
                - The generated prompt string
        """
        pass
