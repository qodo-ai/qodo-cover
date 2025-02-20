from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.PromptBuilder import PromptBuilder
from cover_agent.AICaller import AICaller
from typing import Tuple


class DefaultAgentCompletion(AgentCompletionABC):
    """
    A default implementation of AgentCompletionABC that relies on TOML-based
    prompt templates for each method. It uses a PromptBuilder to construct the
    prompt from the appropriate TOML file, then calls an AI model via AICaller
    to get the response.
    """

    def __init__(self, builder: PromptBuilder, caller: AICaller):
        """
        Initializes the DefaultAgentCompletion.

        Args:
            builder (PromptBuilder): A utility class for building prompts from TOML templates.
            caller (AICaller): A class responsible for sending the prompt to an AI model and returning the response.
        """
        self.builder = builder
        self.caller = caller

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
        Generates additional unit tests using the 'test_generation_prompt.toml' template.

        The prompt typically requests the AI to produce YAML conforming to a
        Pydantic schema named `$NewTests`. These new tests aim to address coverage gaps,
        handle edge cases, or fulfill any special instructions.

        Args:
            source_file_name (str): The name/path of the source file under test.
            max_tests (int): Maximum number of tests to generate in a single run.
            source_file_numbered (str): The source code, annotated with line numbers.
            code_coverage_report (str): Coverage data highlighting untested lines or blocks.
            language (str): Programming language of the source code and tests (e.g., "python").
            test_file (str): The existing test file content.
            test_file_name (str): Name/path of the existing test file.
            testing_framework (str): The testing framework in use (e.g., "pytest", "unittest").
            additional_instructions_text (str, optional): Extra instructions or context for the AI.
            additional_includes_section (str, optional): Additional code/files for the AI to consider.
            failed_tests_section (str, optional): Details regarding previously failed tests, if any.

        Returns:
            Tuple[str, int, int, str]: A 4-element tuple containing:
                - The AI-generated test code or YAML (str),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt sent to the AI (str).
        """
        prompt = self.builder.build_prompt(
            file="test_generation_prompt",
            source_file_name=source_file_name,
            max_tests=max_tests,
            source_file_numbered=source_file_numbered,
            code_coverage_report=code_coverage_report,
            language=language,
            test_file=test_file,
            test_file_name=test_file_name,
            testing_framework=testing_framework,
            additional_instructions_text=additional_instructions_text,
            additional_includes_section=additional_includes_section,
            failed_tests_section=failed_tests_section,
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
        Analyzes a test run failure using the 'analyze_test_run_failure.toml' template.

        The prompt includes:
            - The source file content,
            - The failing test file content (possibly preprocessed),
            - The captured stdout and stderr logs,
            - The name of the failing test file.

        The AI typically returns a concise analysis of why the test failed, plus
        potential solutions or next steps.

        Args:
            source_file_name (str): Name/path of the source file under test.
            source_file (str): The raw content of the source file.
            processed_test_file (str): The content of the failing test file.
            stdout (str): Captured standard output from the test run.
            stderr (str): Captured standard error from the test run.
            test_file_name (str): The name/path of the failing test file.

        Returns:
            Tuple[str, int, int, str]: A 4-element tuple containing:
                - The AI-generated analysis (str),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (str).
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
        test_file_name: str,
        additional_instructions_text: str = None,
    ) -> Tuple[str, int, int, str]:
        """
        Determines the correct line number(s) to insert new test cases, using
        'analyze_suite_test_insert_line.toml'.

        The prompt typically requests the AI to return a YAML object conforming to
        `$TestsAnalysis`, which indicates the line number after which new tests
        should be inserted, as well as where imports (if any) should go.

        Args:
            language (str): The programming language of the test file.
            test_file_numbered (str): The test file content with line numbers included.
            test_file_name (str): The name/path of the test file.
            additional_instructions_text (str, optional): Additional context or instructions.

        Returns:
            Tuple[str, int, int, str]: A 4-element tuple containing:
                - The AI-generated insertion info (str, often YAML),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (str).
        """
        prompt = self.builder.build_prompt(
            file="analyze_suite_test_insert_line",
            language=language,
            test_file_numbered=test_file_numbered,
            test_file_name=test_file_name,
            additional_instructions_text=additional_instructions_text,
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
        Examines a test file against context files using 'analyze_test_against_context.toml'.

        The prompt includes:
            - The test file content,
            - A list of context files (by name),
            - The relevant programming language.

        The AI typically returns a YAML object matching `$TestAgainstContextAnalysis`,
        indicating whether it's a unit test (`is_this_a_unit_test`) and which file
        is most likely the main one being tested (`main_file`).

        Args:
            language (str): The programming language of the test file.
            test_file_content (str): The raw content of the test file.
            test_file_name_rel (str): The relative path/name of the test file.
            context_files_names_rel (str): Names of context files to check against.

        Returns:
            Tuple[str, int, int, str]: A 4-element tuple containing:
                - The AI-generated analysis (str, typically YAML),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (str).
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
        Inspects a test suite's header indentation using 'analyze_suite_test_headers_indentation.toml'.

        This prompt typically tells the AI to return a YAML object conforming to
        `$TestsAnalysis`, indicating the indentation level, number of existing tests,
        and (sometimes) the test framework in use.

        Args:
            language (str): The programming language of the test file.
            test_file_name (str): The name/path of the test file.
            test_file (str): The raw content of the test file.

        Returns:
            Tuple[str, int, int, str]: A 4-element tuple containing:
                - The AI-generated indentation/style analysis (str),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (str).
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
        Adapts a project-wide test command to run a single test file, using
        'adapt_test_command_for_a_single_test_via_ai.toml'.

        The AI typically responds with a YAML object matching
        `$CommandLineToRunASingleTest`, providing the modified command.

        Args:
            test_file_relative_path (str): Relative path to the test file to be run in isolation.
            test_command (str): The command that currently runs all tests.
            project_root_dir (str): The root directory of the project.

        Returns:
            Tuple[str, int, int, str]: A 4-element tuple containing:
                - The AI-generated single-test command (str, often YAML),
                - The input token count (int),
                - The output token count (int),
                - The final constructed prompt (str).
        """
        prompt = self.builder.build_prompt(
            file="adapt_test_command_for_a_single_test_via_ai",
            test_file_relative_path=test_file_relative_path,
            test_command=test_command,
            project_root_dir=project_root_dir,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt
