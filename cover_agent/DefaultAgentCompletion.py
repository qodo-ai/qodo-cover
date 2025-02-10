import logging
from typing import Tuple

from jinja2 import Environment, StrictUndefined

from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.AICaller import AICaller
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import load_yaml


class DefaultAgentCompletion(AgentCompletionABC):
    """
    Default implementation of AgentCompletionABC that uses AICaller and internal prompt-building.
    """

    def __init__(self, caller: AICaller):
        """
        Args:
            caller (AICaller): The AI caller to use for sending prompts to the language model.
        """
        self.caller = caller

    def _build_prompt(self, template_name: str, variables: dict) -> dict:
        """
        Private helper: Renders a system/user prompt from a .toml config and a set of variables.

        Args:
            template_name (str): The key used to look up the prompt's system/user text in get_settings().
            variables (dict): A dictionary of Jinja2 template variables.

        Returns:
            dict: {"system": str, "user": str} representing the final rendered prompt.
        """
        environment = Environment(undefined=StrictUndefined)
        try:
            # Retrieve the toml-defined prompt config
            prompt_config = get_settings().get(template_name)
            if (
                not prompt_config
                or not hasattr(prompt_config, "system")
                or not hasattr(prompt_config, "user")
            ):
                logging.error(
                    f"Could not find valid prompt config for '{template_name}' in settings."
                )
                return {"system": "", "user": ""}

            system_prompt = environment.from_string(prompt_config.system).render(variables)
            user_prompt = environment.from_string(prompt_config.user).render(variables)

            return {"system": system_prompt, "user": user_prompt}
        except Exception as e:
            logging.error(f"Error rendering Jinja2 prompt for '{template_name}': {e}")
            return {"system": "", "user": ""}

    # -----------------------------
    #    Implement Abstract Methods
    # -----------------------------

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
        """
        variables = {
            "source_file_numbered": source_file_numbered,
            "test_file": test_file,
            "code_coverage_report": code_coverage_report,
            "testing_framework": testing_framework,
            "additional_instructions_text": additional_instructions_text,
            # If needed, add defaults or placeholders:
            "language": "python",  # or pass in from caller if not always python
            "max_tests": 4,
            "failed_tests_section": "",  # If you no longer use this, you can remove entirely
            "additional_includes_section": "",
        }

        prompt = self._build_prompt("test_generation_prompt", variables)
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)

        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_failure(
        self,
        source_file: str,
        processed_test_file: str,
        stdout: str,
        stderr: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Analyzes a test failure, returning a short summary & recommended fixes.
        """
        variables = {
            "source_file": source_file,
            "processed_test_file": processed_test_file,
            "stdout": stdout,
            "stderr": stderr,
            # If needed:
            "test_file_name": "",
            "source_file_name": "",
        }

        prompt = self._build_prompt("analyze_test_run_failure", variables)
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_insert_line(
        self,
        test_file_numbered: str,
        language: str,
        testing_framework: str,
        additional_instructions_text: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Determines where new test code should be inserted in the existing test suite.
        """
        variables = {
            "test_file_numbered": test_file_numbered,
            "language": language,
            "testing_framework": testing_framework,
            "additional_instructions_text": additional_instructions_text,
        }

        prompt = self._build_prompt("analyze_suite_test_insert_line", variables)
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_test_against_context(
        self,
        test_file_content: str,
        context_files_names_rel: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Determines if this is a unit test and which context file it targets.
        """
        variables = {
            "test_file_content": test_file_content,
            "context_files_names_rel": context_files_names_rel,
            # Possibly also pass:
            "language": "python",
            "test_file_name_rel": "",
        }

        prompt = self._build_prompt("analyze_test_against_context", variables)
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def analyze_suite_test_headers_indentation(
        self,
        test_file: str,
        language: str,
        testing_framework: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Determines indentation style and test metadata from the suite headers.
        """
        variables = {
            "test_file": test_file,
            "language": language,
            "testing_framework": testing_framework,
        }

        prompt = self._build_prompt("analyze_suite_test_headers_indentation", variables)
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return response, prompt_tokens, completion_tokens, prompt

    def adapt_test_command_for_a_single_test_via_ai(
        self,
        project_root_dir: str,
        test_file_relative_path: str,
        test_command: str,
    ) -> str:
        """
        Adapts a test command to run only a single test file, using the AI model.
        """
        variables = {
            "project_root_dir": project_root_dir,
            "test_file_relative_path": test_file_relative_path,
            "test_command": test_command,
        }

        # The "adapt_test_command_for_a_single_test_via_ai" key in your .toml:
        prompt = self._build_prompt("adapt_test_command_for_a_single_test_via_ai", variables)

        # Non-streaming call for simpler YAML parsing
        response, prompt_tokens, completion_tokens = self.caller.call_model(prompt, stream=False)

        try:
            data = load_yaml(response)
            return data["new_command_line"].strip()
        except Exception as e:
            logging.error(f"Error parsing AI response for single test command: {e}")
            return test_command  # fallback to original if something goes wrong
