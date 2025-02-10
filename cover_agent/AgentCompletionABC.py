from abc import ABC, abstractmethod
from typing import Tuple


class AgentCompletionABC(ABC):
    """
    Abstract base class for AI-driven prompt handling.

    Each method returns a tuple of:
    (AI-generated content, input token count, output token count, generated prompt dictionary)
    except for 'adapt_test_command_for_a_single_test_via_ai()', which returns just a string.
    """

    @abstractmethod
    def generate_tests(
        self,
        source_file_numbered: str,
        test_file: str,
        code_coverage_report: str,
        testing_framework: str,
        additional_instructions_text: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Generates additional unit tests to improve test coverage.

        Args:
            source_file_numbered (str): The source file content with line numbers.
            test_file (str): The existing test file content.
            code_coverage_report (str): The code coverage report content.
            testing_framework (str): The testing framework name (e.g. pytest, unittest).
            additional_instructions_text (str): Any extra user instructions to incorporate.

        Returns:
            Tuple[str, int, int, dict]:
                - str: AI-generated test cases (usually in YAML),
                - int: The input token count,
                - int: The output token count,
                - dict: The rendered prompt (system/user).
        """
        pass

    @abstractmethod
    def analyze_test_failure(
        self,
        source_file: str,
        processed_test_file: str,
        stdout: str,
        stderr: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Analyzes the stdout/stderr from a test run and provides a concise explanation.

        Args:
            source_file (str): The main source file content.
            processed_test_file (str): The existing test file content (potentially processed).
            stdout (str): Captured standard output from the failing test run.
            stderr (str): Captured standard error from the failing test run.

        Returns:
            Tuple[str, int, int, dict]:
                - str: AI-generated analysis of the failure (plain text or short YAML),
                - int: The input token count,
                - int: The output token count,
                - dict: The rendered prompt (system/user).
        """
        pass

    @abstractmethod
    def analyze_test_insert_line(
        self,
        test_file_numbered: str,
        language: str,
        testing_framework: str,
        additional_instructions_text: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Determines where (in line-numbered test code) new tests should be inserted.

        Args:
            test_file_numbered (str): The existing test file content, with line numbers added.
            language (str): Programming language of the test file.
            testing_framework (str): Which testing framework is used.
            additional_instructions_text (str): Any additional user instructions.

        Returns:
            Tuple[str, int, int, dict]:
                - str: AI-generated YAML analysis indicating the line number for insertion, etc.
                - int: The input token count,
                - int: The output token count,
                - dict: The rendered prompt (system/user).
        """
        pass

    @abstractmethod
    def analyze_test_against_context(
        self,
        test_file_content: str,
        context_files_names_rel: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Determines if a test file is a unit test and which context file it tests.

        Args:
            test_file_content (str): The content of the test file.
            context_files_names_rel (str): A list of context file names (relative paths).

        Returns:
            Tuple[str, int, int, dict]:
                - str: AI-generated YAML summarizing whether it's a unit test and the main file tested
                - int: The input token count,
                - int: The output token count,
                - dict: The rendered prompt (system/user).
        """
        pass

    @abstractmethod
    def analyze_suite_test_headers_indentation(
        self,
        test_file: str,
        language: str,
        testing_framework: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Determines indentation style and other metadata about a test suite.

        Args:
            test_file (str): The existing test file content.
            language (str): The programming language of the test file.
            testing_framework (str): The testing framework used.

        Returns:
            Tuple[str, int, int, dict]:
                - str: AI-generated YAML summarizing language, framework, indentation level, etc.
                - int: The input token count,
                - int: The output token count,
                - dict: The rendered prompt (system/user).
        """
        pass

    @abstractmethod
    def adapt_test_command_for_a_single_test_via_ai(
        self,
        project_root_dir: str,
        test_file_relative_path: str,
        test_command: str,
    ) -> str:
        """
        Adapts a full test command (e.g. 'pytest') to run only one specific test file.

        Args:
            project_root_dir (str): The project root directory path.
            test_file_relative_path (str): The relative path to the test file to run.
            test_command (str): The original test command that runs all tests.

        Returns:
            str: A new command line string to run only the single test file.
        """
        pass
