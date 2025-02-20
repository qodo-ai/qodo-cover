from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.PromptBuilder import PromptBuilder
from cover_agent.AICaller import AICaller
from typing import Tuple

class DefaultAgentCompletion(AgentCompletionABC):
    """
    Default implementation of `AgentCompletionABC`, using `PromptBuilder` to construct prompts
    and `AICaller` to invoke LLM calls for test generation, analysis, and adaptation.
    """

    def __init__(self, builder: PromptBuilder, caller: AICaller):
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
        Generates a prompt and invokes an LLM call to create additional unit tests.
        
        This function constructs a prompt with the existing test cases, source file,
        and coverage report, then calls the LLM to generate new tests to improve test coverage.
        
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
        Generates a prompt and invokes an LLM call to analyze test failures.
        
        This function constructs a prompt containing the test execution output, error logs,
        and relevant files, then calls the LLM to determine the root cause of failures
        and suggest fixes.
        
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

    def adapt_test_command_for_a_single_test_via_ai(
        self,
        test_file_relative_path: str,
        test_command: str,
        project_root_dir: str,
    ) -> Tuple[str, int, int, str]:
        """
        Generates a prompt and invokes an LLM call to modify a test command to run a single test file.
        
        This function constructs a prompt that guides the LLM to adapt an
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
        prompt = self.builder.build_prompt(
            file="adapt_test_command_for_a_single_test_via_ai",
            test_file_relative_path=test_file_relative_path,
            test_command=test_command,
            project_root_dir=project_root_dir,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt
