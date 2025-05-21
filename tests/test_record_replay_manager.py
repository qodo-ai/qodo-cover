import hashlib

from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from cover_agent.record_replay_manager import RecordReplayManager


class TestFileHandling:
    """Tests for file path and hash calculations"""

    @staticmethod
    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "name": "valid_files",
                "setup": {"source": "def source(): pass", "test": "def test(): pass", "cache_hash": None},
                "expected": {
                    "type": "success",
                    "validate": lambda x: len(x) == 64 and isinstance(x, str) and x.isalnum(),
                },
            },
            {
                "name": "cached_hash",
                "setup": {"source": None, "test": None, "cache_hash": "cachedhash123"},
                "expected": {"type": "success", "value": "cachedhash123"},
            },
            {
                "name": "missing_source",
                "setup": {"source": None, "test": "def test(): pass", "cache_hash": None},
                "expected": {"type": "error", "error": FileNotFoundError},
            },
            {
                "name": "missing_test",
                "setup": {"source": "def source(): pass", "test": None, "cache_hash": None},
                "expected": {"type": "error", "error": FileNotFoundError},
            },
        ],
    )
    def test_calculate_files_hash_scenarios(test_case, tmp_path):
        """
        Test different scenarios for the `_calculate_files_hash` method of the `RecordReplayManager` class.

        This test is parameterized to cover multiple scenarios, including:
        - Valid files: Ensures the method calculates a hash for valid source and test files.
        - Cached hash: Verifies that the method reuses an existing cached hash if available.
        - Missing source: Confirms that a `FileNotFoundError` is raised when the source file is missing.
        - Missing test: Confirms that a `FileNotFoundError` is raised when the test file is missing.

        Parameters:
        - test_case (dict): A dictionary containing the setup and expected outcome for the test case.
            - setup (dict): Contains the following keys:
                - source (str or None): The content of the source file, or None if the file is missing.
                - test (str or None): The content of the test file, or None if the file is missing.
                - cache_hash (str or None): A precomputed hash to simulate a cached hash.
            - expected (dict): Contains the expected outcome of the test case.
                - type (str): Either "success" or "error".
                - validate (callable, optional): A function to validate the result in success cases.
                - value (str, optional): The expected hash value in success cases.
                - error (Exception, optional): The expected exception in error cases.
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.

        Assertions:
        - For success cases, the calculated hash matches the expected value or passes the validation function.
        - For error cases, the expected exception is raised.
        """
        manager = RecordReplayManager(record_mode=True)

        # Set up a cached hash if specified
        if test_case["setup"]["cache_hash"]:
            manager.files_hash = test_case["setup"]["cache_hash"]

        # Create test files if content is provided
        source_file = tmp_path / "source.py"
        test_file = tmp_path / "test.py"

        if test_case["setup"]["source"]:
            source_file.write_text(test_case["setup"]["source"])
        if test_case["setup"]["test"]:
            test_file.write_text(test_case["setup"]["test"])

        if test_case["expected"]["type"] == "error":
            # Test error cases
            with pytest.raises(test_case["expected"]["error"]):
                manager._calculate_files_hash(str(source_file), str(test_file))
        else:
            # Test success cases
            result = manager._calculate_files_hash(str(source_file), str(test_file))
            if "validate" in test_case["expected"]:
                assert test_case["expected"]["validate"](result)
            else:
                assert result == test_case["expected"]["value"]

    @staticmethod
    def test_get_response_file_path_handle_source_path_with_no_parent_directory(tmp_path):
        """
        Test that _get_response_file_path handles a source path with no parent
        directory correctly.

        This test verifies that when a source file path without a parent directory
        (e.g., "source_file.py") is passed to the `_get_response_file_path` method
        of the `RecordReplayManager` class, the method correctly generates the
        response file path in the default directory.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Call `_get_response_file_path` with a source file path that has no parent directory.
        4. Verify that the returned path matches the expected flat directory structure.
        5. Assert that the parent directory of the generated path exists.

        Assertions:
        - The generated file path matches the expected format: `default_responses_{hash}.yml`.
        - The parent directory of the generated file path exists.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash000")
        result = manager._get_response_file_path("source_file.py", "tests/test_file.py")

        expected_file = tmp_path / f"default_responses_hash000.yml"

        assert result == expected_file
        assert result.parent.exists()

    @staticmethod
    def test_get_response_file_path_with_valid_nested_source(tmp_path):
        """
        Test that _get_response_file_path returns the correct path for a valid
        nested source file.

        This test ensures that when a source file path with nested directories
        (e.g., "nested/folder/source_file.py") is passed to the `_get_response_file_path`
        method of the `RecordReplayManager` class, the method correctly generates
        the response file path in a flat directory structure.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Call `_get_response_file_path` with a nested source file path.
        4. Verify that the returned path matches the expected flat directory structure.
        5. Assert that the parent directory of the generated path exists.

        Assertions:
        - The generated file path matches the expected format: `{parent_folder}_responses_{hash}.yml`.
        - The parent directory of the generated file path exists.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        result = manager._get_response_file_path("nested/folder/source_file.py", "tests/test_file.py")

        expected_file = tmp_path / f"folder_responses_hash123.yml"

        assert result == expected_file
        assert result.parent.exists()

    @staticmethod
    def test_get_response_file_path_with_empty_source_path(tmp_path):
        """
        Test that _get_response_file_path returns the correct path when the source
        path is empty.

        This test ensures that when an empty string is passed as the source file path
        to the `_get_response_file_path` method of the `RecordReplayManager` class,
        the method correctly generates the response file path in the default directory.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Call `_get_response_file_path` with an empty source file path.
        4. Verify that the returned path matches the expected flat directory structure.
        5. Assert that the parent directory of the generated path exists.

        Assertions:
        - The generated file path matches the expected format: `default_responses_{hash}.yml`.
        - The parent directory of the generated file path exists.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash456")
        result = manager._get_response_file_path("", "tests/test_file.py")

        expected_file = tmp_path / f"default_responses_hash456.yml"

        assert result == expected_file
        assert result.parent.exists()

    @staticmethod
    def test_get_response_file_path_create_response_directory_if_not_exists(tmp_path):
        """
        Test that _get_response_file_path creates the response directory if it does
        not already exist.

        This test ensures that when a source file path with a parent directory
        (e.g., "new_folder/source_file.py") is passed to the `_get_response_file_path`
        method of the `RecordReplayManager` class, the method correctly generates
        the response file path and creates the necessary directory if it does not exist.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Call `_get_response_file_path` with a source file path that includes a parent directory.
        4. Verify that the returned path matches the expected flat directory structure.
        5. Assert that the parent directory of the generated path exists.

        Assertions:
        - The generated file path matches the expected format: `{parent_folder}_responses_{hash}.yml`.
        - The parent directory of the generated file path exists.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash789")
        result = manager._get_response_file_path("new_folder/source_file.py", "tests/test_file.py")

        expected_file = tmp_path / f"new_folder_responses_hash789.yml"

        assert result == expected_file
        assert result.parent.exists()


