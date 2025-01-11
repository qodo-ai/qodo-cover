import pytest
import json
import xml.etree.ElementTree as ET
from cover_agent.coverage.processor import (
    CoverageProcessor,
    CoverageProcessorFactory,
    JacocoProcessor,
    CoberturaProcessor,
    LcovProcessor,
    CoverageData,
    CoverageReport,
    CoverageReportFilter,
    DiffCoverageProcessor
)
from unittest.mock import patch, MagicMock

class TestCoverageProcessorFactory:
    def test_create_processor_returns_correct_instance(self):
        processor = CoverageProcessorFactory.create_processor(
            tool_type='cobertura',
            report_path='dummy_path.xml',
            src_file_path='dummy_src.java'
        )
        assert isinstance(processor, CoberturaProcessor)

        processor = CoverageProcessorFactory.create_processor(
            tool_type='jacoco',
            report_path='dummy_path.xml',
            src_file_path='dummy_src.java'
        )
        assert isinstance(processor, JacocoProcessor)

        processor = CoverageProcessorFactory.create_processor(
            tool_type='lcov',
            report_path='dummy_path.info',
            src_file_path='dummy_src.java'
        )
        assert isinstance(processor, LcovProcessor)

        processor = CoverageProcessorFactory.create_processor(
            tool_type='diff_cover_json',
            report_path='dummy_path.json',
            src_file_path='dummy_src.java',
            diff_coverage_report_path='dummy_diff.json'
        )
        assert isinstance(processor, DiffCoverageProcessor)

class TestCoverageProcessor:
    @patch('os.path.exists', return_value=False)
    def test_process_coverage_report_file_not_found(self, mock_exists):
        processor = CoberturaProcessor('non_existent_file.xml', 'dummy_src.java')
        with pytest.raises(FileNotFoundError):
            processor.process_coverage_report(time_of_test_command=1234567890)

class TestCoverageReportFilter:
    def test_filter_report_with_file_pattern(self):
        coverage_data = {
            'file1.java': CoverageData([1, 2, 3], 3, [4, 5], 2, 0.6),
            'file2.java': CoverageData([1, 2], 2, [3, 4, 5], 3, 0.4),
            'test_file.java': CoverageData([1], 1, [2, 3, 4, 5], 4, 0.2)
        }
        report = CoverageReport(total_coverage=0.5, file_coverage=coverage_data)
        filter = CoverageReportFilter()
        filtered_report = filter.filter_report(report, 'test_file')

        assert len(filtered_report.file_coverage) == 1
        assert 'test_file.java' in filtered_report.file_coverage
        assert filtered_report.total_coverage == 0.2

@pytest.fixture
def mock_xml_tree(monkeypatch):
    """
    Creates a mock function to simulate the ET.parse method, returning a mocked XML tree structure.
    """
    def mock_parse(file_path):
        # Mock XML structure for the test
        xml_str = """<coverage>
                        <packages>
                            <package>
                                <classes>
                                    <class filename="app.py">
                                        <lines>
                                            <line number="1" hits="1"/>
                                            <line number="2" hits="0"/>
                                        </lines>
                                    </class>
                                    <class filename="app.py">
                                        <lines>
                                            <line number="3" hits="1"/>
                                            <line number="4" hits="0"/>
                                        </lines>
                                    </class>
                                </classes>
                            </package>
                        </packages>
                     </coverage>"""
        root = ET.ElementTree(ET.fromstring(xml_str))
        return root

    monkeypatch.setattr(ET, "parse", mock_parse)

class TestCoverageProcessorFactory:
    def test_create_processor_cobertura(self):
        processor = CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")
        assert isinstance(processor, CoberturaProcessor), "Expected CoberturaProcessor instance"

    def test_create_processor_jacoco(self):
        processor = CoverageProcessorFactory.create_processor("jacoco", "fake_path", "app.py")
        assert isinstance(processor, JacocoProcessor), "Expected JacocoProcessor instance"

    def test_create_processor_lcov(self):
        processor = CoverageProcessorFactory.create_processor("lcov", "fake_path", "app.py")
        assert isinstance(processor, LcovProcessor), "Expected LcovProcessor instance"

    def test_create_processor_unsupported_type(self):
        with pytest.raises(ValueError, match="Invalid coverage type specified: unsupported_type"):
            CoverageProcessorFactory.create_processor("unsupported_type", "fake_path", "app.py")

