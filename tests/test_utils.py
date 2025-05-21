import cover_agent.utils as utils


HASH_DISPLAY_LENGTH = 12


def test_truncate_hash_truncates_hash_to_standard_length():
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
    truncated_hash = utils.truncate_hash(full_hash, HASH_DISPLAY_LENGTH)

    assert truncated_hash == "1234567890ab"
    assert len(truncated_hash) == HASH_DISPLAY_LENGTH


def test_truncate_hash_handles_empty_hash_value():
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
    truncated_hash = utils.truncate_hash(empty_hash, HASH_DISPLAY_LENGTH)

    assert truncated_hash == ""
    assert len(truncated_hash) == 0


def test_truncate_hash_handles_shorter_hash_than_standard_length():
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
    truncated_hash = utils.truncate_hash(short_hash, HASH_DISPLAY_LENGTH)

    assert truncated_hash == "12345"
    assert len(truncated_hash) == len(short_hash)
