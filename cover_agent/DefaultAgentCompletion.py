from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.PromptBuilder import PromptBuilder
from cover_agent.AICaller import AICaller


class DefaultAgentCompletion(AgentCompletionABC):
    """Default implementation using PromptBuilder and AICaller."""

    def __init__(self, builder: PromptBuilder, caller: AICaller):
        self.builder = builder
        self.caller = caller

    def generate_tests(self, failed_tests, language, test_framework, coverage_report):
        """Generates additional unit tests to improve test coverage."""
        prompt = self.builder.build_prompt(
            file="test_generation_prompt",
            failed_tests_section=failed_tests,
            language=language,
            testing_framework=test_framework,
            code_coverage_report=coverage_report,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_failure(self, stderr, stdout, processed_test_file):
        """Analyzes the output of a failed test to determine the cause of failure."""
        prompt = self.builder.build_prompt(
            file="analyze_test_run_failure",
            stderr=stderr,
            stdout=stdout,
            processed_test_file=processed_test_file,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_insert_line(self, test_file):
        """Determines where to insert new test cases."""
        prompt = self.builder.build_prompt(
            file="analyze_suite_test_insert_line",
            test_file=test_file,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_against_context(self, test_code, context):
        """Validates whether a generated test is appropriate for its corresponding source code."""
        prompt = self.builder.build_prompt(
            file="analyze_test_against_context",
            test_code=test_code,
            context=context,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_suite_test_headers_indentation(self, test_file):
        """Determines the indentation style used in test suite headers."""
        prompt = self.builder.build_prompt(
            file="analyze_suite_test_headers_indentation",
            test_file=test_file,
        )
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt
