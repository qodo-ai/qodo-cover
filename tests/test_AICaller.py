import os

import pytest
from unittest.mock import patch, Mock
from cover_agent.AICaller import AICaller


class TestAICaller:
    """
    Test suite for the AICaller class.
    """

    @pytest.fixture
    def ai_caller(self):
        """
        Fixture to create an instance of AICaller for testing.
        """
        return AICaller("test-model", "test-api", enable_retry=False)

    @patch("cover_agent.AICaller.AICaller.call_model")
    def test_call_model_simplified(self, mock_call_model):
        """
        Test the call_model method with a simplified scenario.
        """
        # Set up the mock to return a predefined response
        mock_call_model.return_value = ("Hello world!", 2, 10)
        prompt = {"system": "", "user": "Hello, world!"}

        ai_caller = AICaller("test-model", "test-api", enable_retry=False)
        # Explicitly provide the default value of max_tokens
        response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)

        # Assertions to check if the returned values are as expected
        assert response == "Hello world!"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check if call_model was called correctly
        mock_call_model.assert_called_once_with(prompt)

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_with_error(self, mock_completion, ai_caller):
        """
        Test the call_model method when an exception is raised.
        """
        # Set up mock to raise an exception
        mock_completion.side_effect = Exception("Test exception")
        prompt = {"system": "", "user": "Hello, world!"}
        # Call the method and handle the exception
        with pytest.raises(Exception) as exc_info:
            ai_caller.call_model(prompt)

        assert str(exc_info.value) == "Test exception"

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_error_streaming(self, mock_completion, ai_caller):
        """
        Test the call_model method when an exception is raised during streaming.
        """
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
        """
        Test the call_model method with W&B logging enabled.
        """
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
        """
        Test the call_model method with a different API base.
        """
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
        """
        Test the call_model method with a system key in the prompt.
        """
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
        """
        Test the call_model method when the prompt is missing required keys.
        """
        prompt = {"user": "Hello, world!"}
        with pytest.raises(KeyError) as exc_info:
            ai_caller.call_model(prompt)
        assert (
            str(exc_info.value)
            == "\"The prompt dictionary must contain 'system' and 'user' keys.\""
        )

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_user_message_only(self, mock_completion, ai_caller):
        """
        Test the call_model method with a model that only supports user messages.
        """
        # Set the model to one that only supports user messages
        ai_caller.model = "o1-preview"  # This is in USER_MESSAGE_ONLY_MODELS
        prompt = {"system": "System instruction", "user": "User query"}

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        # Call the method with stream=False for simplicity
        response, prompt_tokens, response_tokens = ai_caller.call_model(
            prompt, stream=False
        )

        # Verify the response
        assert response == "response"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check that litellm.completion was called with the correct arguments
        # Most importantly, verify that system and user messages were combined into a single user message
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["role"] == "user"
        assert call_args["messages"][0]["content"] == "System instruction\nUser query"

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_no_temperature_support(self, mock_completion, ai_caller):
        """
        Test the call_model method with a model that doesn't support temperature.
        """
        # Set the model to one that doesn't support temperature
        ai_caller.model = "o1-preview"  # This is in NO_SUPPORT_TEMPERATURE_MODELS
        prompt = {"system": "System message", "user": "Hello, world!"}

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        # Call the method
        response, prompt_tokens, response_tokens = ai_caller.call_model(
            prompt, stream=False
        )

        # Verify the response
        assert response == "response"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check that litellm.completion was called without the temperature parameter
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert "temperature" not in call_args

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_no_streaming_support(self, mock_completion, ai_caller):
        """
        Test the call_model method with a model that doesn't support streaming.
        """
        # Set the model to one that doesn't support streaming
        ai_caller.model = "o1"  # This is in NO_SUPPORT_STREAMING_MODELS
        prompt = {"system": "System message", "user": "Hello, world!"}

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        # Call the method explicitly requesting streaming, which should be ignored
        response, prompt_tokens, response_tokens = ai_caller.call_model(
            prompt, stream=True
        )

        # Verify the response
        assert response == "response"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check that litellm.completion was called with stream=False
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert call_args["stream"] == False
        # Check if max_tokens was removed and max_completion_tokens was added
        assert "max_tokens" not in call_args
        assert call_args["max_completion_tokens"] == 2 * ai_caller.max_tokens

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_streaming_response(self, mock_completion, ai_caller):
        """
        Test the call_model method with a streaming response.
        """
        # Make sure we're using a model that supports streaming
        ai_caller.model = "gpt-4"  # Not in NO_SUPPORT_STREAMING_MODELS
        prompt = {"system": "", "user": "Hello, world!"}
        # Mock the response to be an iterable of chunks
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="response part"))]
        mock_completion.return_value = [mock_chunk]
        with patch("cover_agent.AICaller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(
                prompt, stream=True
            )
            assert response == "response"
            assert prompt_tokens == 2

    @patch("cover_agent.AICaller.litellm.completion")
    def test_call_model_empty_system_prompt(self, mock_completion, ai_caller):
        """
        Test the call_model method with an empty system prompt.
        """
        # Should work the same for any model type
        prompt = {"system": "", "user": "Hello, world!"}

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response

        # Call the method
        response, prompt_tokens, response_tokens = ai_caller.call_model(
            prompt, stream=False
        )

        # Verify the response
        assert response == "response"
        assert prompt_tokens == 2
        assert response_tokens == 10

        # Check that litellm.completion was called with only a user message
        mock_completion.assert_called_once()
        call_args = mock_completion.call_args[1]
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["role"] == "user"
        assert call_args["messages"][0]["content"] == "Hello, world!"

    @patch("cover_agent.AICaller.litellm.completion")
    @patch.dict(os.environ, {"WANDB_API_KEY": "test_key"})
    @patch("cover_agent.AICaller.Trace.log")
    def test_call_model_wandb_logging_exception(
            self, mock_log, mock_completion, ai_caller
    ):
        """
        Test the call_model method with W&B logging and handle logging exceptions.
        """
        # Create a proper mock chunk with the correct structure
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="response"))]
        mock_completion.return_value = [mock_chunk]

        mock_log.side_effect = Exception("Logging error")
        prompt = {"system": "", "user": "Hello, world!"}

        with patch("cover_agent.AICaller.litellm.stream_chunk_builder") as mock_builder, \
                patch.object(ai_caller.logger, 'error') as mock_logger:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)

            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10
            mock_logger.assert_called_once_with("Error logging to W&B: Logging error")
