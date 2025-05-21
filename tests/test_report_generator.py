import pytest

from cover_agent.report_generator import ReportGenerator


class TestReportGeneration:
    """
    Test suite for the ReportGenerator class.
    This class contains tests to validate the functionality of the report generation.
    """

    @pytest.fixture
    def sample_results(self):
        """
        Fixture providing sample data mimicking the structure expected by the ReportGenerator.
        """
        return [
            {
                "status": "pass",
                "reason": "All tests passed",
                "exit_code": 0,
                "stderr": "",
                "stdout": "test session starts platform linux -- Python 3.10.12, pytest-7.0.1",
                "test_code": "def test_current_date():\n    response = client.get('/current-date')\n    assert response.status_code == 200\n    assert 'date' in response.json()",
                "imports": "import requests",
                "language": "python",
                "source_file": "app.py",
                "original_test_file": "test_app.py",
                "processed_test_file": "new_test_app.py",
            },
            # Add more sample results if needed
        ]

    @pytest.fixture
    def expected_output(self):
        """
        Fixture providing simplified expected output for validation.
        """
        expected_start = "<!DOCTYPE html>"
        expected_table_header = "<th>Status</th>"
        expected_row_content = "test_current_date"
        expected_end = "</html>"
        return expected_start, expected_table_header, expected_row_content, expected_end

    def test_generate_report(self, sample_results, expected_output, tmp_path):
        """
        Test the generate_report method of ReportGenerator.

        This test verifies that the generated HTML report contains key parts of the expected output.
        """
        # Temporary path for generating the report
        report_path = tmp_path / "test_report.html"
        ReportGenerator.generate_report(sample_results, str(report_path))

        # Read the generated report content
        with open(report_path, "r") as file:
            content = file.read()

        # Verify that key parts of the expected HTML output are present in the report
        assert expected_output[0] in content  # Check if the start of the HTML is correct
        assert expected_output[1] in content  # Check if the table header includes "Status"
        assert expected_output[2] in content  # Check if the row includes "test_current_date"
        assert expected_output[3] in content  # Check if the HTML closes properly

    def test_generate_partial_diff_basic(self):
        """
        Test the generate_partial_diff method of ReportGenerator.

        This test verifies that the generated diff output correctly highlights added, removed, and unchanged lines.
        """
        original = "line1\nline2\nline3"
        processed = "line1\nline2 modified\nline3\nline4"
        diff_output = ReportGenerator.generate_partial_diff(original, processed)

        # Verify that the diff output contains the expected changes
        assert '<span class="diff-added">+line2 modified</span>' in diff_output
        assert '<span class="diff-added">+line4</span>' in diff_output
        assert '<span class="diff-removed">-line2</span>' in diff_output
        assert '<span class="diff-unchanged"> line1</span>' in diff_output

        # Additional validation can be added based on specific content if required
