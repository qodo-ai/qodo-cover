import os

import pytest

from cover_agent.unit_test_db import UnitTestDB, UnitTestGenerationAttempt, dump_to_report, dump_to_report_cli


DB_NAME = "unit_test_runs.db"
DATABASE_URL = f"sqlite:///{DB_NAME}"


@pytest.fixture(scope="class")
def unit_test_db():
    """
    Fixture to set up and tear down the UnitTestDB instance for testing.
    Creates an empty database file before tests and removes it after tests.
    """
    # Create an empty DB file for testing
    with open(DB_NAME, "w"):
        pass

    db = UnitTestDB(DATABASE_URL)
    yield db

    # Cleanup after tests
    db.engine.dispose()

    # Delete the db file
    os.remove(DB_NAME)


@pytest.mark.usefixtures("unit_test_db")
class TestUnitTestDB:
    """
    Test class for UnitTestDB functionalities.
    """

    def test_insert_attempt(self, unit_test_db):
        """
        Test the insert_attempt method of UnitTestDB.
        Verifies that the attempt is correctly inserted into the database.
        """
        test_result = {
            "status": "success",
            "reason": "",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest",
            },
            "language": "python",
            "source_file": "sample source code",
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        # Insert the test result into the database
        attempt_id = unit_test_db.insert_attempt(test_result)
        with unit_test_db.Session() as session:
            attempt = session.query(UnitTestGenerationAttempt).filter_by(id=attempt_id).one()

        # Assertions to verify the inserted attempt
        assert attempt.id == attempt_id
        assert attempt.status == "success"
        assert attempt.reason == ""
        assert attempt.exit_code == 0
        assert attempt.stderr == ""
        assert attempt.stdout == "Test passed"
        assert attempt.test_code == "def test_example(): pass"
        assert attempt.imports == "import pytest"
        assert attempt.language == "python"
        assert attempt.source_file == "sample source code"
        assert attempt.original_test_file == "sample test code"
        assert attempt.processed_test_file == "sample new test code"

    def test_dump_to_report(self, unit_test_db, tmp_path):
        """
        Test the dump_to_report method of UnitTestDB.
        Verifies that the report is generated and contains the correct content.
        """
        test_result = {
            "status": "success",
            "reason": "Test passed successfully",
            "exit_code": 0,
            "stderr": "",
            "stdout": "Test passed",
            "test": {
                "test_code": "def test_example(): pass",
                "new_imports_code": "import pytest",
            },
            "language": "python",
            "source_file": "sample source code",
            "original_test_file": "sample test code",
            "processed_test_file": "sample new test code",
        }

        # Insert the test result into the database
        unit_test_db.insert_attempt(test_result)

        # Generate the report and save it to a temporary file
        report_filepath = tmp_path / "unit_test_report.html"
        unit_test_db.dump_to_report(str(report_filepath))

        # Check if the report was generated successfully
        assert os.path.exists(report_filepath)

        # Verify the report content
        with open(report_filepath, "r") as file:
            content = file.read()

        assert "sample test code" in content
        assert "sample new test code" in content
        assert "def test_example(): pass" in content

    def test_dump_to_report_cli_custom_args(self, unit_test_db, tmp_path, monkeypatch):
        """
        Test the dump_to_report_cli function with custom command-line arguments.
        Verifies that the report is generated at the specified location.
        """
        custom_db_path = str(tmp_path / "cli_custom_unit_test_runs.db")
        custom_report_filepath = str(tmp_path / "cli_custom_report.html")
        monkeypatch.setattr(
            "sys.argv",
            [
                "prog",
                "--path-to-db",
                custom_db_path,
                "--report-filepath",
                custom_report_filepath,
            ],
        )
        dump_to_report_cli()
        assert os.path.exists(custom_report_filepath)

    def test_dump_to_report_defaults(self, unit_test_db, tmp_path):
        """
        Test the dump_to_report function with default arguments.
        Verifies that the report is generated at the default location.
        """
        report_filepath = tmp_path / "default_report.html"
        dump_to_report(report_filepath=str(report_filepath))
        assert os.path.exists(report_filepath)
