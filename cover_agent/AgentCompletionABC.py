from abc import ABC, abstractmethod
from typing import Tuple


class AgentCompletionABC(ABC):
    """
    Abstract base class for AI-driven prompt handling. Each method accepts
    specific input parameters (e.g. source/test content, logs, coverage data)
    and returns a tuple containing the AI response, along with additional
    metadata (e.g. token usage and the generated prompt).
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
        Generates additional unit tests to improve coverage or handle edge cases.

        Args:
            source_file_name (str): Name of the source file under test.
            max_tests (int): Maximum number of test functions to propose.
            source_file_numbered (str): The source code with line numbers.
            code_coverage_report (str): Coverage details highlighting untested lines.
            language (str): The programming language (e.g. "python", "java").
            test_file (str): Contents of the existing test file.
            test_file_name (str): The name/path of the test file.
            testing_framework (str): The test framework in use (e.g. "pytest", "junit").
            additional_instructions_text (str, optional): Extra instructions or context.
            additional_includes_section (str, optional): Additional code or includes.
            failed_tests_section (str, optional): Details of failed tests to consider.

        Returns:
            Tuple[str, int, int, str]:
                A 4-element tuple containing:
                - The AI-generated test suggestions (string),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (string).
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
        Analyzes the output of a failed test to determine possible causes and
        recommended fixes.

        Args:
            source_file_name (str): Name of the source file being tested.
            source_file (str): Raw content of the source file.
            processed_test_file (str): Content of the failing test file (pre-processed).
            stdout (str): Captured standard output from the test run.
            stderr (str): Captured standard error from the test run.
            test_file_name (str): Name/path of the failing test file.

        Returns:
            Tuple[str, int, int, str]:
                A 4-element tuple containing:
                - The AI-generated analysis or explanation (string),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (string).
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
        Determines the correct placement for inserting new test cases into
        an existing test file.

        Args:
            language (str): The programming language of the test file.
            test_file_numbered (str): The test file content, labeled with line numbers.
            test_file_name (str): Name/path of the test file.
            additional_instructions_text (str, optional): Any extra instructions or context.

        Returns:
            Tuple[str, int, int, str]:
                A 4-element tuple containing:
                - The AI-generated suggestion or instructions (string),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (string).
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
        Evaluates a test file against a set of related context files to identify:
        1. If it is a unit test,
        2. Which context file the test is primarily targeting.

        Args:
            language (str): The programming language of the test file.
            test_file_content (str): Raw content of the test file under review.
            test_file_name_rel (str): Relative path/name of the test file.
            context_files_names_rel (str): One or more file names related to the context.

        Returns:
            Tuple[str, int, int, str]:
                A 4-element tuple containing:
                - The AI-generated classification or analysis (string),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (string).
        """
        pass

    @abstractmethod
    def analyze_suite_test_headers_indentation(
        self,
        language: str,
        test_file_name: str,
        test_file: str,
    ) -> Tuple[str, int, int, str]:
        """
        Analyzes an existing test suite to determine its indentation style,
        the number of existing tests, and potentially the testing framework.

        Args:
            language (str): The programming language of the test file.
            test_file_name (str): Name/path of the test file.
            test_file (str): Raw content of the test file.

        Returns:
            Tuple[str, int, int, str]:
                A 4-element tuple containing:
                - The AI-generated suite analysis (string),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (string).
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
        Adapts an existing test command line to run only a single test file,
        preserving other relevant flags and arguments where possible.

        Args:
            test_file_relative_path (str): Path to the specific test file to be isolated.
            test_command (str): The original command line used for running multiple tests.
            project_root_dir (str): Root directory of the project.

        Returns:
            Tuple[str, int, int, str]:
                A 4-element tuple containing:
                - The AI-generated single-test command line (string) or None upon failure.
                - The input token count (int).
                - The output token count (int).
                - The final constructed prompt (string).
        """
        pass
