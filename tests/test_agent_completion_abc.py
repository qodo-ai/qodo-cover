import pytest

from cover_agent.agent_completion_abc import AgentCompletionABC


# Dummy subclass that calls the parent's abstract method (executing "pass") then returns dummy values.
class DummyAgent(AgentCompletionABC):
    """
    A dummy implementation of AgentCompletionABC for testing purposes.
    """

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
        """
        Generate tests for the given source file.

        :param source_file_name: Name of the source file.
        :param max_tests: Maximum number of tests to generate.
        :param source_file_numbered: Numbered source file content.
        :param code_coverage_report: Code coverage report.
        :param language: Programming language of the source file.
        :param test_file: Content of the test file.
        :param test_file_name: Name of the test file.
        :param testing_framework: Testing framework to use.
        :param additional_instructions_text: Additional instructions text.
        :param additional_includes_section: Additional includes section.
        :param failed_tests_section: Failed tests section.
        :return: A tuple containing generated tests information.
        """
        # Call the abstract method to execute the "pass"
        super().generate_tests(
            source_file_name,
            max_tests,
            source_file_numbered,
            code_coverage_report,
            language,
            test_file,
            test_file_name,
            testing_framework,
            additional_instructions_text,
            additional_includes_section,
            failed_tests_section,
        )
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
        """
        Analyze the failure of a test.

        :param source_file_name: Name of the source file.
        :param source_file: Content of the source file.
        :param processed_test_file: Processed test file content.
        :param stdout: Standard output from the test run.
        :param stderr: Standard error from the test run.
        :param test_file_name: Name of the test file.
        :return: A tuple containing analyzed failure information.
        """
        super().analyze_test_failure(
            source_file_name,
            source_file,
            processed_test_file,
            stdout,
            stderr,
            test_file_name,
        )
        return ("analyzed_failure", 30, 40, "failure_prompt")

    def analyze_test_insert_line(
        self,
        language: str,
        test_file_numbered: str,
        test_file_name: str,
        additional_instructions_text: str = None,
    ) -> tuple:
        """
        Analyze the insertion line for a test.

        :param language: Programming language of the test file.
        :param test_file_numbered: Numbered test file content.
        :param test_file_name: Name of the test file.
        :param additional_instructions_text: Additional instructions text.
        :return: A tuple containing insert line analysis information.
        """
        super().analyze_test_insert_line(language, test_file_numbered, test_file_name, additional_instructions_text)
        return ("insert_line_instruction", 50, 60, "insert_prompt")

    def analyze_test_against_context(
        self,
        language: str,
        test_file_content: str,
        test_file_name_rel: str,
        context_files_names_rel: str,
    ) -> tuple:
        """
        Analyze the test against the given context.

        :param language: Programming language of the test file.
        :param test_file_content: Content of the test file.
        :param test_file_name_rel: Relative name of the test file.
        :param context_files_names_rel: Relative names of the context files.
        :return: A tuple containing context analysis information.
        """
        super().analyze_test_against_context(language, test_file_content, test_file_name_rel, context_files_names_rel)
        return ("context_analysis", 70, 80, "context_prompt")

    def analyze_suite_test_headers_indentation(
        self,
        language: str,
        test_file_name: str,
        test_file: str,
    ) -> tuple:
        """
        Analyze the headers indentation of a test suite.

        :param language: Programming language of the test file.
        :param test_file_name: Name of the test file.
        :param test_file: Content of the test file.
        :return: A tuple containing suite analysis information.
        """
        super().analyze_suite_test_headers_indentation(language, test_file_name, test_file)
        return ("suite_analysis", 90, 100, "suite_prompt")

    def adapt_test_command_for_a_single_test_via_ai(
        self,
        test_file_relative_path: str,
        test_command: str,
        project_root_dir: str,
    ) -> tuple:
        """
        Adapt the test command for a single test using AI.

        :param test_file_relative_path: Relative path of the test file.
        :param test_command: Original test command.
        :param project_root_dir: Root directory of the project.
        :return: A tuple containing adapted command information.
        """
        super().adapt_test_command_for_a_single_test_via_ai(test_file_relative_path, test_command, project_root_dir)
        return ("adapted_command", 110, 120, "adapt_prompt")


class TestAgentCompletionABC:
    """
    Test cases for the AgentCompletionABC class.
    """

    def check_output_format(self, result):
        """
        Check the format of the output result.

        :param result: The result to check.
        """
        assert isinstance(result, tuple), "Result is not a tuple"
        assert len(result) == 4, "Tuple does not have four elements"
        assert isinstance(result[0], str), "First element is not a string (AI-generated text)"
        assert isinstance(result[1], int), "Second element is not an integer (input token count)"
        assert isinstance(result[2], int), "Third element is not an integer (output token count)"
        assert isinstance(result[3], str), "Fourth element is not a string (final prompt)"

    def test_instantiation_of_abstract_class(self):
        """
        Test that instantiating the abstract class raises a TypeError.
        """
        with pytest.raises(TypeError):
            AgentCompletionABC()

    def test_generate_tests(self):
        """
        Test the generate_tests method of DummyAgent.
        """
        agent = DummyAgent()
        result = agent.generate_tests(
            "source.py",
            5,
            "numbered_source",
            "coverage",
            "python",
            "test_file_content",
            "test_file.py",
            "pytest",
        )
        self.check_output_format(result)

    def test_analyze_test_failure(self):
        """
        Test the analyze_test_failure method of DummyAgent.
        """
        agent = DummyAgent()
        result = agent.analyze_test_failure(
            "source.py",
            "source_code",
            "processed_test",
            "stdout",
            "stderr",
            "test_file.py",
        )
        self.check_output_format(result)

    def test_analyze_test_insert_line(self):
        """
        Test the analyze_test_insert_line method of DummyAgent.
        """
        agent = DummyAgent()
        result = agent.analyze_test_insert_line("python", "numbered_test_file", "test_file.py")
        self.check_output_format(result)

    def test_analyze_test_against_context(self):
        """
        Test the analyze_test_against_context method of DummyAgent.
        """
        agent = DummyAgent()
        result = agent.analyze_test_against_context(
            "python", "test_file_content", "test_file.py", "context1.py, context2.py"
        )
        self.check_output_format(result)

    def test_analyze_suite_test_headers_indentation(self):
        """
        Test the analyze_suite_test_headers_indentation method of DummyAgent.
        """
        agent = DummyAgent()
        result = agent.analyze_suite_test_headers_indentation("python", "test_file.py", "test_file_content")
        self.check_output_format(result)

    def test_adapt_test_command_for_a_single_test_via_ai(self):
        """
        Test the adapt_test_command_for_a_single_test_via_ai method of DummyAgent.
        """
        agent = DummyAgent()
        result = agent.adapt_test_command_for_a_single_test_via_ai(
            "relative/path/test_file.py", "pytest --maxfail=1", "/project/root"
        )
        self.check_output_format(result)
