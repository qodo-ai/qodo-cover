from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.PromptBuilder import PromptBuilder
from cover_agent.AICaller import AICaller
from typing import Tuple


class DefaultAgentCompletion(AgentCompletionABC):
    """Default implementation using PromptBuilder and AICaller."""

    def __init__(self, builder: PromptBuilder, caller: AICaller):
        self.builder = builder
        self.caller = caller

    def generate_tests(
        self,
        source_file_name: str,
        max_tests: int,
        source_file_numbered: str,
        code_coverage_report: str,
        additional_instructions_text: str,
        additional_includes_section: str,
        language: str,
        test_file: str,
        failed_tests_section: str,
        test_file_name: str,
        testing_framework: str,
    ) -> Tuple[str, int, int, str]:
        """
        Generates additional unit tests to improve test coverage.

        Args:
            source_file_name (str): Name of the source file under test.
            max_tests (int): Maximum number of tests to generate.
            source_file_numbered (str): The source code with line numbers added.
            code_coverage_report (str): Coverage details, highlighting untested lines.
            additional_instructions_text (str): Extra instructions for the AI.
            additional_includes_section (str): Additional includes/imports for context.
            language (str): Programming language (e.g. "python", "java").
            test_file (str): Content of the current test file.
            failed_tests_section (str): Data about failed tests (if any).
            test_file_name (str): Name of the test file.
            testing_framework (str): The testing framework in use (e.g., "pytest", "junit").

        Returns:
            Tuple[str, int, int, str]:
                - AI-generated test code as a string
                - The count of input tokens
                - The count of output tokens
                - The generated prompt (for reference)
        """
        prompt = self.builder.build_prompt(
            file="test_generation_prompt",
            source_file_name=source_file_name,
            max_tests=max_tests,
            source_file_numbered=source_file_numbered,
            code_coverage_report=code_coverage_report,
            additional_instructions_text=additional_instructions_text,
            additional_includes_section=additional_includes_section,
            language=language,
            test_file=test_file,
            failed_tests_section=failed_tests_section,
            test_file_name=test_file_name,
            testing_framework=testing_framework,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

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
        Analyzes the output of a failed test to determine the cause of failure.

        Args:
            source_file_name (str): Name of the source file under test.
            source_file (str): Raw source file content.
            processed_test_file (str): Preprocessed test file content.
            stdout (str): Standard output from the test run.
            stderr (str): Standard error from the test run.
            test_file_name (str): Name of the failing test file.

        Returns:
            Tuple[str, int, int, str]:
                - AI-generated analysis
                - The count of input tokens
                - The count of output tokens
                - The generated prompt
        """
        prompt = self.builder.build_prompt(
            file="analyze_test_run_failure",
            source_file_name=source_file_name,
            source_file=source_file,
            processed_test_file=processed_test_file,
            stdout=stdout,
            stderr=stderr,
            test_file_name=test_file_name,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_insert_line(
        self,
        language: str,
        test_file_numbered: str,
        additional_instructions_text: str,
        test_file_name: str,
    ) -> Tuple[str, int, int, str]:
        """
        Determines where to insert new test cases.

        Args:
            language (str): The programming language for the test file.
            test_file_numbered (str): The test file content with line numbers.
            additional_instructions_text (str): Any extra AI instructions.
            test_file_name (str): Name of the test file.

        Returns:
            Tuple[str, int, int, str]:
                - AI-generated suggestion for insertion
                - The count of input tokens
                - The count of output tokens
                - The generated prompt
        """
        prompt = self.builder.build_prompt(
            file="analyze_suite_test_insert_line",
            language=language,
            test_file_numbered=test_file_numbered,
            additional_instructions_text=additional_instructions_text,
            test_file_name=test_file_name,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_against_context(
        self,
        language: str,
        test_file_content: str,
        test_file_name_rel: str,
        context_files_names_rel: str,
    ) -> Tuple[str, int, int, str]:
        """
        Validates whether a generated test is appropriate for its corresponding source code.

        Args:
            language (str): Programming language for the test file.
            test_file_content (str): The actual content of the test file.
            test_file_name_rel (str): The relative path/name of the test file.
            context_files_names_rel (str): Names of context files to consider.

        Returns:
            Tuple[str, int, int, str]:
                - AI-generated validation or analysis
                - The count of input tokens
                - The count of output tokens
                - The generated prompt
        """
        prompt = self.builder.build_prompt(
            file="analyze_test_against_context",
            language=language,
            test_file_content=test_file_content,
            test_file_name_rel=test_file_name_rel,
            context_files_names_rel=context_files_names_rel,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_suite_test_headers_indentation(
        self,
        language: str,
        test_file_name: str,
        test_file: str,
    ) -> Tuple[str, int, int, str]:
        """
        Determines the indentation style used in test suite headers.

        Args:
            language (str): Programming language of the test file.
            test_file_name (str): The name of the test file.
            test_file (str): Raw content of the test file.

        Returns:
            Tuple[str, int, int, str]:
                - AI-generated indentation analysis
                - The count of input tokens
                - The count of output tokens
                - The generated prompt
        """
        prompt = self.builder.build_prompt(
            file="analyze_suite_test_headers_indentation",
            language=language,
            test_file_name=test_file_name,
            test_file=test_file,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt
    
    def adapt_test_command_for_a_single_test_via_ai(
        self,
        test_file_relative_path: str,
        test_command: str,
        project_root_dir: str,
    ) -> Tuple[str, int, int, str]:
        """
        Adapts the test command line to run only a single test file.

        This method modifies the provided test command so that it targets only one
        specific test file, preserving other flags or parameters where possible.

        Args:
            test_file_relative_path (str): The relative path to the specific test file to run.
            test_command (str): The original command line that runs all tests.
            project_root_dir (str): The project's root directory.

        Returns:
            Tuple[str, int, int, str]:
                - AI-generated command line (string) tailored to the specified test file
                - The count of input tokens (int)
                - The count of output tokens (int)
                - The generated prompt (string)
        """
        prompt = self.builder.build_prompt(
            file="adapt_test_command_for_a_single_test_via_ai",
            test_file_relative_path=test_file_relative_path,
            test_command=test_command,
            project_root_dir=project_root_dir,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt