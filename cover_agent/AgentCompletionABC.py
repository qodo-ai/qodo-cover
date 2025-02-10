from abc import ABC, abstractmethod
from typing import Tuple, Dict


class AgentCompletionABC(ABC):
    """
    Abstract base class for AI-driven prompt handling.

    Each method that interacts with the AI returns:
        (AI-generated string, input token count, output token count, dict-of-rendered-prompt)
    except for 'adapt_test_command_for_a_single_test_via_ai()', which returns a single string.
    """

    @abstractmethod
    def generate_tests(
        self,
        language: str,
        source_file_name: str,
        source_file_numbered: str,
        test_file_name: str,
        test_file: str,
        testing_framework: str,
        code_coverage_report: str,
        additional_includes_section: str,
        failed_tests_section: str,
        additional_instructions_text: str,
        max_tests: int,
    ) -> Tuple[str, int, int, Dict]:
        """
        Builds a prompt using 'test_generation_prompt.toml' to generate comprehensive unit tests.
        Matches placeholders:
            {{ language }}, {{ source_file_name }}, {{ source_file_numbered }},
            {{ test_file_name }}, {{ test_file }}, {{ testing_framework }},
            {{ code_coverage_report }}, {{ additional_includes_section }},
            {{ failed_tests_section }}, {{ additional_instructions_text }},
            {{ max_tests }}
        """
        pass

    @abstractmethod
    def analyze_test_run_failure(
        self,
        test_file_name: str,
        processed_test_file: str,
        source_file_name: str,
        source_file: str,
        stdout: str,
        stderr: str,
    ) -> Tuple[str, int, int, Dict]:
        """
        Builds a prompt using 'analyze_test_run_failure.toml' to get analysis of a failing test run.
        Matches placeholders:
            {{ test_file_name }}, {{ processed_test_file }}, {{ source_file_name }},
            {{ source_file }}, {{ stdout }}, {{ stderr }}
        """
        pass

    @abstractmethod
    def analyze_suite_test_insert_line(
        self,
        language: str,
        test_file_name: str,
        test_file_numbered: str,
        additional_instructions_text: str,
    ) -> Tuple[str, int, int, Dict]:
        """
        Builds a prompt using 'analyze_suite_test_insert_line.toml' to determine
        where new test code should be inserted.
        Matches placeholders:
            {{ language }}, {{ test_file_name }},
            {{ test_file_numbered }}, {{ additional_instructions_text }}
        """
        pass

    @abstractmethod
    def analyze_test_against_context(
        self,
        language: str,
        test_file_name_rel: str,
        test_file_content: str,
        context_files_names_rel: str,
    ) -> Tuple[str, int, int, Dict]:
        """
        Builds a prompt using 'analyze_test_against_context.toml' to figure out if a test is a unit test
        and which context file it's primarily testing.
        Matches placeholders:
            {{ language }}, {{ test_file_name_rel }},
            {{ test_file_content }}, {{ context_files_names_rel }}
        """
        pass

    @abstractmethod
    def analyze_suite_test_headers_indentation(
        self,
        language: str,
        test_file_name: str,
        test_file: str,
    ) -> Tuple[str, int, int, Dict]:
        """
        Builds a prompt using 'analyze_suite_test_headers_indentation.toml'
        to determine test indentation, language, testing framework, etc.
        Matches placeholders:
            {{ language }}, {{ test_file_name }}, {{ test_file }}
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
        Builds a prompt using 'adapt_test_command_for_a_single_test_via_ai.toml'
        to adapt a test command to only run a single file.
        Matches placeholders:
            {{ project_root_dir }}, {{ test_file_relative_path }}, {{ test_command }}
        """
        pass
