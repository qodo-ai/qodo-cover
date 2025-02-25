import pytest
from cover_agent.AgentCompletionABC import AgentCompletionABC

# Dummy subclass that calls the parent's abstract method (executing "pass") then returns dummy values.
class DummyAgent(AgentCompletionABC):
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
    ) -> tuple:
        # Call the abstract method to execute the "pass"
        super().generate_tests(source_file_name, max_tests, source_file_numbered, code_coverage_report, language, test_file, test_file_name, testing_framework, additional_instructions_text, additional_includes_section, failed_tests_section)
        return ("generated_tests", 10, 20, "final_prompt")

    def analyze_test_failure(
        self,
        source_file_name: str,
        source_file: str,
        processed_test_file: str,
        stdout: str,
        stderr: str,
        test_file_name: str,
    ) -> tuple:
        super().analyze_test_failure(source_file_name, source_file, processed_test_file, stdout, stderr, test_file_name)
        return ("analyzed_failure", 30, 40, "failure_prompt")

    def analyze_test_insert_line(
        self,
        language: str,
        test_file_numbered: str,
        test_file_name: str,
        additional_instructions_text: str = None,
    ) -> tuple:
        super().analyze_test_insert_line(language, test_file_numbered, test_file_name, additional_instructions_text)
        return ("insert_line_instruction", 50, 60, "insert_prompt")

    def analyze_test_against_context(
        self,
        language: str,
        test_file_content: str,
        test_file_name_rel: str,
        context_files_names_rel: str,
    ) -> tuple:
        super().analyze_test_against_context(language, test_file_content, test_file_name_rel, context_files_names_rel)
        return ("context_analysis", 70, 80, "context_prompt")

    def analyze_suite_test_headers_indentation(
        self,
        language: str,
        test_file_name: str,
        test_file: str,
    ) -> tuple:
        super().analyze_suite_test_headers_indentation(language, test_file_name, test_file)
        return ("suite_analysis", 90, 100, "suite_prompt")

    def adapt_test_command_for_a_single_test_via_ai(
        self,
        test_file_relative_path: str,
        test_command: str,
        project_root_dir: str,
    ) -> tuple:
        super().adapt_test_command_for_a_single_test_via_ai(test_file_relative_path, test_command, project_root_dir)
        return ("adapted_command", 110, 120, "adapt_prompt")


class TestAgentCompletionABC:
    def check_output_format(self, result):
        assert isinstance(result, tuple), "Result is not a tuple"
        assert len(result) == 4, "Tuple does not have four elements"
        assert isinstance(result[0], str), "First element is not a string (AI-generated text)"
        assert isinstance(result[1], int), "Second element is not an integer (input token count)"
        assert isinstance(result[2], int), "Third element is not an integer (output token count)"
        assert isinstance(result[3], str), "Fourth element is not a string (final prompt)"

    def test_instantiation_of_abstract_class(self):
        with pytest.raises(TypeError):
            AgentCompletionABC()

    def test_generate_tests(self):
        agent = DummyAgent()
        result = agent.generate_tests(
            "source.py", 5, "numbered_source", "coverage", "python",
            "test_file_content", "test_file.py", "pytest"
        )
        self.check_output_format(result)

    def test_analyze_test_failure(self):
        agent = DummyAgent()
        result = agent.analyze_test_failure(
            "source.py", "source_code", "processed_test", "stdout", "stderr", "test_file.py"
        )
        self.check_output_format(result)

    def test_analyze_test_insert_line(self):
        agent = DummyAgent()
        result = agent.analyze_test_insert_line("python", "numbered_test_file", "test_file.py")
        self.check_output_format(result)

    def test_analyze_test_against_context(self):
        agent = DummyAgent()
        result = agent.analyze_test_against_context("python", "test_file_content", "test_file.py", "context1.py, context2.py")
        self.check_output_format(result)

    def test_analyze_suite_test_headers_indentation(self):
        agent = DummyAgent()
        result = agent.analyze_suite_test_headers_indentation("python", "test_file.py", "test_file_content")
        self.check_output_format(result)

    def test_adapt_test_command_for_a_single_test_via_ai(self):
        agent = DummyAgent()
        result = agent.adapt_test_command_for_a_single_test_via_ai(
            "relative/path/test_file.py", "pytest --maxfail=1", "/project/root"
        )
        self.check_output_format(result)