class TestCoverageProcessor:
    def test_is_report_obsolete(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.getmtime", return_value=1234567.0)
        processor = CoverageProcessorFactory.create_processor(
             "cobertura", "fake_path", "app.py"
        )
        with pytest.raises(
            ValueError,
            match="Coverage report is outdated",
        ):
            processor._is_coverage_valid(1234567890)

    def test_is_report_exist(self, mocker):
        mocker.patch("os.path.exists", return_value=False)

        processor = CoverageProcessorFactory.create_processor(
             "cobertura", "fake_path", "app.py"
        )
        with pytest.raises(
            FileNotFoundError,
            match='Coverage report "fake_path" not found',
        ):
            processor._is_coverage_valid(1234567890)

    # Process valid coverage data and calculate correct total coverage percentage
    def test_process_valid_coverage_data(self, mocker):
        # Arrange
        time_of_test = 123456
        coverage_data = {
            "file1.py": CoverageData(covered_lines=[], covered=80, missed_lines=[], missed=20, coverage=0.8),
            "file2.py": CoverageData(covered_lines=[], covered=60, missed_lines=[], missed=40, coverage=0.6)
        }

        processor = CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")
        mocker.patch.object(processor, '_is_coverage_valid')
        mocker.patch.object(processor, 'parse_coverage_report', return_value=coverage_data)

        # Act
        report = processor.process_coverage_report(time_of_test)

        # Assert
        assert report.total_coverage == 0.7  # (140 covered)/(200 total) = 0.7
        assert report.file_coverage == coverage_data
        processor._is_coverage_valid.assert_called_once_with(time_of_test_command=time_of_test)

    # Handle coverage data with zero total lines
    def test_process_zero_lines_coverage(self, mocker):
        # Arrange
        time_of_test = 123456
        coverage_data = {
            "file1.py": CoverageData(covered_lines=[], covered=0, missed_lines=[], missed=0, coverage=0.0),
            "file2.py": CoverageData(covered_lines=[], covered=0, missed_lines=[], missed=0, coverage=0.0)
        }

        processor = CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")
        mocker.patch.object(processor, '_is_coverage_valid')
        mocker.patch.object(processor, 'parse_coverage_report', return_value=coverage_data)

        # Act
        report = processor.process_coverage_report(time_of_test)

        # Assert
        assert report.total_coverage == 0.0
        assert report.file_coverage == coverage_data
        processor._is_coverage_valid.assert_called_once_with(time_of_test_command=time_of_test)

class TestCoberturaProcessor:
    @pytest.fixture
    def processor(self):
        # Initializes CoberturaProcessor with cobertura coverage type for each test
        return CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")

    def test_parse_coverage_report_cobertura(self, mock_xml_tree, processor):
        """
        Tests the parse_coverage_report method for correct line number and coverage calculation with Cobertura reports.
        """
        coverage = processor.parse_coverage_report()
        assert len(coverage) == 1, "Expected coverage data for one file"
        assert coverage["app.py"].covered_lines == [1, 3], "Should list lines 1 and 3 as covered"
        assert coverage["app.py"].covered == 2, "Should have 2 line as covered"
        assert coverage["app.py"].missed_lines == [2, 4], "Should list lines 2 and 4 as missed"
        assert coverage["app.py"].missed == 2, "Should have 2 line as missed"
        assert coverage["app.py"].coverage == 0.5, "Coverage should be 50 percent"

class TestLcovProcessor:
    # Parse LCOV file with single source file containing covered and uncovered lines
    def test_parse_lcov_file_with_covered_and_uncovered_lines(self, tmp_path):
        # Arrange
        lcov_content = """SF:src/file1.py
        DA:1,1
        DA:2,0
        DA:3,1
        end_of_record"""
        lcov_file = tmp_path / "coverage.lcov"
        lcov_file.write_text(lcov_content)

        processor = LcovProcessor(str(lcov_file), "src/file1.py")

        # Act
        result = processor.parse_coverage_report()

        # Assert
        assert len(result) == 1
        assert "src/file1.py" in result
        coverage_data = result["src/file1.py"]
        assert coverage_data.covered_lines == [1, 3]
        assert coverage_data.missed_lines == [2]
        assert coverage_data.covered == 2
        assert coverage_data.missed == 1
        assert coverage_data.coverage == 2/3

    # Handle malformed LCOV file with missing end_of_record
    def test_parse_malformed_lcov_missing_end_record(self, tmp_path):
        # Arrange
        lcov_content = """SF:src/file1.py
        DA:1,1
        DA:2,0
        DA:3,1"""
        lcov_file = tmp_path / "coverage.lcov"
        lcov_file.write_text(lcov_content)

        processor = LcovProcessor(str(lcov_file), "src/file1.py")

        # Act
        result = processor.parse_coverage_report()

        # Assert
        assert len(result) == 1
        assert "src/file1.py" in result
        coverage_data = result["src/file1.py"]
        assert coverage_data.covered_lines == [1, 3]
        assert coverage_data.missed_lines == [2]
        assert coverage_data.covered == 2
        assert coverage_data.missed == 1
        assert coverage_data.coverage == 2/3

class TestJacocoProcessor:
    # Successfully parse XML JaCoCo report and extract coverage data
    def test_parse_xml_coverage_report_success(self, mocker):
        # Arrange
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <report>
            <package name="com.example">
                <sourcefile name="MyClass.java">
                    <counter type="LINE" missed="5" covered="15"/>
                </sourcefile>
            </package>
        </report>'''

        mock_file = mocker.mock_open(read_data='package com.example;\npublic class MyClass {')
        mocker.patch('builtins.open', mock_file)
        mocker.patch('xml.etree.ElementTree.parse', return_value=ET.ElementTree(ET.fromstring(xml_content)))

        processor = JacocoProcessor('coverage.xml', 'MyClass.java')

        # Act
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert len(coverage_data) == 1
        assert 'MyClass' in coverage_data
        # should not include <counter type="LINE" missed="5" covered="15"/>
        assert coverage_data['MyClass'].missed == 0
        assert coverage_data['MyClass'].covered == 0
        assert coverage_data['MyClass'].coverage == 0

    # Handle empty or malformed XML/CSV coverage reports
    def test_parse_empty_xml_coverage_report(self, mocker):
        # Arrange
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <report>
            <package name="com.example">
            </package>
        </report>'''

        mock_file = mocker.mock_open(read_data='package com.example;\npublic class MyClass {')
        mocker.patch('builtins.open', mock_file)
        mocker.patch('xml.etree.ElementTree.parse', return_value=ET.ElementTree(ET.fromstring(xml_content)))

        processor = JacocoProcessor('coverage.xml', 'MyClass.java')

        # Act
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert len(coverage_data) == 1
        assert 'MyClass' in coverage_data
        assert coverage_data['MyClass'].missed == 0
        assert coverage_data['MyClass'].covered == 0
        assert coverage_data['MyClass'].coverage == 0.0

    def test_returns_empty_lists_and_float(self, mocker):
        # Mocking the necessary methods
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._parse_jacoco_xml",
            return_value=([], []),
        )

        # Initialize the CoverageProcessor object
        coverage_processor = JacocoProcessor(
            file_path="path/to/coverage.xml",
            src_file_path="path/to/example.java",
        )

        # Invoke the parse_coverage_report_jacoco method
        coverageData = coverage_processor.parse_coverage_report()

        # Assert the results
        assert coverageData["Example"].covered_lines == [], "Expected covered_lines to be an empty list"
        assert coverageData["Example"].missed_lines == [], "Expected missed_lines to be an empty list"
        assert coverageData["Example"].coverage == 0, "Expected coverage percentage to be 0"

    def test_parse_missed_covered_lines_jacoco_xml_no_source_file(self, mocker):
        #, mock_xml_tree
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._extract_package_and_class_java",
            return_value=("com.example", "MyClass"),
        )
        xml_str = """<?xml version="1.0" encoding="UTF-8"?>
                        <report>
                            <package name="path/to">
                                <sourcefile name="MyClass.java">
                                    <line nr="35" mi="0" ci="9" mb="0" cb="0"/>
                                    <line nr="36" mi="0" ci="1" mb="0" cb="0"/>
                                    <line nr="37" mi="0" ci="3" mb="0" cb="0"/>
                                    <line nr="38" mi="0" ci="9" mb="0" cb="0"/>
                                    <line nr="39" mi="1" ci="0" mb="0" cb="0"/>
                                    <line nr="40" mi="5" ci="0" mb="0" cb="0"/>
                                    <line nr="41" mi="9" ci="0" mb="0" cb="0"/>
                                    <counter type="INSTRUCTION" missed="53" covered="387"/>
                                    <counter type="BRANCH" missed="2" covered="6"/>
                                    <counter type="LINE" missed="9" covered="94"/>
                                    <counter type="COMPLEXITY" missed="5" covered="23"/>
                                    <counter type="METHOD" missed="3" covered="21"/>
                                    <counter type="CLASS" missed="0" covered="1"/>
                                </sourcefile>
                            </package>
                        </report>"""
        mocker.patch(
            "xml.etree.ElementTree.parse",
            return_value=ET.ElementTree(ET.fromstring(xml_str))
        )
        processor = JacocoProcessor("path/to/coverage_report.xml", "path/to/MySecondClass.java")

        # Action
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert 'MySecondClass' not in coverage_data

    def test_parse_missed_covered_lines_jacoco_xml(self, mocker):
        #, mock_xml_tree
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._extract_package_and_class_java",
            return_value=("com.example", "MyClass"),
        )
        xml_str = """<report>
                        <package name="path/to">
                            <sourcefile name="MyClass.java">
                                <line nr="35" mi="0" ci="9" mb="0" cb="0"/>
                                <line nr="36" mi="0" ci="1" mb="0" cb="0"/>
                                <line nr="37" mi="0" ci="3" mb="0" cb="0"/>
                                <line nr="38" mi="0" ci="9" mb="0" cb="0"/>
                                <line nr="39" mi="1" ci="0" mb="0" cb="0"/>
                                <line nr="40" mi="5" ci="0" mb="0" cb="0"/>
                                <line nr="41" mi="9" ci="0" mb="0" cb="0"/>
                                <counter type="INSTRUCTION" missed="53" covered="387"/>
                                <counter type="BRANCH" missed="2" covered="6"/>
                                <counter type="LINE" missed="9" covered="94"/>
                                <counter type="COMPLEXITY" missed="5" covered="23"/>
                                <counter type="METHOD" missed="3" covered="21"/>
                                <counter type="CLASS" missed="0" covered="1"/>
                            </sourcefile>
                        </package>
                    </report>"""
        mocker.patch(
            "xml.etree.ElementTree.parse",
            return_value=ET.ElementTree(ET.fromstring(xml_str))
        )
        processor = JacocoProcessor("path/to/coverage_report.xml", "path/to/MyClass.java")

        # Action
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert "MyClass" in coverage_data
        assert coverage_data["MyClass"].missed_lines == [39, 40, 41]
        assert coverage_data["MyClass"].covered_lines == [35, 36, 37, 38]

    def test_parse_missed_covered_lines_kotlin_jacoco_xml(self, mocker):
        #, mock_xml_tree
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._extract_package_and_class_kotlin",
            return_value=("com.example", "MyClass"),
        )
        xml_str = """<report>
                        <package name="path/to">
                            <sourcefile name="MyClass.kt">
                                <line nr="35" mi="0" ci="9" mb="0" cb="0"/>
                                <line nr="36" mi="0" ci="1" mb="0" cb="0"/>
                                <line nr="37" mi="0" ci="3" mb="0" cb="0"/>
                                <line nr="38" mi="0" ci="9" mb="0" cb="0"/>
                                <line nr="39" mi="1" ci="0" mb="0" cb="0"/>
                                <line nr="40" mi="5" ci="0" mb="0" cb="0"/>
                                <line nr="41" mi="9" ci="0" mb="0" cb="0"/>
                                <counter type="INSTRUCTION" missed="53" covered="387"/>
                                <counter type="BRANCH" missed="2" covered="6"/>
                                <counter type="LINE" missed="9" covered="94"/>
                                <counter type="COMPLEXITY" missed="5" covered="23"/>
                                <counter type="METHOD" missed="3" covered="21"/>
                                <counter type="CLASS" missed="0" covered="1"/>
                            </sourcefile>
                        </package>
                    </report>"""
        mocker.patch(
            "xml.etree.ElementTree.parse",
            return_value=ET.ElementTree(ET.fromstring(xml_str))
        )
        processor = JacocoProcessor("path/to/coverage_report.xml", "path/to/MyClass.kt")

        # Action
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert "MyClass" in coverage_data
        assert coverage_data["MyClass"].missed_lines == [39, 40, 41]
        assert coverage_data["MyClass"].covered_lines == [35, 36, 37, 38]