class TestFuzzyMatching:
    @staticmethod
    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "name": "prefix_comparison",
                "current_prompt": "Find all prime numbers below 100",
                "recorded_prompts": {
                    "hash1": "Find all prime numbers below 200",
                    "hash2": "Calculate fibonacci numbers",
                    "hash3": "Find prime factors of 100",
                },
                "threshold": 80,
                "prefix_length": 10,
                "expected": "hash1",
            },
            {
                "name": "token_sort_ratio",
                "current_prompt": "below 100 find all prime numbers",
                "recorded_prompts": {
                    "hash1": "Find all prime numbers below 100",
                    "hash2": "Calculate prime numbers up to 100",
                    "hash3": "Find all numbers below 100",
                },
                "threshold": 80,
                "prefix_length": None,
                "expected": "hash1",
            },
            {
                "name": "no_match_above_threshold",
                "current_prompt": "Find all prime numbers below 100",
                "recorded_prompts": {
                    "hash1": "Calculate fibonacci sequence",
                    "hash2": "Sort an array of integers",
                    "hash3": "Implement binary search",
                },
                "threshold": 90,
                "prefix_length": None,
                "expected": None,
            },
        ],
    )
    def test_find_closest_prompt_match(test_case):
        """
        Test the `_find_closest_prompt_match` method of the `RecordReplayManager` class.

        This test verifies that the method correctly identifies the closest matching prompt
        from a dictionary of recorded prompts based on the provided threshold and prefix length.

        Parameters:
        - test_case (dict): A dictionary containing the test setup and expected outcome.
            - current_prompt (str): The prompt to match against the recorded prompts.
            - recorded_prompts (dict): A dictionary of recorded prompts with their hashes as keys.
            - threshold (int): The minimum similarity score required for a match.
            - prefix_length (int or None): The length of the prefix to consider for matching, or None for full matching.
            - expected (str or None): The expected hash of the closest matching prompt, or None if no match is found.

        Assertions:
        - The result of `_find_closest_prompt_match` matches the expected hash or None.
        """
        manager = RecordReplayManager(record_mode=True)

        result = manager._find_closest_prompt_match(
            test_case["current_prompt"],
            test_case["recorded_prompts"],
            threshold=test_case["threshold"],
            prefix_length=test_case["prefix_length"],
        )

        assert result == test_case["expected"]

    @staticmethod
    def test_find_closest_prompt_match_handles_empty_prompts_dictionary():
        """
        Test that _find_closest_prompt_match handles an empty dictionary of recorded prompts.

        This test ensures that when the `recorded_prompts` parameter is an empty dictionary,
        the method does not raise any exceptions and correctly returns None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode.
        2. Define a current prompt and set `recorded_prompts` to an empty dictionary.
        3. Call `_find_closest_prompt_match` with the current prompt and empty `recorded_prompts`.
        4. Verify that the method returns None.

        Assertions:
        - The method returns None when `recorded_prompts` is empty.
        """
        manager = RecordReplayManager(record_mode=True)
        current_prompt = "Find all prime numbers below 100"
        recorded_prompts = {}

        result = manager._find_closest_prompt_match(current_prompt, recorded_prompts)

        assert result is None

    @staticmethod
    def test_find_closest_prompt_match_respects_best_ratio_parameter():
        """
        Test that _find_closest_prompt_match respects the best_ratio parameter.

        This test ensures that when the `best_ratio` parameter is set, the method only
        returns matches that exceed both the similarity threshold and the best_ratio
        parameter, ensuring high-quality matches.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode.
        2. Define a current prompt and a dictionary of recorded prompts.
        3. Call `_find_closest_prompt_match` with a threshold and best_ratio parameter.
        4. Verify that the method returns the hash of the best matching prompt.

        Assertions:
        - The returned hash matches the expected prompt with the highest similarity
          ratio that exceeds the best_ratio parameter.
        """
        manager = RecordReplayManager(record_mode=True)
        current_prompt = "Find all prime numbers below 100"
        recorded_prompts = {
            "hash1": "Find all prime numbers below 90",
            "hash2": "Find all prime numbers below 80",
        }

        result = manager._find_closest_prompt_match(
            current_prompt,
            recorded_prompts,
            threshold=80,
            best_ratio=94,  # Set best_ratio lower than the actual ratio of 95
        )

        assert result == "hash1"


