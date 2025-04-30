from unittest.mock import patch

import cover_agent.utils as utils


class TestRecordReplayManager:
    """
    A test class for the RecordReplayManager.

    This class contains test methods to verify the functionality of the
    RecordReplayManager class, including methods for handling hash truncation,
    streaming recorded responses, and preserving formatting.

    Attributes:
        HASH_DISPLAY_LENGTH (int): The standard length to which hash strings
        are truncated for display purposes.
    """

    HASH_DISPLAY_LENGTH = 12

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

    def test_truncate_hash_truncates_hash_to_standard_length(self):
        """
        Test that _truncate_hash correctly truncates a hash to the standard display length.

        This test verifies that the _truncate_hash method of the RecordReplayManager class
        truncates a full-length hash string to the predefined HASH_DISPLAY_LENGTH. It also
        ensures that the truncated hash has the correct length.

        Assertions:
            - The truncated hash matches the expected first HASH_DISPLAY_LENGTH characters
              of the full hash.
            - The length of the truncated hash is equal to HASH_DISPLAY_LENGTH.
        """
        full_hash = "1234567890abcdef1234567890abcdef"
        truncated_hash = utils.truncate_hash(full_hash, self.HASH_DISPLAY_LENGTH)

        assert truncated_hash == "1234567890ab"
        assert len(truncated_hash) == self.HASH_DISPLAY_LENGTH

    def test_truncate_hash_handles_empty_hash_value(self):
        """
        Test that _truncate_hash handles an empty hash value gracefully.

        This test verifies that when an empty string is passed to the _truncate_hash method
        of the RecordReplayManager class, it returns an empty string without errors. It also
        ensures that the length of the returned string is zero.

        Assertions:
            - The truncated hash is an empty string.
            - The length of the truncated hash is zero.
        """
        empty_hash = ""
        truncated_hash = utils.truncate_hash(empty_hash, self.HASH_DISPLAY_LENGTH)

        assert truncated_hash == ""
        assert len(truncated_hash) == 0

    def test_truncate_hash_handles_shorter_hash_than_standard_length(self):
        """
        Test that _truncate_hash handles a hash shorter than the standard display length.

        This test verifies that when a hash string shorter than the predefined HASH_DISPLAY_LENGTH
        is passed to the _truncate_hash method of the RecordReplayManager class, it returns the
        original hash string without truncation. It also ensures that the length of the returned
        string matches the length of the input hash.

        Assertions:
            - The truncated hash is equal to the original hash.
            - The length of the truncated hash matches the length of the input hash.
        """
        short_hash = "12345"
        truncated_hash = utils.truncate_hash(short_hash, self.HASH_DISPLAY_LENGTH)

        assert truncated_hash == "12345"
        assert len(truncated_hash) == len(short_hash)
