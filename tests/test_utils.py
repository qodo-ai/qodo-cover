from unittest.mock import patch

import cover_agent.utils as utils


class TestStreamRecordedLLMResponse:

    @staticmethod
    def test_stream_recorded_llm_response_outputs_text_with_natural_pacing(capsys):
        """
        Tests that the `stream_recorded_llm_response` function outputs text with natural pacing.

        This test verifies that the function correctly outputs the provided content with a space
        and newline at the end, and that it calls `time.sleep` with the expected delay to simulate
        natural pacing.

        Args:
            capsys: A pytest fixture used to capture stdout and stderr during the test.

        Assertions:
            - The captured output matches the expected formatted content.
            - The `time.sleep` function is called with a delay of 0.01 seconds.
        """
        content = "Hello world"

        with patch("time.sleep") as mock_sleep:
            utils.stream_recorded_llm_response(content)

            captured = capsys.readouterr()
            assert captured.out == "Hello world \n"
            mock_sleep.assert_called_with(0.01)

    @staticmethod
    def test_stream_recorded_llm_response_preserves_yaml_indentation(capsys):
        content = "root:\n  child:\n    item"

        with patch("time.sleep"):
            utils.stream_recorded_llm_response(content)

            captured = capsys.readouterr()
            assert captured.out == "root: \n  child: \n    item \n"

    @staticmethod
    def test_stream_recorded_llm_response_handles_multiple_empty_lines(capsys):
        """
        Tests that the `stream_recorded_llm_response` function preserves YAML indentation.

        This test verifies that the function correctly outputs the provided YAML content
        with proper indentation, appending a space and newline at the end of each line.

        Args:
            capsys: A pytest fixture used to capture stdout and stderr during the test.

        Assertions:
            - The captured output matches the expected YAML content with preserved indentation
              and a trailing space and newline added to each line.
        """
        content = "line1\n\n\nline2"

        with patch("time.sleep"):
            utils.stream_recorded_llm_response(content)

            captured = capsys.readouterr()
            assert captured.out == "line1 \n\n\nline2 \n"

    @staticmethod
    def test_stream_recorded_llm_response_handles_complex_whitespace_formatting(capsys):
        content = "  indented\n    more\n      most  "

        with patch("time.sleep"):
            utils.stream_recorded_llm_response(content)

            captured = capsys.readouterr()
            assert captured.out == "  indented \n    more \n      most \n"

    @staticmethod
    def test_stream_recorded_llm_response_handles_empty_input(capsys):
        """
        Tests that the `stream_recorded_llm_response` function handles complex whitespace formatting.

        This test verifies that the function correctly processes input with varying levels of indentation
        and trailing spaces, ensuring that each line is output with a trailing space and newline.

        Args:
            capsys: A pytest fixture used to capture stdout and stderr during the test.

        Assertions:
            - The captured output matches the expected formatted content, preserving indentation
              and appending a trailing space and newline to each line.
        """
        content = ""

        with patch("time.sleep"):
            utils.stream_recorded_llm_response(content)

            captured = capsys.readouterr()
            assert captured.out == ""

    @staticmethod
    def test_stream_recorded_llm_response_preserves_spacing_between_words(capsys):
        """
        Tests that the `stream_recorded_llm_response` function preserves spacing between words.

        This test verifies that the function correctly processes input with multiple spaces
        between words, ensuring that the output consolidates the spaces into a single space
        and appends a trailing space and newline.

        Args:
            capsys: A pytest fixture used to capture stdout and stderr during the test.

        Assertions:
            - The captured output matches the expected content with consolidated spaces
              and a trailing space and newline.
        """
        content = "word1   word2     word3"

        with patch("time.sleep"):
            utils.stream_recorded_llm_response(content)

            captured = capsys.readouterr()
            assert captured.out == "word1 word2 word3 \n"
