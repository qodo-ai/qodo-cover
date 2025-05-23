import xml.etree.ElementTree as ET

import pytest

from cover_agent.coverage_processor import CoverageProcessor


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


class TestCoverageProcessor:
    """
    Test suite for the CoverageProcessor class.
    """

    @pytest.fixture
    def processor(self):
        """
        Initializes CoverageProcessor with cobertura coverage type for each test.
        """
        return CoverageProcessor("fake_path", "app.py", "cobertura")

    def test_parse_coverage_report_cobertura(self, mock_xml_tree, processor):
        """
        Tests the parse_coverage_report method for correct line number and coverage calculation with Cobertura reports.
        """
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report()

        assert covered_lines == [1, 3], "Should list lines 1 and 3 as covered"
        assert missed_lines == [2, 4], "Should list lines 2 and 4 as missed"
        assert coverage_pct == 0.5, "Coverage should be 50 percent"

    def test_correct_parsing_for_matching_package_and_class(self, mocker):
        """
        Tests parsing of missed and covered lines for a matching package and class in a JaCoCo CSV report.
        """
        # Setup
        mock_open = mocker.patch(
            "builtins.open",
            mocker.mock_open(read_data="PACKAGE,CLASS,LINE_MISSED,LINE_COVERED\ncom.example,MyClass,5,10"),
        )
        mocker.patch(
            "csv.DictReader",
            return_value=[
                {
                    "PACKAGE": "com.example",
                    "CLASS": "MyClass",
                    "LINE_MISSED": "5",
                    "LINE_COVERED": "10",
                }
            ],
        )
        processor = CoverageProcessor("path/to/coverage_report.csv", "path/to/MyClass.java", "jacoco")

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco_csv("com.example", "MyClass")

        # Assert
        assert missed == 5
        assert covered == 10

    def test_returns_empty_lists_and_float(self, mocker):
        """
        Tests that parse_coverage_report_jacoco returns empty lists and 0 coverage percentage when no data is found.
        """
        # Mocking the necessary methods
        mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )
        mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_missed_covered_lines_jacoco_xml",
            return_value=([], []),
        )

        # Initialize the CoverageProcessor object
        coverage_processor = CoverageProcessor(
            file_path="path/to/coverage.xml",
            src_file_path="path/to/example.java",
            coverage_type="jacoco",
        )

        # Invoke the parse_coverage_report_jacoco method
        lines_covered, lines_missed, coverage_percentage = coverage_processor.parse_coverage_report_jacoco()

        # Assert the results
        assert lines_covered == [], "Expected lines_covered to be an empty list"
        assert lines_missed == [], "Expected lines_missed to be an empty list"
        assert coverage_percentage == 0, "Expected coverage percentage to be 0"

    def test_parse_coverage_report_unsupported_type(self):
        """
        Tests that parse_coverage_report raises a ValueError for unsupported coverage report types.
        """
        processor = CoverageProcessor("fake_path", "app.py", "unsupported_type")
        with pytest.raises(ValueError, match="Unsupported coverage report type: unsupported_type"):
            processor.parse_coverage_report()

    def test_extract_package_and_class_java_file_error(self, mocker):
        """
        Tests that extract_package_and_class_java raises a FileNotFoundError when the file does not exist.
        """
        mocker.patch("builtins.open", side_effect=FileNotFoundError("File not found"))
        processor = CoverageProcessor("fake_path", "path/to/MyClass.java", "jacoco")
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.extract_package_and_class_java()

    def test_extract_package_and_class_kotlin(self, mocker):
        """
        Tests extraction of package and class names from a Kotlin file.
        """
        kotlin_file_content = """
        package com.madrapps.playground
    
        import androidx.lifecycle.ViewModel

        class MainViewModel : ViewModel() {
        
            fun validate(userId: String): Boolean {
                return userId == "admin"
            }
        
            fun verifyAccess1(userId: String): Boolean {
                return userId == "super-admin"
            }
        
            fun verifyPassword(password: String): Boolean {
                return password.isNotBlank()
            }
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=kotlin_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MainViewModel.kt", "jacoco")
        package_name, class_name = processor.extract_package_and_class_kotlin()
        assert package_name == "com.madrapps.playground", "Expected package name to be 'com.madrapps.playground'"
        assert class_name == "MainViewModel", "Expected class name to be 'MainViewModel'"

    def test_extract_package_and_class_java(self, mocker):
        """
        Tests extraction of package and class names from a Java public Class source file.
        """
        java_file_content = """
        package com.example;

        public class MyClass {
            // class content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MyClass.java", "jacoco")
        package_name, class_name = processor.extract_package_and_class_java()
        assert package_name == "com.example", "Expected package name to be 'com.example'"
        assert class_name == "MyClass", "Expected class name to be 'MyClass'"

    def test_extract_package_and_class_java_nonpublic(self, mocker):
        """
        Tests extraction of package and class names from a Java package scoped Class source file.
        """
        java_file_content = """
        package com.example;

        class MyClass {
            // class content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MyClass.java", "jacoco")
        package_name, class_name = processor.extract_package_and_class_java()
        assert (
            package_name == "com.example"
        ), "Expected package name to be 'com.example'"
        assert class_name == "MyClass", "Expected class name to be 'MyClass'"

    def test_extract_package_and_class_java_interface(self, mocker):
        """

        Tests extraction of package and class names from a Java Interface source file.

        """
        java_file_content = """
        package com.example;

        interface MyInterface {
            // interface content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MyInterface.java", "jacoco")
        package_name, class_name = processor.extract_package_and_class_java()
        assert (
            package_name == "com.example"
        ), "Expected package name to be 'com.example'"
        assert class_name == "MyInterface", "Expected class name to be 'MyInterface'"

    def test_extract_package_and_class_java_record(self, mocker):
        """
        Tests extraction of package and class names from a Java Record source file.
        """
        java_file_content = """
        package com.example;

        record MyRecord {
            // record content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MyRecord.java", "jacoco")
        package_name, class_name = processor.extract_package_and_class_java()
        assert (
                package_name == "com.example"
        ), "Expected package name to be 'com.example'"
        assert class_name == "MyRecord", "Expected class name to be 'MyRecord'"

    def test_extract_package_and_class_java_template(self, mocker):
        """
        Tests extraction of package and class names from a Java Template source file.
        """
        java_file_content = """
        package com.example;

        class MyTemplate<T> {
            // template content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MyTemplate.java", "jacoco")
        package_name, class_name = processor.extract_package_and_class_java()
        assert (
            package_name == "com.example"
        ), "Expected package name to be 'com.example'"
        assert class_name == "MyTemplate", "Expected class name to be 'MyTemplate'"

    @pytest.mark.skip("no longer an assert. needs rewrite. check out caplog")
    def test_verify_report_update_file_not_updated(self, mocker):
        """
        Tests that verify_report_update raises an AssertionError if the coverage report file was not updated.
        """
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.getmtime", return_value=1234567.0)

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        with pytest.raises(
            AssertionError,
            match="Fatal: The coverage report file was not updated after the test command.",
        ):
            processor.verify_report_update(1234567890)

    def test_verify_report_update_file_not_exist(self, mocker):
        """
        Tests that verify_report_update raises an AssertionError if the coverage report file does not exist.
        """
        mocker.patch("os.path.exists", return_value=False)

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        with pytest.raises(
            AssertionError,
            match='Fatal: Coverage report "fake_path" was not generated.',
        ):
            processor.verify_report_update(1234567890)

    def test_process_coverage_report(self, mocker):
        """
        Tests the process_coverage_report method for verifying and parsing the coverage report.
        """
        mock_verify = mocker.patch("cover_agent.coverage_processor.CoverageProcessor.verify_report_update")
        mock_parse = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report",
            return_value=([], [], 0.0),
        )

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        result = processor.process_coverage_report(1234567890)

        mock_verify.assert_called_once_with(1234567890)
        mock_parse.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_missed_covered_lines_jacoco_csv_key_error(self, mocker):
        """
        Tests that parse_missed_covered_lines_jacoco_csv raises a KeyError when a required key is missing in the CSV.
        """
        mock_open = mocker.patch(
            "builtins.open",
            mocker.mock_open(read_data="PACKAGE,CLASS,LINE_MISSED,LINE_COVERED\ncom.example,MyClass,5,10"),
        )
        mocker.patch(
            "csv.DictReader",
            return_value=[{"PACKAGE": "com.example", "CLASS": "MyClass", "LINE_MISSED": "5"}],
        )  # Missing 'LINE_COVERED'

        processor = CoverageProcessor("path/to/coverage_report.csv", "path/to/MyClass.java", "jacoco")

        with pytest.raises(KeyError):
            processor.parse_missed_covered_lines_jacoco_csv("com.example", "MyClass")

    def test_parse_coverage_report_lcov_no_coverage_data(self, mocker):
        """
        Tests that parse_coverage_report_lcov returns empty lists and 0 coverage when the lcov report contains no relevant data.
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=""))
        processor = CoverageProcessor("empty_report.lcov", "app.py", "lcov")
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_lcov()
        assert covered_lines == [], "Expected no covered lines"
        assert missed_lines == [], "Expected no missed lines"
        assert coverage_pct == 0, "Expected 0% coverage"

    def test_parse_coverage_report_lcov_with_coverage_data(self, mocker):
        """
        Tests that parse_coverage_report_lcov correctly parses coverage data from an lcov report.
        """
        lcov_data = """
        SF:app.py
        DA:1,1
        DA:2,0
        DA:3,1
        end_of_record
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=lcov_data))
        processor = CoverageProcessor("report.lcov", "app.py", "lcov")
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_lcov()
        assert covered_lines == [1, 3], "Expected lines 1 and 3 to be covered"
        assert missed_lines == [2], "Expected line 2 to be missed"
        assert coverage_pct == 2 / 3, "Expected 66.67% coverage"

    def test_parse_coverage_report_lcov_with_multiple_files(self, mocker):
        """
        Tests that parse_coverage_report_lcov correctly parses coverage data for the target file among multiple files in the lcov report.
        """
        lcov_data = """
        SF:other.py
        DA:1,1
        DA:2,0
        end_of_record
        SF:app.py
        DA:1,1
        DA:2,0
        DA:3,1
        end_of_record
        SF:another.py
        DA:1,1
        end_of_record
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=lcov_data))
        processor = CoverageProcessor("report.lcov", "app.py", "lcov")
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_lcov()
        assert covered_lines == [
            1,
            3,
        ], "Expected lines 1 and 3 to be covered for app.py"
        assert missed_lines == [2], "Expected line 2 to be missed for app.py"
        assert coverage_pct == 2 / 3, "Expected 66.67% coverage for app.py"

    def test_parse_coverage_report_unsupported_type(self, mocker):
        """
        Tests that parse_coverage_report_jacoco raises a ValueError for unsupported JaCoCo report formats.
        """
        mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )

        processor = CoverageProcessor("path/to/coverage_report.html", "path/to/MyClass.java", "jacoco")
        with pytest.raises(ValueError, match="Unsupported JaCoCo code coverage report format: html"):
            processor.parse_coverage_report_jacoco()

    def test_parse_missed_covered_lines_jacoco_xml_no_source_file(self, mocker):
        """
        Tests that parse_missed_covered_lines_jacoco_xml returns empty lists when the source file is not found in the XML report.
        """
        mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
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
            return_value=ET.ElementTree(ET.fromstring(xml_str)),
        )

        processor = CoverageProcessor("path/to/coverage_report.xml", "path/to/MySecondClass.java", "jacoco")

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco_xml("MySecondClass")

        # Assert
        assert missed == []
        assert covered == []

    def test_parse_missed_covered_lines_jacoco_xml(self, mocker):
        """
        Tests parsing of missed and covered lines from a JaCoCo XML report.
        """
        mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
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
            return_value=ET.ElementTree(ET.fromstring(xml_str)),
        )

        processor = CoverageProcessor("path/to/coverage_report.xml", "path/to/MyClass.java", "jacoco")

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco_xml("MyClass")

        # Assert
        assert missed == [39, 40, 41]
        assert covered == [35, 36, 37, 38]

    def test_parse_missed_covered_lines_kotlin_jacoco_xml(self, mocker):
        """
        Tests parsing of missed and covered lines from a JaCoCo XML report for a Kotlin file.
        """
        mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.extract_package_and_class_kotlin",
            return_value=("com.example", "Example"),
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
            return_value=ET.ElementTree(ET.fromstring(xml_str)),
        )

        processor = CoverageProcessor("path/to/coverage_report.xml", "path/to/MyClass.kt", "jacoco")

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco_xml("MyClass")

        # Assert
        assert missed == [39, 40, 41]
        assert covered == [35, 36, 37, 38]

    def test_get_file_extension_with_valid_file_extension(self):
        """
        Tests that get_file_extension correctly extracts the file extension from a valid file name.
        """
        processor = CoverageProcessor("path/to/coverage_report.xml", "path/to/MyClass.java", "jacoco")

        file_extension = processor.get_file_extension("coverage_report.xml")

        # Assert
        assert file_extension == "xml"

    def test_get_file_extension_with_no_file_extension(self):
        """
        Tests that get_file_extension returns an empty string when the file name has no extension.
        """
        processor = CoverageProcessor("path/to/coverage_report", "path/to/MyClass.java", "jacoco")

        file_extension = processor.get_file_extension("coverage_report")

        # Assert
        assert file_extension == ""

    def test_parse_coverage_report_lcov_with_feature_flag(self, mocker):
        """
        Tests that parse_coverage_report calls parse_coverage_report_lcov when the feature flag is enabled.
        """
        mock_parse_lcov = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report_lcov",
            return_value=([], [], 0.0),
        )
        processor = CoverageProcessor("fake_path", "app.py", "lcov", use_report_coverage_feature_flag=True)
        result = processor.parse_coverage_report()
        mock_parse_lcov.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_cobertura_with_feature_flag(self, mocker):
        """
        Tests that parse_coverage_report calls parse_coverage_report_cobertura when the feature flag is enabled.
        """
        mock_parse_cobertura = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report_cobertura",
            return_value=([], [], 0.0),
        )
        processor = CoverageProcessor("fake_path", "app.py", "cobertura", use_report_coverage_feature_flag=True)
        result = processor.parse_coverage_report()
        mock_parse_cobertura.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_jacoco(self, mocker):
        """
        Tests that parse_coverage_report calls parse_coverage_report_jacoco when the feature flag is enabled.
        """
        mock_parse_jacoco = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report_jacoco",
            return_value=([], [], 0.0),
        )
        processor = CoverageProcessor("fake_path", "app.py", "jacoco", use_report_coverage_feature_flag=True)
        result = processor.parse_coverage_report()
        mock_parse_jacoco.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_cobertura_filename_not_found(self, mock_xml_tree, processor):
        """
        Tests that parse_coverage_report_cobertura returns empty lists and 0 coverage when the file is not found.
        """
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_cobertura("non_existent_file.py")
        assert covered_lines == [], "Expected no covered lines"
        assert missed_lines == [], "Expected no missed lines"
        assert coverage_pct == 0.0, "Expected 0% coverage"

    def test_parse_coverage_report_lcov_file_read_error(self, mocker):
        """
        Tests that parse_coverage_report_lcov raises an IOError when the file cannot be read.
        """
        mocker.patch("builtins.open", side_effect=IOError("File read error"))
        processor = CoverageProcessor("report.lcov", "app.py", "lcov")
        with pytest.raises(IOError, match="File read error"):
            processor.parse_coverage_report_lcov()

    def test_parse_coverage_report_cobertura_all_files(self, mock_xml_tree, processor):
        """
        Tests that parse_coverage_report_cobertura returns coverage data for all files.
        """
        coverage_data = processor.parse_coverage_report_cobertura()
        expected_data = {"app.py": ([1, 3], [2, 4], 0.5)}
        assert coverage_data == expected_data, "Expected coverage data for all files"

    def test_parse_coverage_report_unsupported_type_with_feature_flag(self):
        """
        Tests that parse_coverage_report raises a ValueError for unsupported coverage report types when the feature flag is enabled.
        """
        processor = CoverageProcessor(
            "fake_path",
            "app.py",
            "unsupported_type",
            use_report_coverage_feature_flag=True,
        )
        with pytest.raises(ValueError, match="Unsupported coverage report type: unsupported_type"):
            processor.parse_coverage_report()

    def test_parse_coverage_report_jacoco_without_feature_flag(self, mocker):
        """
        Tests that parse_coverage_report calls parse_coverage_report_jacoco when the feature flag is disabled.
        """
        mock_parse_jacoco = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report_jacoco",
            return_value=([], [], 0.0),
        )
        processor = CoverageProcessor("fake_path", "app.py", "jacoco", use_report_coverage_feature_flag=False)
        result = processor.parse_coverage_report()
        mock_parse_jacoco.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_unsupported_type_without_feature_flag(self):
        """
        Tests that parse_coverage_report raises a ValueError for unsupported coverage report types when the feature flag is disabled.
        """
        processor = CoverageProcessor(
            "fake_path",
            "app.py",
            "unsupported_type",
            use_report_coverage_feature_flag=False,
        )
        with pytest.raises(ValueError, match="Unsupported coverage report type: unsupported_type"):
            processor.parse_coverage_report()

    def test_parse_coverage_report_lcov_without_feature_flag(self, mocker):
        """
        Tests that parse_coverage_report calls parse_coverage_report_lcov when the feature flag is disabled.
        """
        mock_parse_lcov = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_coverage_report_lcov",
            return_value=([], [], 0.0),
        )
        processor = CoverageProcessor("fake_path", "app.py", "lcov", use_report_coverage_feature_flag=False)
        result = processor.parse_coverage_report()
        mock_parse_lcov.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_diff_cover_json(self, mocker):
        """
        Tests that parse_coverage_report calls parse_json_diff_coverage_report for diff_cover_json type.
        """
        # Mock the parse_json_diff_coverage_report method
        mock_parse_json = mocker.patch(
            "cover_agent.coverage_processor.CoverageProcessor.parse_json_diff_coverage_report",
            return_value=([1, 3, 5], [2, 4, 6], 0.5),
        )

        # Create processor with diff_cover_json type
        processor = CoverageProcessor(
            "fake_path",
            "app.py",
            "diff_cover_json",
            diff_coverage_report_path="diff_coverage.json",
        )

        # Call parse_coverage_report
        result = processor.parse_coverage_report()

        # Verify the correct method was called and results returned
        mock_parse_json.assert_called_once()
        assert result == ([1, 3, 5], [2, 4, 6], 0.5)

    def test_parse_json_diff_coverage_report(self, mocker):
        """
        Tests parsing of JSON diff coverage report.
        """
        # Mock JSON data
        mock_json_data = {
            "src_stats": {
                "path/to/app.py": {
                    "covered_lines": [1, 3, 5],
                    "violation_lines": [2, 4, 6],
                    "percent_covered": 50.0,
                }
            }
        }

        # Mock open and json.load
        mock_open = mocker.patch("builtins.open", mocker.mock_open())
        mocker.patch("json.load", return_value=mock_json_data)

        # Create processor with diff_coverage_report_path
        processor = CoverageProcessor(
            "fake_path",
            "path/to/app.py",
            "diff_cover_json",
            diff_coverage_report_path="diff_coverage.json",
        )

        # Call the method
        covered_lines, missed_lines, coverage_pct = processor.parse_json_diff_coverage_report()

        # Verify results
        assert covered_lines == [1, 3, 5]
        assert missed_lines == [2, 4, 6]
        assert coverage_pct == 0.5

        # Test with file not found in report
        processor = CoverageProcessor(
            "fake_path",
            "path/to/nonexistent.py",
            "diff_cover_json",
            diff_coverage_report_path="diff_coverage.json",
        )

        covered_lines, missed_lines, coverage_pct = processor.parse_json_diff_coverage_report()

        # Verify default values returned
        assert covered_lines == []
        assert missed_lines == []
        assert coverage_pct == 0.0