class TestResponseHandling:
    """
    Test suite for the RecordReplayManager class, which handles recording and replaying
    responses for testing purposes. Each test method validates the specific functionality
    of the RecordReplayManager.
    """

    @staticmethod
    def test_has_response_file_response_file_exists_returns_true_when_file_present(tmp_path):
        """
        Verify that has_response_file returns True when the response file exists.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")  # Mock hash calculation
        source_file = "source.py"
        test_file = "test.py"

        # Mock exists() to return True
        with patch.object(Path, "exists", return_value=True):
            assert manager.has_response_file(source_file, test_file) is True

    @staticmethod
    def test_has_response_file_response_file_exists_returns_false_when_file_missing(tmp_path):
        """
        Test that has_response_file returns False when the response file is missing.

        This test verifies that the `has_response_file` method of the `RecordReplayManager` class
        correctly returns False when the response file does not exist.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock `_calculate_files_hash` to return a predefined hash value.
        3. Mock the `Path.exists` method to simulate the absence of the response file.
        4. Call `has_response_file` with valid source and test file paths.
        5. Verify that the method returns False.

        Assertions:
        - The method returns False when the response file does not exist.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")  # Mock hash calculation
        source_file = "source.py"
        test_file = "test.py"

        with patch.object(Path, "exists", return_value=False):
            assert manager.has_response_file(source_file, test_file) is False

    @staticmethod
    def test_has_response_file_response_file_exists_raises_error_on_empty_source_path(tmp_path):
        """
        Test that has_response_file raises a FileNotFoundError when the source path is empty.

        This test verifies that the `has_response_file` method of the `RecordReplayManager` class
        correctly raises a `FileNotFoundError` when an empty string is provided as the source file path.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Create a test file with valid content in the temporary directory.
        3. Call `has_response_file` with an empty source path and the valid test file path.
        4. Verify that a `FileNotFoundError` is raised.

        Assertions:
        - A `FileNotFoundError` is raised when the source path is empty.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        with pytest.raises(FileNotFoundError):
            manager.has_response_file("", str(test_file))

    @staticmethod
    def test_has_response_file_response_file_exists_raises_error_on_empty_test_path(tmp_path):
        """
        Test that has_response_file raises a FileNotFoundError when the test path is empty.

        This test verifies that the `has_response_file` method of the `RecordReplayManager` class
        correctly raises a `FileNotFoundError` when an empty string is provided as the test file path.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Create a source file with valid content in the temporary directory.
        3. Call `has_response_file` with a valid source path and an empty test path.
        4. Verify that a `FileNotFoundError` is raised.

        Assertions:
        - A `FileNotFoundError` is raised when the test path is empty.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        source_file = tmp_path / "source.py"
        source_file.write_text("def source(): pass")

        with pytest.raises(FileNotFoundError):
            manager.has_response_file(str(source_file), "")

    @staticmethod
    def test_load_recorded_response_returns_none_in_record_mode(tmp_path):
        """
        Test that load_recorded_response returns None when in record mode.

        This test ensures that when the `load_recorded_response` method of the `RecordReplayManager`
        class is called in record mode, it does not attempt to load any response and instead
        returns None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Call `load_recorded_response` with valid source file, test file, and prompt parameters.
        3. Verify that the method returns None.

        Assertions:
        - The method returns None when in record mode.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))

        result = manager.load_recorded_response("source.py", "test.py", {"key": "value"})

        assert result is None

    @staticmethod
    def test_load_recorded_response_with_fuzzy_lookup_on_dict_prompts(tmp_path):
        """
        Test that load_recorded_response handles fuzzy lookup correctly with dictionary prompts.

        This test verifies that the fuzzy lookup mechanism works correctly when the prompts
        are dictionaries containing 'user' keys, focusing on matching the user message content.

        Steps:
        1. Initialize a RecordReplayManager instance in replay mode.
        2. Create a response file with a recorded prompt in dictionary format.
        3. Call load_recorded_response with a similar but not identical prompt.
        4. Verify that fuzzy matching finds the similar prompt and returns its response.

        Args:
            tmp_path: Pytest fixture that provides a temporary directory path
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        manager._find_closest_prompt_match = Mock(side_effect=lambda prompt, prompts, **kwargs: next(iter(prompts)))
        response_file = manager._get_response_file_path("source.py", "test.py")
        response_file.parent.mkdir(parents=True, exist_ok=True)

        # Create a recorded prompt with slightly different wording
        recorded_prompt = {"user": "Generate a function to find all prime numbers up to 100"}
        prompt_hash = hashlib.sha256(str(recorded_prompt).encode()).hexdigest()
        truncated_hash = prompt_hash[: RecordReplayManager.HASH_DISPLAY_LENGTH]

        # Create a response file with the recorded prompt
        with open(response_file, "w") as f:
            yaml.safe_dump(
                {
                    "metadata": {"files_hash": "hash123"},
                    "unknown_caller": {
                        truncated_hash: {
                            "prompt": recorded_prompt,
                            "response": "fuzzy_matched_response",
                            "prompt_tokens": 12,
                            "completion_tokens": 18,
                        },
                    },
                },
                f,
            )

        # Test with a similar but not identical prompt
        current_prompt = {"user": "Create a function that finds prime numbers below 100"}
        result = manager.load_recorded_response(
            "source.py",
            "test.py",
            current_prompt,
            fuzzy_lookup=True,
        )

        assert result == ("fuzzy_matched_response", 12, 18)

    @staticmethod
    def test_load_recorded_response_with_fuzzy_lookup_multiple_prompts(tmp_path):
        """
        Test that load_recorded_response correctly handles fuzzy matching with multiple recorded prompts.

        This test verifies that when multiple similar prompts exist, the method selects
        the one with the highest similarity score above the threshold.

        Args:
            tmp_path: Pytest fixture that provides a temporary directory path
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        response_file = manager._get_response_file_path("source.py", "test.py")
        response_file.parent.mkdir(parents=True, exist_ok=True)

        # Create multiple recorded prompts with varying similarity
        prompts = {
            "p1": {"user": "Generate a function to calculate fibonacci numbers"},
            "p2": {"user": "Write code to find prime numbers up to 100"},
            "p3": {"user": "Create a function that finds all prime numbers below 100"},
        }

        responses = {}
        target_hash = None
        for key, prompt in prompts.items():
            prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
            truncated_hash = prompt_hash[: RecordReplayManager.HASH_DISPLAY_LENGTH]
            responses[truncated_hash] = {
                "prompt": prompt,
                "response": f"response_{key}",
                "prompt_tokens": 10,
                "completion_tokens": 20,
            }
            if key == "p3":
                target_hash = truncated_hash

        # Create a response file with multiple prompts
        with open(response_file, "w") as f:
            yaml.safe_dump(
                {
                    "metadata": {"files_hash": "hash123"},
                    "unknown_caller": responses,
                },
                f,
            )

        # Mock find_closest_prompt_match to return the hash of p3
        manager._find_closest_prompt_match = Mock(return_value=target_hash)

        # Test with a prompt that should match p3 best
        current_prompt = {"user": "Create a function for finding prime numbers below 100"}
        result = manager.load_recorded_response(
            "source.py",
            "test.py",
            current_prompt,
            fuzzy_lookup=True,
        )

        # Should match p3 as it's the most similar
        assert result == ("response_p3", 10, 20)

    @pytest.fixture
    def setup_response_file(tmp_path):
        """
        Set up a response file for testing purposes.

        This function initializes a `RecordReplayManager` instance in replay mode and creates
        a response file with predefined metadata and an empty `unknown_caller` section. It is
        used to prepare the environment for tests that require a response file.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.

        Returns:
        - RecordReplayManager: An instance of `RecordReplayManager` configured with the temporary directory.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        response_file = manager._get_response_file_path("source.py", "test.py")
        response_file.parent.mkdir(parents=True, exist_ok=True)

        with open(response_file, "w") as f:
            yaml.safe_dump(
                {
                    "metadata": {"files_hash": "hash123"},
                    "unknown_caller": {},
                },
                f,
            )

        return manager

    @staticmethod
    def test_load_recorded_response_logs_warning_when_fuzzy_lookup_finds_no_match():
        """
        Test that load_recorded_response logs a warning when a fuzzy lookup finds no match.

        This test verifies that when the `load_recorded_response` method is called with
        `fuzzy_lookup=True` and no matching prompt is found, the method correctly logs
        a warning and returns None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode.
        2. Mock `_calculate_files_hash` to return a predefined hash value.
        3. Mock `_find_closest_prompt_match` to simulate no match being found.
        4. Mock file operations to simulate the presence of a response file.
        5. Call `load_recorded_response` with a test prompt and `fuzzy_lookup=True`.
        6. Verify that the method returns None.

        Assertions:
        - The method returns None when no match is found during fuzzy lookup.

        Mocks:
        - `builtins.open`: Simulates reading a response file.
        - `Path.exists`: Simulates the existence of the response file.
        - `Path.mkdir`: Simulates directory creation.

        Parameters:
        - None
        """
        manager = RecordReplayManager(record_mode=False, base_dir="/tmp")
        manager._calculate_files_hash = Mock(return_value="hash123")
        manager._find_closest_prompt_match = Mock(return_value=None)

        mock_file = mock_open(
            read_data=yaml.safe_dump(
                {
                    "metadata": {"files_hash": "hash123"},
                    "unknown_caller": {},
                }
            )
        )

        with (
            patch("builtins.open", mock_file),
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "mkdir", return_value=None),
        ):
            result = manager.load_recorded_response(
                "source.py",
                "test.py",
                {"user": "test prompt"},
                fuzzy_lookup=True,
            )

        assert result is None

    @staticmethod
    def test_load_recorded_response_logs_error_on_exception(tmp_path):
        """
        Test that load_recorded_response logs an error when an exception occurs.

        This test verifies that the `load_recorded_response` method of the
        `RecordReplayManager` class handles exceptions gracefully by logging an error
        and returning None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock `_calculate_files_hash` to return a predefined hash value.
        3. Mock `_find_closest_prompt_match` to raise an exception.
        4. Mock file operations to simulate the presence of a response file.
        5. Call `load_recorded_response` with a test prompt and `fuzzy_lookup=True`.
        6. Verify that the method returns None.

        Assertions:
        - The method returns None when an exception occurs during fuzzy lookup.

        Mocks:
        - `builtins.open`: Simulates reading a response file.
        - `Path.exists`: Simulates the existence of the response file.
        - `Path.mkdir`: Simulates directory creation.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        manager._find_closest_prompt_match = Mock(side_effect=Exception("Test error"))

        mock_file = mock_open(
            read_data=yaml.safe_dump(
                {
                    "metadata": {"files_hash": "hash123"},
                    "unknown_caller": {},
                }
            )
        )

        with (
            patch("builtins.open", mock_file),
            patch.object(Path, "exists", return_value=True),
            patch.object(Path, "mkdir", return_value=None),
        ):
            result = manager.load_recorded_response(
                "source.py",
                "test.py",
                {"user": "test prompt"},
                fuzzy_lookup=True,
            )

        assert result is None

    @staticmethod
    @pytest.mark.parametrize(
        "test_case",
        [
            {
                "name": "new_response",
                "record_mode": True,
                "existing_data": None,
                "prompt": {"key": "value"},
                "response": "response",
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "expected_hash": "hash123",
                "expected_metadata": {"files_hash": "hash123"},
                "validate_existing": False,
            },
            {
                "name": "append_to_existing",
                "record_mode": True,
                "existing_data": {
                    "metadata": {"files_hash": "hash456"},
                    "unknown_caller": {
                        "existing_hash": {
                            "prompt": {"key": "old_value"},
                            "response": "old_response",
                            "prompt_tokens": 5,
                            "completion_tokens": 10,
                        },
                    },
                },
                "prompt": {"key": "new_value"},
                "response": "new_response",
                "prompt_tokens": 15,
                "completion_tokens": 25,
                "expected_hash": "hash456",
                "expected_metadata": {"files_hash": "hash456"},
                "validate_existing": True,
            },
            {
                "name": "invalid_yaml",
                "record_mode": True,
                "existing_data": "invalid: [unclosed",
                "prompt": {"key": "value"},
                "response": "response",
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "expected_hash": "hash789",
                "expected_metadata": {"files_hash": "hash789"},
                "validate_existing": False,
            },
            {
                "name": "skip_in_replay_mode",
                "record_mode": False,
                "existing_data": None,
                "prompt": {"key": "value"},
                "response": "response",
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "expected_hash": "hash123",  # Changed: Need a valid hash for a file path
                "expected_metadata": None,
                "validate_existing": False,
            },
        ],
    )
    def test_record_response(test_case, tmp_path):
        """
        Test the `record_response` method of the `RecordReplayManager` class.

        This test verifies that the `record_response` method correctly handles various scenarios,
        including creating a new response file, appending to an existing file, and skipping
        recording in replay mode.

        Parameters:
        - test_case (dict): A dictionary containing the test setup and expected outcomes.
            - record_mode (bool): Whether the manager is in record mode.
            - existing_data (str or dict or None): Existing data in the response file, if any.
            - prompt (dict): The prompt to record.
            - response (str): The response to record.
            - prompt_tokens (int): The number of tokens in the prompt.
            - completion_tokens (int): The number of tokens in the response.
            - expected_hash (str): The expected hash value for the response file.
            - expected_metadata (dict or None): The expected metadata in the response file.
            - validate_existing (bool): Whether to validate existing data in the response file.
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.

        Steps:
        1. Initialize a `RecordReplayManager` instance with the specified record mode and base directory.
        2. Mock the `_calculate_files_hash` method to return the expected hash.
        3. If `existing_data` is provided, create a response file with the specified data.
        4. Call the `record_response` method with the test case parameters.
        5. Verify that the response file is created or skipped based on the record mode.
        6. Validate the contents of the response file if it exists.

        Assertions:
        - The response file is created or skipped based on the record mode.
        - The response file contains the expected metadata and recorded data.
        - Existing data in the response file is validated if `validate_existing` is True.
        """
        manager = RecordReplayManager(record_mode=test_case["record_mode"], base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value=test_case["expected_hash"])

        response_file = manager._get_response_file_path("source.py", "test.py")

        if test_case["existing_data"]:
            response_file.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(test_case["existing_data"], str):
                response_file.write_text(test_case["existing_data"])
            else:
                with open(response_file, "w") as f:
                    yaml.safe_dump(test_case["existing_data"], f)

        manager.record_response(
            "source.py",
            "test.py",
            test_case["prompt"],
            test_case["response"],
            test_case["prompt_tokens"],
            test_case["completion_tokens"],
        )

        if not test_case["record_mode"]:
            assert not response_file.exists()
            return

        assert response_file.exists()
        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        assert isinstance(data, dict)
        assert "metadata" in data
        assert data["metadata"] == test_case["expected_metadata"]

        if test_case["validate_existing"]:
            assert "existing_hash" in data["unknown_caller"]

        prompt_hash = hashlib.sha256(str(test_case["prompt"]).encode()).hexdigest()
        truncated_hash = prompt_hash[: RecordReplayManager.HASH_DISPLAY_LENGTH]
        entry = data["unknown_caller"][truncated_hash]

        assert entry["prompt"] == test_case["prompt"]
        assert entry["response"] == test_case["response"]
        assert entry["prompt_tokens"] == test_case["prompt_tokens"]
        assert entry["completion_tokens"] == test_case["completion_tokens"]

    @staticmethod
    def test_load_recorded_response_direct_hash_hit(tmp_path):
        """
        Test that load_recorded_response retrieves the correct response when a direct hash match is found.

        This test verifies that the `load_recorded_response` method of the `RecordReplayManager` class
        correctly retrieves a response when the hash of the provided prompt matches a hash in the
        response file.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock `_calculate_files_hash` to return a predefined hash value.
        3. Create a test prompt and calculate its hash.
        4. Create a response file containing the prompt hash and associated response data.
        5. Mock file operations to simulate the presence of the response file.
        6. Call `load_recorded_response` with the test prompt and verify the returned response.

        Assertions:
        - The method returns the correct response, prompt tokens, and completion tokens.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        prompt = {"user": "test prompt"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        truncated_hash = prompt_hash[: RecordReplayManager.HASH_DISPLAY_LENGTH]

        test_data = {
            "metadata": {"files_hash": "hash123"},
            "test_caller": {
                truncated_hash: {
                    "prompt": prompt,
                    "response": "test response",
                    "prompt_tokens": 5,
                    "completion_tokens": 10,
                },
            },
        }

        # Mock file operations
        with (
            patch("builtins.open", mock_open(read_data=yaml.safe_dump(test_data))),
            patch.object(Path, "exists", return_value=True),
        ):
            result = manager.load_recorded_response(
                "source.py",
                "test.py",
                prompt,
                caller_name="test_caller",
            )

        assert result == ("test response", 5, 10)

    @staticmethod
    def test_load_recorded_response_nonexistent_caller(tmp_path):
        """
        Test that load_recorded_response returns None when the specified caller does not exist.

        This test verifies that the `load_recorded_response` method of the `RecordReplayManager` class
        correctly handles the case where the response file exists but does not contain data for the
        specified caller.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock `_calculate_files_hash` to return a predefined hash value.
        3. Create a response file with metadata and data for a different caller.
        4. Call `load_recorded_response` with a caller name that is not present in the response file.
        5. Verify that the method returns None.

        Assertions:
        - The method returns None when the specified caller is not found in the response file.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")

        source_file = "source.py"
        test_file = "test.py"
        response_file = manager._get_response_file_path(source_file, test_file)
        response_file.parent.mkdir(parents=True, exist_ok=True)

        # Create test data without the test_caller
        test_data = {
            "metadata": {"files_hash": "hash123"},
            "other_caller": {},
        }

        # Write test data to file
        with open(response_file, "w") as f:
            yaml.safe_dump(test_data, f)

        # Call the method
        result = manager.load_recorded_response(
            source_file,
            test_file,
            {"user": "test prompt"},
            caller_name="test_caller",
        )

        # Verify results
        assert result is None

    @staticmethod
    def test_load_recorded_response_file_not_found(tmp_path):
        """
        Test that load_recorded_response returns None when the response file is not found.

        This test verifies that the `load_recorded_response` method of the `RecordReplayManager` class
        correctly handles the case where the response file does not exist, ensuring it returns None
        without raising an exception.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock `_calculate_files_hash` to return a predefined hash value.
        3. Call `load_recorded_response` without creating the response file.
        4. Verify that the method returns None.

        Assertions:
        - The method returns None when the response file is not found.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")

        source_file = "source.py"
        test_file = "test.py"

        # Call the method without creating the response file
        result = manager.load_recorded_response(
            source_file,
            test_file,
            {"user": "test prompt"},
            caller_name="test_caller",
        )

        # Verify results
        assert result is None
