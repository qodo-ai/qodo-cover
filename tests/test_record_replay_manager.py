import hashlib
import yaml

from unittest.mock import Mock

import pytest

from cover_agent.record_replay_manager import RecordReplayManager


class TestRecordReplayManager:
    """
    Test suite for the RecordReplayManager class, which handles recording and replaying
    responses for testing purposes. Each test method validates the specific functionality
    of the RecordReplayManager.
    """

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
    def test_load_recorded_response_returns_none_if_file_does_not_exist(tmp_path):
        """
        Test that load_recorded_response returns None if the response file does not exist.

        This test ensures that when the `load_recorded_response` method of the `RecordReplayManager`
        class is called and the response file is missing, the method does not raise an exception
        and instead returns None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Create source and test files with valid content in the temporary directory.
        3. Call `load_recorded_response` with the paths of the source and test files and a sample prompt.
        4. Verify that the method returns None.

        Assertions:
        - The method returns None when the response file does not exist.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        source_file = tmp_path / "source.py"
        test_file = tmp_path / "test.py"
        source_file.write_text("def test(): pass")
        test_file.write_text("def test(): pass")

        result = manager.load_recorded_response(str(source_file), str(test_file), {"key": "value"})

        assert result is None

    @staticmethod
    def test_load_recorded_response_returns_none_if_prompt_hash_not_found(tmp_path):
        """
        Test that load_recorded_response returns None if the prompt hash is not found
        in the response file.

        This test ensures that when the `load_recorded_response` method of the `RecordReplayManager`
        class is called and the response file does not contain the expected prompt hash, the method
        returns None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Create a response file with a different hash and some existing data.
        4. Call `load_recorded_response` with valid parameters.
        5. Verify that the method returns None.

        Assertions:
        - The method returns None when the prompt hash is not found in the response file.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        response_file = tmp_path / "default" / "responses_hash123.yml"
        response_file.parent.mkdir(parents=True, exist_ok=True)
        with open(response_file, "w") as f:
            yaml.safe_dump({"other_hash": {"response": "old_response"}}, f)

        result = manager.load_recorded_response("source.py", "test.py", {"key": "value"})

        assert result is None

    @staticmethod
    def test_load_recorded_response_returns_correct_data_for_valid_prompt_hash(tmp_path):
        """
        Test that load_recorded_response returns the correct data when the prompt hash
        is found in the response file.

        This test ensures that when the `load_recorded_response` method of the `RecordReplayManager`
        class is called and the response file contains a valid prompt hash, the method retrieves
        the correct response data.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Generate the response file path using `_get_response_file_path`.
        4. Create a prompt and calculate its hash.
        5. Write the response file with the expected data structure.
        6. Call `load_recorded_response` with the source file, test file, and prompt.
        7. Verify that the returned data matches the expected response, prompt tokens, and completion tokens.

        Assertions:
        - The returned data matches the expected response, prompt tokens, and completion tokens.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")

        # Get the correct file path using the manager's method
        response_file = manager._get_response_file_path("source.py", "test.py")
        response_file.parent.mkdir(parents=True, exist_ok=True)

        # Create prompt and calculate hash
        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        truncated_hash = prompt_hash[:RecordReplayManager.HASH_DISPLAY_LENGTH]

        # Write the response file with the expected data structure
        with open(response_file, "w") as f:
            yaml.safe_dump({
                truncated_hash: {
                    "prompt": {
                        "user": prompt
                    },
                    "response": "response",
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "files_hash": "hash123"
                }
            }, f)

        result = manager.load_recorded_response("source.py", "test.py", prompt)

        assert result == ("response", 10, 20)

    @staticmethod
    def test_load_recorded_response_handles_invalid_yaml_gracefully(tmp_path):
        """
        Test that load_recorded_response handles invalid YAML files gracefully by returning None.

        This test ensures that when the `load_recorded_response` method of the `RecordReplayManager`
        class is called and the response file contains invalid YAML, the method does not raise
        an exception and instead returns None.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Create a response file with invalid YAML content.
        4. Call `load_recorded_response` with valid parameters.
        5. Verify that the method returns None.

        Assertions:
        - The method returns None when the response file contains invalid YAML.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        response_file = tmp_path / "default" / "responses_hash123.yml"
        response_file.parent.mkdir(parents=True, exist_ok=True)
        response_file.write_text("invalid: [unclosed")

        result = manager.load_recorded_response("source.py", "test.py", {"key": "value"})

        assert result is None

    @staticmethod
    def test_record_response_skips_recording_in_replay_mode(tmp_path):
        """
        Test that record_response does not record anything when in replay mode.

        This test ensures that when the `record_response` method of the `RecordReplayManager`
        class is called in replay mode, it does not perform any recording operations.

        Steps:
        1. Initialize a `RecordReplayManager` instance in replay mode with a temporary base directory.
        2. Mock the `_get_response_file_path` and `_calculate_files_hash` methods.
        3. Call `record_response` with arbitrary data.
        4. Verify that the mocked methods are not called.

        Assertions:
        - `_get_response_file_path` is not called.
        - `_calculate_files_hash` is not called.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._get_response_file_path = Mock()
        manager._calculate_files_hash = Mock()

        manager.record_response("source.py", "test.py", {"key": "value"}, "response", 10, 20)

        manager._get_response_file_path.assert_not_called()
        manager._calculate_files_hash.assert_not_called()

    @staticmethod
    def test_record_response_records_new_response_with_valid_data(tmp_path):
        """
        Test that record_response creates a new response file with valid data.

        This test ensures that when the `record_response` method of the `RecordReplayManager`
        class is called in record mode, it creates a new response file containing the
        correct prompt, response, prompt tokens, completion tokens, and file hash.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Call `record_response` with valid data.
        4. Verify that the response file is created and contains the expected data.

        Assertions:
        - The response file exists after the method call.
        - The response file contains the correct prompt, response, prompt tokens, completion tokens, and file hash.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")

        # Get the correct file path using the manager's method
        response_file = manager._get_response_file_path("source.py", "test.py")
        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        truncated_hash = prompt_hash[:RecordReplayManager.HASH_DISPLAY_LENGTH]

        manager.record_response("source.py", "test.py", prompt, "response", 10, 20)

        assert response_file.exists()
        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        assert truncated_hash in data
        assert data[truncated_hash]["prompt"] == prompt
        assert data[truncated_hash]["response"] == "response"
        assert data[truncated_hash]["prompt_tokens"] == 10
        assert data[truncated_hash]["completion_tokens"] == 20
        assert data[truncated_hash]["files_hash"] == "hash123"

    @staticmethod
    def test_record_response_appends_to_existing_response_file(tmp_path):
        """
        Test that record_response appends new data to an existing response file.

        This test ensures that when the `record_response` method of the `RecordReplayManager`
        class is called and the response file already contains data, the method appends
        the new data without overwriting the existing content.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Create a response file with existing data.
        4. Call `record_response` with new data.
        5. Verify that the new data is appended to the existing data in the response file.

        Assertions:
        - The response file contains the existing data after the method call.
        - The response file contains the new data after the method call.
        - The new data includes the correct prompt, response, prompt tokens, completion tokens, and file hash.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash456")

        # Get the correct file path using the manager's method
        response_file = manager._get_response_file_path("source.py", "test.py")
        response_file.parent.mkdir(parents=True, exist_ok=True)
        with open(response_file, "w") as f:
            yaml.safe_dump({"existing_hash": {"response": "old_response"}}, f)

        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        truncated_hash = prompt_hash[:RecordReplayManager.HASH_DISPLAY_LENGTH]

        manager.record_response("source.py", "test.py", prompt, "new_response", 15, 25)

        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        assert "existing_hash" in data
        assert truncated_hash in data
        assert data[truncated_hash]["response"] == "new_response"
        assert data[truncated_hash]["prompt_tokens"] == 15
        assert data[truncated_hash]["completion_tokens"] == 25
        assert data[truncated_hash]["files_hash"] == "hash456"

    @staticmethod
    def test_record_response_handles_invalid_yaml_in_existing_response_file(tmp_path):
        """
        Test that record_response replaces invalid YAML in an existing response file
        with valid data.

        This test ensures that when the `record_response` method of the `RecordReplayManager`
        class is called and the existing response file contains invalid YAML, the method
        replaces the invalid content with valid YAML data.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode with a temporary base directory.
        2. Mock the `_calculate_files_hash` method to return a predefined hash value.
        3. Create a response file with invalid YAML content.
        4. Call `record_response` with valid data.
        5. Verify that the invalid YAML is replaced with valid data in the response file.

        Assertions:
        - The response file contains valid YAML data after the method call.
        - The valid data includes the correct prompt, response, prompt tokens, completion tokens, and file hash.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash789")

        # Get the correct file path using the manager's method
        response_file = manager._get_response_file_path("source.py", "test.py")
        response_file.parent.mkdir(parents=True, exist_ok=True)
        response_file.write_text("invalid: [unclosed")

        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        truncated_hash = prompt_hash[:RecordReplayManager.HASH_DISPLAY_LENGTH]

        manager.record_response("source.py", "test.py", prompt, "response", 10, 20)

        # The manager should have written valid YAML data
        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        # Check that the invalid YAML was replaced with valid data
        assert isinstance(data, dict)
        assert truncated_hash in data
        assert data[truncated_hash]["response"] == "response"
        assert data[truncated_hash]["prompt"] == prompt
        assert data[truncated_hash]["prompt_tokens"] == 10
        assert data[truncated_hash]["completion_tokens"] == 20
        assert data[truncated_hash]["files_hash"] == "hash789"

    @staticmethod
    def test_calculate_files_hash_calculates_hash_for_valid_files(tmp_path):
        """
        Test that _calculate_files_hash correctly calculates a hash for valid files.

        This test ensures that when valid source and test files are provided to the
        `_calculate_files_hash` method of the `RecordReplayManager` class, the method
        generates a valid hash string.

        Steps:
        1. Create a source file and a test file with valid content in the temporary directory.
        2. Call `_calculate_files_hash` with the paths of the source and test files.
        3. Verify that the returned hash is a 64-character alphanumeric string.

        Assertions:
        - The length of the generated hash is 64 characters.
        - The generated hash is a string.
        - The generated hash contains only alphanumeric characters.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True)
        source_file = tmp_path / "source.py"
        test_file = tmp_path / "test.py"
        source_file.write_text("def source(): pass")
        test_file.write_text("def test(): pass")

        result = manager._calculate_files_hash(str(source_file), str(test_file))

        assert len(result) == 64
        assert isinstance(result, str)
        assert result.isalnum()

    @staticmethod
    def test_calculate_files_hash_reuses_cached_hash_if_available(tmp_path):
        """
        Test that _calculate_files_hash reuses a cached hash if it is available.

        This test ensures that when the `files_hash` attribute of the `RecordReplayManager`
        class is already set, the `_calculate_files_hash` method returns the cached hash
        value instead of recalculating it.

        Steps:
        1. Initialize a `RecordReplayManager` instance in record mode.
        2. Set the `files_hash` attribute to a predefined cached hash value.
        3. Call `_calculate_files_hash` with arbitrary file paths.
        4. Verify that the returned hash matches the cached hash value.

        Assertions:
        - The returned hash is equal to the cached hash value.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True)
        manager.files_hash = "cachedhash123"

        result = manager._calculate_files_hash("source.py", "test.py")

        assert result == "cachedhash123"

    @staticmethod
    def test_calculate_files_hash_raises_error_for_missing_source_file(tmp_path):
        """
        Test that _calculate_files_hash raises a FileNotFoundError if the source file
        is missing.

        This test ensures that when the `_calculate_files_hash` method of the
        `RecordReplayManager` class is called with a missing source file, it raises
        a `FileNotFoundError`.

        Steps:
        1. Create a test file with valid content in the temporary directory.
        2. Define a source file path that does not exist.
        3. Call `_calculate_files_hash` with the missing source file and the test file.
        4. Verify that a `FileNotFoundError` is raised.

        Assertions:
        - A `FileNotFoundError` is raised when the source file is missing.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True)
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")
        source_file = tmp_path / "missing_source.py"

        with pytest.raises(FileNotFoundError):
            manager._calculate_files_hash(str(source_file), str(test_file))

    @staticmethod
    def test_calculate_files_hash_raises_error_for_missing_test_file(tmp_path):
        """
        Test that _calculate_files_hash raises a FileNotFoundError if the test file
        is missing.

        This test ensures that when the `_calculate_files_hash` method of the
        `RecordReplayManager` class is called with a missing test file, it raises
        a `FileNotFoundError`.

        Steps:
        1. Create a source file with valid content in the temporary directory.
        2. Define a test file path that does not exist.
        3. Call `_calculate_files_hash` with the source file and the missing test file.
        4. Verify that a `FileNotFoundError` is raised.

        Assertions:
        - A `FileNotFoundError` is raised when the test file is missing.

        Parameters:
        - tmp_path (Path): A pytest fixture providing a temporary directory for the test.
        """
        manager = RecordReplayManager(record_mode=True)
        source_file = tmp_path / "source.py"
        source_file.write_text("def source(): pass")
        test_file = tmp_path / "missing_test.py"

        with pytest.raises(FileNotFoundError):
            manager._calculate_files_hash(str(source_file), str(test_file))

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