class TestDiffCoverageProcessor:
    # Successfully parse JSON diff coverage report and extract coverage data for matching file path
    def test_parse_coverage_report_with_matching_file(self, mocker):
        # Arrange
        test_file_path = "test/file.py"
        test_src_path = "src/test/file.py"
        test_diff_report = "diff_coverage.json"

        mock_json_data = {
            "src_stats": {
                "src/test/file.py": {
                    "covered_lines": [1, 2, 3],
                    "violation_lines": [4, 5],
                    "percent_covered": 60.0
                }
            }
        }

        mock_open = mocker.mock_open(read_data=json.dumps(mock_json_data))
        mocker.patch("builtins.open", mock_open)

        processor = DiffCoverageProcessor(
            diff_coverage_report_path=test_diff_report,
            file_path=test_file_path,
            src_file_path=test_src_path
        )

        # Act
        result = processor.parse_coverage_report()

        # Assert
        assert test_file_path in result
        coverage_data = result[test_file_path]
        assert coverage_data.covered_lines == [1, 2, 3]
        assert coverage_data.missed_lines == [4, 5]
        assert coverage_data.covered == 3
        assert coverage_data.missed == 2
        assert coverage_data.coverage == 0.6

    # Handle case when file is not found in coverage report
    def test_parse_coverage_report_with_no_matching_file(self, mocker):
        # Arrange
        test_file_path = "test/file.py"
        test_src_path = "src/test/file.py"
        test_diff_report = "diff_coverage.json"
    
        mock_json_data = {
            "src_stats": {
                "src/other/file.py": {
                    "covered_lines": [1, 2],
                    "violation_lines": [3],
                    "percent_covered": 66.7
                }
            }
        }

        mock_open = mocker.mock_open(read_data=json.dumps(mock_json_data))
        mocker.patch("builtins.open", mock_open)

        processor = DiffCoverageProcessor(
            diff_coverage_report_path=test_diff_report,
            file_path=test_file_path,
            src_file_path=test_src_path
        )

        # Act
        result = processor.parse_coverage_report()

        # Assert
        assert test_file_path in result
        coverage_data = result[test_file_path]
        assert coverage_data.covered_lines == []
        assert coverage_data.missed_lines == []
        assert coverage_data.covered == 0
        assert coverage_data.missed == 0
        assert coverage_data.coverage == 0.0