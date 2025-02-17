import os

import pytest
from unittest.mock import patch, Mock
from cover_agent import USER_MESSAGE_ONLY_MODELS
from cover_agent.AICaller import AICaller


class TestAICaller:
    @pytest.fixture
    def ai_caller(self):
        return AICaller("test-model", "test-api", enable_retry=False)

    @patch("cover_agent.AICaller.AICaller.call_model")
    def test_call_model_simplified(self, mock_call_model):
        # Set up the mock to return a predefined response
        mock_call_model.return_value = ("Hello world!", 2, 10)
        prompt = {"system": "", "user": "Hello, world!"}

        ai_caller = AICaller("test-model", "test-api", enable_retry=False)
        # Explicitly provide the default value of max_tokens
        response, prompt_tokens, response_tokens = ai_caller.call_model(
            prompt, max_tokens=4096
        )

        # Assertions to check if the returned values are as expected
        assert response == "Hello world!"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check if call_model was called correctly
        mock_call_model.assert_called_once_with(prompt, max_tokens=4096)

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_with_error(self, mock_completion, ai_caller):
        # Set up mock to raise an exception
        mock_completion.side_effect = Exception("Test exception")
        prompt = {"system": "", "user": "Hello, world!"}
        # Call the method and handle the exception
        with pytest.raises(Exception) as exc_info:
            ai_caller.call_model(prompt)

        assert str(exc_info.value) == "Test exception"

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_error_streaming(self, mock_completion, ai_caller):
        # Set up mock to raise an exception
        mock_completion.side_effect = ["results"]
        prompt = {"system": "", "user": "Hello, world!"}
        # Call the method and handle the exception
        with pytest.raises(Exception) as exc_info:
            ai_caller.call_model(prompt)

        # assert str(exc_info.value) == "list index out of range"
        assert (
            str(exc_info.value) == "'NoneType' object is not subscriptable"
        )  # this error message might change for different versions of litellm

    @patch("cover_agent.AICaller.litellm.completion")
    @patch.dict(os.environ, {"WANDB_API_KEY": "test_key"})
    @patch("cover_agent.AICaller.Trace.log")
    def test_call_model_wandb_logging(self, mock_log, mock_completion, ai_caller):
        mock_completion.return_value = [
            {"choices": [{"delta": {"content": "response"}}]}
        ]
        prompt = {"system": "", "user": "Hello, world!"}
        with patch("cover_agent.AICaller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)
            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10
            mock_log.assert_called_once()

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_api_base(self, mock_completion, ai_caller):
        mock_completion.return_value = [
            {"choices": [{"delta": {"content": "response"}}]}
        ]
        ai_caller.model = "openai/test-model"
        prompt = {"system": "", "user": "Hello, world!"}
        with patch("cover_agent.AICaller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)
            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_with_system_key(self, mock_completion, ai_caller):
        mock_completion.return_value = [
            {"choices": [{"delta": {"content": "response"}}]}
        ]
        prompt = {"system": "System message", "user": "Hello, world!"}
        with patch("cover_agent.AICaller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)
            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10

    def test_call_model_missing_keys(self, ai_caller):
        prompt = {"user": "Hello, world!"}
        with pytest.raises(KeyError) as exc_info:
            ai_caller.call_model(prompt)
        assert (
            str(exc_info.value)
            == "\"The prompt dictionary must contain 'system' and 'user' keys.\""
        )

    @pytest.mark.parametrize("model_name,expect_streaming,expect_temperature", [
        ("deepseek/deepseek-reasoner", False, False),
        ("o1-preview", True, False),
        ("gpt-4", True, True),
        ("o3-mini-2025-01-31", True, False)
    ])
    @patch("cover_agent.AICaller.litellm.completion")
    def test_model_specific_parameters(self, mock_completion, model_name, expect_streaming, 
                                     expect_temperature, ai_caller):
        """Test parameter handling for different model types"""
        ai_caller.model = model_name
        prompt = {"system": "System", "user": "User"}

        # Mock response structure for both streaming and non-streaming
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        ai_caller.call_model(prompt)
        # Verify completion parameters
        called_params = mock_completion.call_args[1]
        assert called_params.get("stream") == expect_streaming
        assert ("temperature" in called_params) == expect_temperature

        if model_name in ai_caller.no_support_streaming_models:
            assert "max_completion_tokens" in called_params
            assert "max_tokens" not in called_params
        else:
            assert "max_tokens" in called_params

    @pytest.mark.parametrize("model_name,system_prompt,expected_role_count", [
        ("deepseek/deepseek-reasoner", "System message", 1),
        ("o1-preview", "System message", 1),
        ("gpt-4", "System message", 2),
        ("anthropic/claude-3", "", 1)
    ])
    @patch("cover_agent.AICaller.litellm.completion")
    def test_message_structure_handling(self, mock_completion, model_name, system_prompt,
                                      expected_role_count, ai_caller):
        """Test message structure for different model requirements"""
        ai_caller.model = model_name
        prompt = {"system": system_prompt, "user": "User message"}

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        ai_caller.call_model(prompt)

        messages = mock_completion.call_args[1]["messages"]
        assert len(messages) == expected_role_count

        if model_name in ai_caller.user_message_only_models:
            assert messages[0]["role"] == "user"
            if system_prompt:
                assert system_prompt in messages[0]["content"]
            assert "User message" in messages[0]["content"]

    @patch("cover_agent.AICaller.litellm.completion")
    def test_api_base_inclusion(self, mock_completion, ai_caller):
        """Test API base is included for specific model types"""
        test_cases = [
            ("openai/custom-model", True),
            ("ollama/llama2", True),
            ("huggingface/codellama", True),
            ("gpt-4", False)
        ]

        for model_name, expect_api_base in test_cases:
            ai_caller.model = model_name
            ai_caller.api_base = "https://custom.endpoint"

            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="response"))]
            mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
            mock_completion.return_value = mock_response

            ai_caller.call_model({"system": "", "user": "test"})

            called_params = mock_completion.call_args[1]
            if expect_api_base:
                assert called_params["api_base"] == "https://custom.endpoint"
            else:
                assert "api_base" not in called_params

    @patch("cover_agent.AICaller.litellm.completion")
    def test_max_completion_tokens_handling(self, mock_completion, ai_caller):
        """Test models requiring max_completion_tokens instead of max_tokens"""
        ai_caller.model = "deepseek/deepseek-reasoner"
        prompt = {"system": "", "user": "test"}

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        ai_caller.call_model(prompt, max_tokens=4096)

        called_params = mock_completion.call_args[1]
        assert "max_completion_tokens" in called_params
        assert called_params["max_completion_tokens"] == 8192  # 2*max_tokens
        assert "max_tokens" not in called_params

    @patch("cover_agent.AICaller.litellm.completion")
    def test_non_streaming_response_handling(self, mock_completion, ai_caller):
        """Test proper handling of non-streaming responses"""
        ai_caller.model = "deepseek/deepseek-reasoner"
        prompt = {"system": "", "user": "test"}

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        response, _, _ = ai_caller.call_model(prompt)

        assert response == "response"
        mock_completion.assert_called_once()
        assert mock_completion.call_args[1]["stream"] is False

    def test_environment_variable_models(self, ai_caller):
        """Verify model lists are populated from init imports"""
        assert len(ai_caller.user_message_only_models) >= 4
        assert len(ai_caller.no_support_temperature_models) >= 7
        assert len(ai_caller.no_support_streaming_models) >= 3
        assert all(model in USER_MESSAGE_ONLY_MODELS
                 for model in ai_caller.user_message_only_models)
