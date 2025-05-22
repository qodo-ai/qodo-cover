import os

from unittest.mock import Mock, patch

import pytest

from cover_agent.ai_caller import AICaller


class TestAICaller:
    """
    Test suite for the AICaller class.
    """

    @pytest.fixture
    def ai_caller(self):
        """
        Fixture to create an instance of AICaller for testing.
        """
        return AICaller(model="test-model", api_base="test-api", enable_retry=False)

    @patch("cover_agent.ai_caller.AICaller.call_model")
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

    @patch("cover_agent.ai_caller.litellm.completion")
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

    @patch("cover_agent.ai_caller.litellm.completion")
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

    @patch("cover_agent.ai_caller.litellm.completion")
    @patch.dict(os.environ, {"WANDB_API_KEY": "test_key"})
    @patch("cover_agent.ai_caller.Trace.log")
    def test_call_model_wandb_logging(self, mock_log, mock_completion, ai_caller):
        """
        Test the call_model method with W&B logging enabled.
        """
        mock_completion.return_value = [{"choices": [{"delta": {"content": "response"}}]}]
        prompt = {"system": "", "user": "Hello, world!"}
        with patch("cover_agent.ai_caller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)
            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10
            mock_log.assert_called_once()

    @patch("cover_agent.ai_caller.litellm.completion")
    def test_call_model_api_base(self, mock_completion, ai_caller):
        """
        Test the call_model method with a different API base.
        """
        mock_completion.return_value = [{"choices": [{"delta": {"content": "response"}}]}]
        ai_caller.model = "openai/test-model"
        prompt = {"system": "", "user": "Hello, world!"}
        with patch("cover_agent.ai_caller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)
            assert ai_caller.api_base == "test-api"
            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10

    @patch("cover_agent.ai_caller.litellm.completion")
    def test_call_model_with_system_key(self, mock_completion, ai_caller):
        """
        Test the call_model method with a system key in the prompt.
        """
        mock_completion.return_value = [{"choices": [{"delta": {"content": "response"}}]}]
        prompt = {"system": "System message", "user": "Hello, world!"}
        with patch("cover_agent.ai_caller.litellm.stream_chunk_builder") as mock_builder:
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
        assert str(exc_info.value) == "\"The prompt dictionary must contain 'system' and 'user' keys.\""

    @patch("cover_agent.ai_caller.litellm.completion")
    def test_call_model_o1_preview(self, mock_completion, ai_caller):
        """
        Test the call_model method with the 'o1-preview' model.
        """
        ai_caller.model = "o1-preview"
        prompt = {"system": "System message", "user": "Hello, world!"}
        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="response"))]
        mock_response.usage = Mock(prompt_tokens=2, completion_tokens=10)
        mock_completion.return_value = mock_response
        # Call the method
        response, prompt_tokens, response_tokens = ai_caller.call_model(prompt, stream=False)
        assert response == "response"
        assert prompt_tokens == 2
        assert response_tokens == 10

    @patch("cover_agent.ai_caller.litellm.completion")
    def test_call_model_streaming_response(self, mock_completion, ai_caller):
        """
        Test the call_model method with a streaming response.
        """
        prompt = {"system": "", "user": "Hello, world!"}
        # Mock the response to be an iterable of chunks
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="response part"))]
        mock_completion.return_value = [mock_chunk]
        with patch("cover_agent.ai_caller.litellm.stream_chunk_builder") as mock_builder:
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt, stream=True)
            assert response == "response"
            assert prompt_tokens == 2

    @patch("cover_agent.ai_caller.litellm.completion")
    @patch.dict(os.environ, {"WANDB_API_KEY": "test_key"})
    @patch("cover_agent.ai_caller.Trace.log")
    def test_call_model_wandb_logging_exception(self, mock_log, mock_completion, ai_caller):
        """
        Test the call_model method with W&B logging and handle logging exceptions.
        """
        # Create a proper mock chunk with the correct structure
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="response"))]
        mock_completion.return_value = [mock_chunk]

        mock_log.side_effect = Exception("Logging error")
        prompt = {"system": "", "user": "Hello, world!"}

        with (
            patch("cover_agent.ai_caller.litellm.stream_chunk_builder") as mock_builder,
            patch.object(ai_caller.logger, "error") as mock_logger,
        ):
            mock_builder.return_value = {
                "choices": [{"message": {"content": "response"}}],
                "usage": {"prompt_tokens": 2, "completion_tokens": 10},
            }
            response, prompt_tokens, response_tokens = ai_caller.call_model(prompt)

            assert response == "response"
            assert prompt_tokens == 2
            assert response_tokens == 10
            mock_logger.assert_called_once_with("Error logging to W&B: Logging error")
