import logging
from typing import Tuple, Dict

from jinja2 import Environment, StrictUndefined

from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.AICaller import AICaller
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import load_yaml


class DefaultAgentCompletion(AgentCompletionABC):
    """
    Default implementation that uses AICaller and internal prompt-building logic
    to match the TOML templates exactly.
    """

    def __init__(self, caller: AICaller):
        self.caller = caller

    def _build_prompt(self, template_name: str, variables: dict) -> dict:
        environment = Environment(undefined=StrictUndefined)
        try:
            prompt_config = get_settings().get(template_name)
            if (
                not prompt_config
                or not hasattr(prompt_config, "system")
                or not hasattr(prompt_config, "user")
            ):
                logging.error(f"No valid prompt config found for '{template_name}'.")
                return {"system": "", "user": ""}

            system_prompt = environment.from_string(prompt_config.system).render(variables)
            user_prompt = environment.from_string(prompt_config.user).render(variables)
            return {"system": system_prompt, "user": user_prompt}

        except Exception as e:
            logging.error(f"Error rendering prompt for '{template_name}': {e}")
            return {"system": "", "user": ""}

    # ------------------------------------------------------------------------
    # Implement abstract methods, passing EXACT placeholders used by the TOMLs.
    # ------------------------------------------------------------------------

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
    ) -> Tuple[str, int, int, dict]:
        """
        Matches test_generation_prompt.toml placeholders exactly.
        """
        variables = {
            "language": language,
            "source_file_name": source_file_name,
            "source_file_numbered": source_file_numbered,
            "test_file_name": test_file_name,
            "test_file": test_file,
            "testing_framework": testing_framework,
            "code_coverage_report": code_coverage_report,
            "additional_includes_section": additional_includes_section,
            "failed_tests_section": failed_tests_section,
            "additional_instructions_text": additional_instructions_text,
            "max_tests": max_tests,
        }

        prompt = self._build_prompt("test_generation_prompt", variables)
        ai_response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return ai_response, prompt_tokens, completion_tokens, prompt

    def analyze_test_run_failure(
        self,
        test_file_name: str,
        processed_test_file: str,
        source_file_name: str,
        source_file: str,
        stdout: str,
        stderr: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Matches analyze_test_run_failure.toml placeholders:
            {{ test_file_name }}, {{ processed_test_file }},
            {{ source_file_name }}, {{ source_file }}, {{ stdout }}, {{ stderr }}
        """
        variables = {
            "test_file_name": test_file_name,
            "processed_test_file": processed_test_file,
            "source_file_name": source_file_name,
            "source_file": source_file,
            "stdout": stdout,
            "stderr": stderr,
        }

        prompt = self._build_prompt("analyze_test_run_failure", variables)
        ai_response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return ai_response, prompt_tokens, completion_tokens, prompt

    def analyze_suite_test_insert_line(
        self,
        language: str,
        test_file_name: str,
        test_file_numbered: str,
        additional_instructions_text: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Matches analyze_suite_test_insert_line.toml placeholders:
            {{ language }}, {{ test_file_name }},
            {{ test_file_numbered }}, {{ additional_instructions_text }}
        """
        variables = {
            "language": language,
            "test_file_name": test_file_name,
            "test_file_numbered": test_file_numbered,
            "additional_instructions_text": additional_instructions_text,
        }

        prompt = self._build_prompt("analyze_suite_test_insert_line", variables)
        ai_response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return ai_response, prompt_tokens, completion_tokens, prompt

    def analyze_test_against_context(
        self,
        language: str,
        test_file_name_rel: str,
        test_file_content: str,
        context_files_names_rel: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Matches analyze_test_against_context.toml placeholders:
            {{ language }}, {{ test_file_name_rel }},
            {{ test_file_content }}, {{ context_files_names_rel }}
        """
        variables = {
            "language": language,
            "test_file_name_rel": test_file_name_rel,
            "test_file_content": test_file_content,
            "context_files_names_rel": context_files_names_rel,
        }

        prompt = self._build_prompt("analyze_test_against_context", variables)
        ai_response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return ai_response, prompt_tokens, completion_tokens, prompt

    def analyze_suite_test_headers_indentation(
        self,
        language: str,
        test_file_name: str,
        test_file: str,
    ) -> Tuple[str, int, int, dict]:
        """
        Matches analyze_suite_test_headers_indentation.toml placeholders:
            {{ language }}, {{ test_file_name }}, {{ test_file }}
        """
        variables = {
            "language": language,
            "test_file_name": test_file_name,
            "test_file": test_file,
        }

        prompt = self._build_prompt("analyze_suite_test_headers_indentation", variables)
        ai_response, prompt_tokens, completion_tokens = self.caller.call_model(prompt)
        return ai_response, prompt_tokens, completion_tokens, prompt

    def adapt_test_command_for_a_single_test_via_ai(
        self,
        project_root_dir: str,
        test_file_relative_path: str,
        test_command: str,
    ) -> str:
        """
        Matches adapt_test_command_for_a_single_test_via_ai.toml placeholders:
            {{ project_root_dir }}, {{ test_file_relative_path }}, {{ test_command }}
        """
        variables = {
            "project_root_dir": project_root_dir,
            "test_file_relative_path": test_file_relative_path,
            "test_command": test_command,
        }

        prompt = self._build_prompt("adapt_test_command_for_a_single_test_via_ai", variables)
        # use a non-streaming call for simpler YAML parsing
        ai_response, _, _ = self.caller.call_model(prompt, stream=False)

        try:
            data = load_yaml(ai_response)
            return data["new_command_line"].strip()
        except Exception as e:
            logging.error(f"Error parsing AI response for single test command: {e}")
            return test_command
