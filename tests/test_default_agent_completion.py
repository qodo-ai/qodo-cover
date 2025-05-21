from unittest.mock import MagicMock, patch

import pytest

from cover_agent.default_agent_completion import DefaultAgentCompletion


class TestDefaultAgentCompletion:
    """
    Test suite for the DefaultAgentCompletion class.
    """

    def test_generate_tests(self):
        """
        Test the generate_tests method to ensure it correctly constructs the prompt,
        calls the AI model, and returns the expected response and tokens.
        """
        mock_caller = MagicMock()
        mock_caller.call_model.return_value = ("test response", 100, 50)
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch.object(agent, "_build_prompt") as mock_build_prompt:
            mock_build_prompt.return_value = {
                "system": "sys prompt",
                "user": "user prompt",
            }

            result = agent.generate_tests(
                source_file_name="test.py",
                max_tests=5,
                source_file_numbered="1: code",
                code_coverage_report="report",
                language="python",
                test_file="test content",
                test_file_name="test_file.py",
                testing_framework="pytest",
            )

            assert result == ("test response", 100, 50, "user prompt")
            mock_build_prompt.assert_called_once()
            mock_caller.call_model.assert_called_once()

    def test_adapt_test_command_success(self):
        """
        Test the adapt_test_command_for_a_single_test_via_ai method to ensure it correctly
        adapts the test command and returns the expected new command line and tokens.
        """
        mock_caller = MagicMock()
        mock_caller.call_model.return_value = (
            '{"new_command_line": "pytest test_file.py"}',
            100,
            50,
        )
        agent = DefaultAgentCompletion(caller=mock_caller)

        result = agent.adapt_test_command_for_a_single_test_via_ai(
            test_file_relative_path="test_file.py",
            test_command="pytest",
            project_root_dir="/path",
        )

        assert result[0] == "pytest test_file.py"
        assert result[1] == 100
        assert result[2] == 50
        assert isinstance(result[3], str)

    def test_build_prompt_rendering_error(self):
        """
        Test the _build_prompt method to ensure it raises a RuntimeError when there is
        an error rendering the prompt templates.
        """
        mock_caller = MagicMock()
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch("cover_agent.default_agent_completion.get_settings") as mock_settings:
            settings = MagicMock()
            settings.system = "{{ invalid_var }}"
            settings.user = "test"
            mock_settings.return_value.get.return_value = settings

            with pytest.raises(RuntimeError) as exc_info:
                agent._build_prompt("test_file")

            assert "Error rendering prompt" in str(exc_info.value)

    def test_build_prompt_invalid_settings(self):
        """
        Test the _build_prompt method to ensure it raises a ValueError when the TOML
        config does not contain valid 'system' and 'user' keys.
        """
        mock_caller = MagicMock()
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch("cover_agent.default_agent_completion.get_settings") as mock_get_settings:
            mock_get_settings.return_value = {"test_file": None}

            with pytest.raises(ValueError) as exc_info:
                agent._build_prompt("test_file")

            assert "Could not find valid system/user prompt settings" in str(exc_info.value)

    def test_build_prompt_valid_settings(self):
        """
        Test the _build_prompt method to ensure it correctly renders the system and user
        prompts when provided with valid settings and variables.
        """
        mock_caller = MagicMock()
        agent = DefaultAgentCompletion(caller=mock_caller)

        mock_settings = MagicMock()
        mock_settings.system = "Hello {{ name }}"
        mock_settings.user = "Test {{ value }}"

        with patch("cover_agent.default_agent_completion.get_settings") as mock_get_settings:
            mock_get_settings.return_value = {"test_file": mock_settings}

            result = agent._build_prompt("test_file", name="World", value=42)

            assert result == {"system": "Hello World", "user": "Test 42"}

    def test_adapt_test_command_yaml_parsing_error(self):
        """
        Test the adapt_test_command_for_a_single_test_via_ai method to ensure it returns
        None for the command when YAML parsing fails.
        """
        mock_caller = MagicMock()
        # Return invalid YAML to trigger parsing error
        mock_caller.call_model.return_value = ("invalid yaml content", 100, 50)
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch("cover_agent.default_agent_completion.load_yaml") as mock_load_yaml:
            mock_load_yaml.side_effect = Exception("YAML parsing error")

            result = agent.adapt_test_command_for_a_single_test_via_ai(
                test_file_relative_path="test_file.py",
                test_command="pytest",
                project_root_dir="/path",
            )

            # Verify that the method returns None for the command when YAML parsing fails
            assert result[0] is None
            assert result[1] == 100
            assert result[2] == 50
            assert isinstance(result[3], str)

    def test_analyze_suite_test_headers_indentation(self):
        """
        Test the analyze_suite_test_headers_indentation method to ensure it correctly
        constructs the prompt, calls the AI model, and returns the expected response and tokens.
        """
        mock_caller = MagicMock()
        mock_caller.call_model.return_value = ("indentation analysis", 100, 50)
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch.object(agent, "_build_prompt") as mock_build_prompt:
            mock_build_prompt.return_value = {
                "system": "sys prompt",
                "user": "user prompt",
            }

            result = agent.analyze_suite_test_headers_indentation(
                language="python",
                test_file_name="test_file.py",
                test_file="test content",
            )

            assert result == ("indentation analysis", 100, 50, "user prompt")
            mock_build_prompt.assert_called_once()
            mock_caller.call_model.assert_called_once()

    def test_analyze_test_against_context(self):
        """
        Test the analyze_test_against_context method to ensure it correctly constructs
        the prompt, calls the AI model, and returns the expected response and tokens.
        """
        mock_caller = MagicMock()
        mock_caller.call_model.return_value = ("context analysis response", 100, 50)
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch.object(agent, "_build_prompt") as mock_build_prompt:
            mock_build_prompt.return_value = {
                "system": "sys prompt",
                "user": "user prompt",
            }

            result = agent.analyze_test_against_context(
                language="python",
                test_file_content="test content",
                test_file_name_rel="tests/test_file.py",
                context_files_names_rel="src/file.py",
            )

            assert result == ("context analysis response", 100, 50, "user prompt")
            mock_build_prompt.assert_called_once()
            mock_caller.call_model.assert_called_once()

    def test_analyze_test_insert_line(self):
        """
        Test the analyze_test_insert_line method to ensure it correctly constructs the
        prompt, calls the AI model, and returns the expected response and tokens.
        """
        mock_caller = MagicMock()
        mock_caller.call_model.return_value = ("insert line response", 100, 50)
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch.object(agent, "_build_prompt") as mock_build_prompt:
            mock_build_prompt.return_value = {
                "system": "sys prompt",
                "user": "user prompt",
            }

            result = agent.analyze_test_insert_line(
                language="python",
                test_file_numbered="1: test content",
                test_file_name="test_file.py",
                additional_instructions_text="extra instructions",
            )

            assert result == ("insert line response", 100, 50, "user prompt")
            mock_build_prompt.assert_called_once()
            mock_caller.call_model.assert_called_once()

    def test_analyze_test_failure(self):
        """
        Test the analyze_test_failure method to ensure it correctly constructs the prompt,
        calls the AI model, and returns the expected response and tokens.
        """
        mock_caller = MagicMock()
        mock_caller.call_model.return_value = ("analysis response", 100, 50)
        agent = DefaultAgentCompletion(caller=mock_caller)

        with patch.object(agent, "_build_prompt") as mock_build_prompt:
            mock_build_prompt.return_value = {
                "system": "sys prompt",
                "user": "user prompt",
            }

            result = agent.analyze_test_failure(
                source_file_name="test.py",
                source_file="source content",
                processed_test_file="test content",
                stdout="test output",
                stderr="test error",
                test_file_name="test_file.py",
            )

            assert result == ("analysis response", 100, 50, "user prompt")
            mock_build_prompt.assert_called_once()
            mock_caller.call_model.assert_called_once()
