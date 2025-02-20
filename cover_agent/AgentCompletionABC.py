from abc import ABC, abstractmethod
from typing import Tuple

class AgentCompletionABC(ABC):
    """
    Abstract base class for AI-driven prompt handling.
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
        Generates additional unit tests to improve test coverage.

        This method integrates logic for building a prompt that includes the
        source code, existing test suite, coverage data, and optional extra instructions.
        The AI will propose new tests that aim to address any untested lines or scenarios.

        Returns:
            Tuple[str, int, int, str]: 
                - AI-generated test cases (string)
                - input token count (int)
                - output token count (int)
                - the generated prompt (string)
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
        Analyzes a test failure and returns insights.

        This method processes logs and source/test files to identify why a test
        might have failed, and suggests potential fixes or next steps.

        Returns:
            Tuple[str, int, int, str]: 
                - AI-generated analysis (string)
                - input token count (int)
                - output token count (int)
                - the generated prompt (string)
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
        Determines where to insert new test cases.

        This method examines an existing test file (with line numbers) to find
        the most appropriate place to add new tests.

        Returns:
            Tuple[str, int, int, str]: 
                - insertion advice or line number info (string)
                - input token count (int)
                - output token count (int)
                - the generated prompt (string)
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
        Validates whether a test is appropriate for its corresponding source code.

        Given a test file’s content and a set of context files, this method determines
        if the file is indeed a unit test and identifies the primary source file it targets.

        Returns:
            Tuple[str, int, int, str]: 
                - AI validation result (string)
                - input token count (int)
                - output token count (int)
                - the generated prompt (string)
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
        Determines the indentation style used in test suite headers.

        This method inspects an existing test suite to identify indentation
        conventions, so newly generated tests can conform to the same style.

        Returns:
            Tuple[str, int, int, str]: 
                - indentation style feedback (string)
                - input token count (int)
                - output token count (int)
                - the generated prompt (string)
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
        Adapts the test command line to run only a single test file.

        This method takes the original command line that runs all tests and rewrites
        it so that it targets only the specified test file, retaining other flags 
        or arguments as much as possible.

        Returns:
            Tuple[str, int, int, str]:
                - modified single-test command line (string)
                - input token count (int)
                - output token count (int)
                - the generated prompt (string)
        """
        pass