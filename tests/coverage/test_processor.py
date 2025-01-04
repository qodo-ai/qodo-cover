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
            'file1.java': CoverageData(True, [1, 2, 3], 3, [4, 5], 2, 0.6),
            'file2.java': CoverageData(False, [1, 2], 2, [3, 4, 5], 3, 0.4),
            'test_file.java': CoverageData(False, [1], 1, [2, 3, 4, 5], 4, 0.2)
        }
        report = CoverageReport(total_coverage=0.5, file_coverage=coverage_data)
        filtered_report = report.filter_to_target_coverage()

        assert len(filtered_report.file_coverage) == 1
        assert 'file1.java' in filtered_report.file_coverage
        assert filtered_report.total_coverage == 0.6

@pytest.fixture
def mock_xml_tree(monkeypatch):
    """
    Creates a mock function to simulate the ET.parse method, returning a mocked XML tree structure.
    """
    def mock_parse(file_path):
        # Mock XML structure for the test
        xml_str = """<coverage>
                        <packages>
                            <package name=".">
                                <classes>
                                    <class name="app.py" filename="app.py">
                                        <lines>
                                            <line number="1" hits="1"/>
                                            <line number="2" hits="0"/>
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
        with pytest.raises(ValueError, match="Unsupported tool type: unsupported_type"):
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
            "file1.py": CoverageData(is_target_file=False, covered_lines=[], covered=80, missed_lines=[], missed=20, coverage=0.8),
            "file2.py": CoverageData(is_target_file=False, covered_lines=[], covered=60, missed_lines=[], missed=40, coverage=0.6)
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
            "file1.py": CoverageData(is_target_file=False, covered_lines=[], covered=0, missed_lines=[], missed=0, coverage=0.0),
            "file2.py": CoverageData(is_target_file=False, covered_lines=[], covered=0, missed_lines=[], missed=0, coverage=0.0)
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
        print(coverage)
        assert len(coverage) == 1, "Expected coverage data for one file"
        assert coverage["default.app.py"].covered_lines == [1], "Should list line 1 as covered"
        assert coverage["default.app.py"].covered == 1, "Should have 1 line as covered"
        assert coverage["default.app.py"].missed_lines == [2], "Should list line 2 as missed"
        assert coverage["default.app.py"].missed == 1, "Should have 1 line as missed"
        assert coverage["default.app.py"].coverage == 0.5, "Coverage should be 50 percent"
        assert coverage["default.app.py"].is_target_file == True, "Should be a target file"

    def test_parse_non_target_coverage(self, mocker):
        # Arrange
        xml_content = '''
        <coverage>
            <packages>
                <package name=".">
                    <classes>
                        <class name="other.py" filename="other.py">
                            <lines>
                                <line number="1" hits="1"/>
                                <line number="2" hits="0"/>
                            </lines>
                        </class>
                    </classes>
                </package>
            </packages>
        </coverage>
        '''
        mock_file = mocker.mock_open(read_data='class Other:')
        mocker.patch('builtins.open', mock_file)
        mocker.patch('xml.etree.ElementTree.parse', return_value=ET.ElementTree(ET.fromstring(xml_content)))
        processor = CoberturaProcessor('coverage.xml', 'app.py')

        # Act
        coverage_data = processor.parse_coverage_report()
        print(coverage_data)

        # Assert
        assert len(coverage_data) == 1
        assert 'default.other.py' in coverage_data
        assert coverage_data['default.other.py'].missed == 1
        assert coverage_data['default.other.py'].missed_lines == [2]
        assert coverage_data['default.other.py'].covered == 1
        assert coverage_data['default.other.py'].covered_lines == [1]
        assert coverage_data['default.other.py'].coverage == 0.5
        assert coverage_data['default.other.py'].is_target_file == False

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
        assert coverage_data.is_target_file == True

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

    # Parse LCOV file with multiple source file containing covered and uncovered lines
    def test_parse_lcov_file_with_multiple_covered_and_uncovered_lines(self, tmp_path):
        # Arrange
        lcov_content = """SF:src/file1.py
        DA:1,1
        DA:2,0
        DA:3,1
        end_of_record
        SF:src/file2.py
        DA:1,0
        DA:2,1
        DA:3,1
        end_of_record"""
        lcov_file = tmp_path / "coverage.lcov"
        lcov_file.write_text(lcov_content)

        processor = LcovProcessor(str(lcov_file), "src/file1.py")

        # Act
        result = processor.parse_coverage_report()
        print(result)
        # Assert
        assert len(result) == 2
        assert "src/file1.py" in result
        coverage_data = result["src/file1.py"]
        assert coverage_data.is_target_file == True
        other_coverage_data = result["src/file2.py"]
        assert other_coverage_data.is_target_file == False

class TestJacocoProcessor:
    # Successfully parse XML JaCoCo report and extract coverage data
    def test_parse_xml_coverage_report_success(self, mocker):
        # Arrange
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <report>
            <package name="com/example">
                <class name="com/example" sourcefilename="MyClass.java">
                    <counter type="LINE" missed="5" covered="15"/>
                </class>
            </package>
        </report>'''

        mock_file = mocker.mock_open(read_data='package com.example;\npublic class MyClass {')
        mocker.patch('builtins.open', mock_file)
        mocker.patch('xml.etree.ElementTree.parse', return_value=ET.ElementTree(ET.fromstring(xml_content)))

        processor = JacocoProcessor('coverage.xml', 'com/example/MyClass.java')

        # Act
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert len(coverage_data) == 1
        assert 'com.example.MyClass.java' in coverage_data
        assert coverage_data['com.example.MyClass.java'].missed == 5
        assert coverage_data['com.example.MyClass.java'].covered == 15
        assert coverage_data['com.example.MyClass.java'].coverage == 0.75
        assert coverage_data['com.example.MyClass.java'].is_target_file == True

    # Successfully parse XML JaCoCo report with multiple files and extract coverage data
    def test_parse_xml_coverage_report_multi_files(self, mocker):
        # Arrange
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <report>
            <package name="com/example">
                <class name="com/example" sourcefilename="MyClass.java">
                    <counter type="LINE" missed="5" covered="15"/>
                </class>
                <class name="com/example" sourcefilename="Other.java">
                    <counter type="LINE" missed="2" covered="20"/>
                </class>
            </package>
        </report>'''

        mock_file = mocker.mock_open(read_data='package com.example;\npublic class MyClass {')
        mocker.patch('builtins.open', mock_file)
        mocker.patch('xml.etree.ElementTree.parse', return_value=ET.ElementTree(ET.fromstring(xml_content)))

        processor = JacocoProcessor('coverage.xml', 'com/example/MyClass.java')

        # Act
        coverage_data = processor.parse_coverage_report()

        # Assert
        assert len(coverage_data) == 2
        assert 'com.example.MyClass.java' in coverage_data
        assert coverage_data['com.example.MyClass.java'].is_target_file == True
        assert 'com.example.Other.java' in coverage_data
        assert coverage_data['com.example.Other.java'].missed == 2
        assert coverage_data['com.example.Other.java'].covered == 20
        assert coverage_data['com.example.Other.java'].coverage == 0.9090909090909091
        assert coverage_data['com.example.Other.java'].is_target_file == False

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
        assert len(coverage_data) == 0

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