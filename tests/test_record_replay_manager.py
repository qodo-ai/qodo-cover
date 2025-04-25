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
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))

        result = manager.load_recorded_response("source.py", "test.py", {"key": "value"})

        assert result is None

    @staticmethod
    def test_load_recorded_response_returns_none_if_file_does_not_exist(tmp_path):
        """
        Test that load_recorded_response returns None if the response file does not exist.
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
        """
        manager = RecordReplayManager(record_mode=False, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        response_file = tmp_path / "default" / "responses_hash123.yml"
        response_file.parent.mkdir(parents=True, exist_ok=True)
        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        with open(response_file, "w") as f:
            yaml.safe_dump({
                prompt_hash: {
                    "response": "response",
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                }
            }, f)

        result = manager.load_recorded_response("source.py", "test.py", prompt)

        assert result == ("response", 10, 20)

    @staticmethod
    def test_load_recorded_response_handles_invalid_yaml_gracefully(tmp_path):
        """
        Test that load_recorded_response handles invalid YAML files gracefully
        by returning None.
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
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        response_file = tmp_path / "default" / "responses_hash123.yml"
        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()

        manager.record_response("source.py", "test.py", prompt, "response", 10, 20)

        assert response_file.exists()
        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        assert prompt_hash in data
        assert data[prompt_hash]["response"] == "response"
        assert data[prompt_hash]["prompt_tokens"] == 10
        assert data[prompt_hash]["completion_tokens"] == 20

    @staticmethod
    def test_record_response_appends_to_existing_response_file(tmp_path):
        """
        Test that record_response appends new data to an existing response file.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash456")
        response_file = tmp_path / "default" / "responses_hash456.yml"
        response_file.parent.mkdir(parents=True, exist_ok=True)
        with open(response_file, "w") as f:
            yaml.safe_dump({"existing_hash": {"response": "old_response"}}, f)

        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        manager.record_response("source.py", "test.py", prompt, "new_response", 15, 25)

        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        assert "existing_hash" in data
        assert prompt_hash in data
        assert data[prompt_hash]["response"] == "new_response"

    @staticmethod
    def test_record_response_handles_invalid_yaml_in_existing_response_file(tmp_path):
        """
        Test that record_response replaces invalid YAML in an existing response file
        with valid data.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash789")
        response_file = tmp_path / "default" / "responses_hash789.yml"
        response_file.parent.mkdir(parents=True, exist_ok=True)
        response_file.write_text("invalid: [unclosed")

        prompt = {"key": "value"}
        prompt_hash = hashlib.sha256(str(prompt).encode()).hexdigest()
        manager.record_response("source.py", "test.py", prompt, "response", 10, 20)

        with open(response_file, "r") as f:
            data = yaml.safe_load(f)

        # Check that the invalid YAML was replaced with valid data
        assert isinstance(data, dict)
        assert prompt_hash in data
        assert data[prompt_hash]["response"] == "response"
        assert data[prompt_hash]["prompt_tokens"] == 10
        assert data[prompt_hash]["completion_tokens"] == 20
        assert data[prompt_hash]["files_hash"] == "hash789"

    @staticmethod
    def test_calculate_files_hash_calculates_hash_for_valid_files(tmp_path):
        """
        Test that _calculate_files_hash correctly calculates a hash for valid files.
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
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash123")
        result = manager._get_response_file_path("nested/folder/source_file.py", "tests/test_file.py")

        assert result == tmp_path / "folder" / "responses_hash123.yml"
        assert (tmp_path / "folder").exists()

    @staticmethod
    def test_get_response_file_path_with_empty_source_path(tmp_path):
        """
        Test that _get_response_file_path returns the correct path when the source
        path is empty.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash456")
        result = manager._get_response_file_path("", "tests/test_file.py")

        assert result == tmp_path / "default" / "responses_hash456.yml"
        assert (tmp_path / "default").exists()

    @staticmethod
    def test_get_response_file_path_create_response_directory_if_not_exists(tmp_path):
        """
        Test that _get_response_file_path creates the response directory if it does
        not already exist.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash789")
        result = manager._get_response_file_path("new_folder/source_file.py", "tests/test_file.py")

        assert result == tmp_path / "new_folder" / "responses_hash789.yml"
        assert (tmp_path / "new_folder").exists()

    @staticmethod
    def test_get_response_file_path_handle_source_path_with_no_parent_directory(tmp_path):
        """
        Test that _get_response_file_path handles a source path with no parent
        directory correctly.
        """
        manager = RecordReplayManager(record_mode=True, base_dir=str(tmp_path))
        manager._calculate_files_hash = Mock(return_value="hash000")
        result = manager._get_response_file_path("source_file.py", "tests/test_file.py")

        assert result == tmp_path / "default" / "responses_hash000.yml"
        assert (tmp_path / "default").exists()
