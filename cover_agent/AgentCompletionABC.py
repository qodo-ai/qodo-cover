from abc import ABC, abstractmethod
from typing import Tuple


class AgentCompletionABC(ABC):
    """Abstract base class for AI-driven prompt handling."""

    @abstractmethod
    def generate_tests(
        self,
        failed_tests: str,
        language: str,
        test_framework: str,
        coverage_report: str,
    ) -> Tuple[str, int, int, str]:
        """
        Generates additional unit tests to improve test coverage.

        Returns:
            Tuple[str, int, int, str]: AI-generated test cases, input token count, output token count, and generated prompt.
        """
        pass

    @abstractmethod
    def analyze_test_failure(
        self, stderr: str, stdout: str, processed_test_file: str
    ) -> Tuple[str, int, int, str]:
        """
        Analyzes a test failure and returns insights.

        Returns:
            Tuple[str, int, int, str]: AI-generated analysis, input token count, output token count, and generated prompt.
        """
        pass

    @abstractmethod
    def analyze_test_insert_line(self, test_file: str) -> Tuple[str, int, int, str]:
        """
        Determines where to insert new test cases.

        Returns:
            Tuple[str, int, int, str]: Suggested insertion point, input token count, output token count, and generated prompt.
        """
        pass

    @abstractmethod
    def analyze_test_against_context(
        self, test_code: str, context: str
    ) -> Tuple[str, int, int, str]:
        """
        Validates whether a test is appropriate for its corresponding source code.

        Returns:
            Tuple[str, int, int, str]: AI validation result, input token count, output token count, and generated prompt.
        """
        pass

    @abstractmethod
    def analyze_suite_test_headers_indentation(
        self, test_file: str
    ) -> Tuple[str, int, int, str]:
        """
        Determines the indentation style used in test suite headers.

        Returns:
            Tuple[str, int, int, str]: Suggested indentation style, input token count, output token count, and generated prompt.
        """
        pass
