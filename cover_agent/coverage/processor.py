from abc import ABC, abstractmethod
from dataclasses import dataclass
from cover_agent.CustomLogger import CustomLogger
from typing import Dict, Optional, List, Tuple, Union
import csv
import os
import re
import json
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class CoverageData:
    """
    A class to represent coverage data.

    This class is used to encapsulate information about code coverage
    for a file or class, such as the line numbers that are covered by
    tests, the number of lines that are covered, the line numbers that
    are not covered by tests, the number of lines that are not covered,
    and the coverage percentage.

    Attributes:
        covered_lines (int): The line numbers that are covered by tests.
        covered (int)      : The number of lines that are covered by tests.
        missed_lines (int) : The line numbers that are not covered by tests.
        missed (int)       : The number of lines that are not covered by tests.
        coverage (float)   : The coverage percentage of the file or class.
    """
    covered_lines: List[int]
    covered: int
    missed_lines: List[int]
    missed: int
    coverage: float

@dataclass
class CoverageReport:
    """
    A class to represent the coverage report of a project.

    This class is used to encapsulate information about the coverage
    of a project, such as the total coverage percentage and the coverage
    data for each file in the project.

    Attributes:
    ----------
    total_coverage : float
        The total coverage percentage of the project.
    file_coverage : Dict[str, CoverageData]
        A dictionary mapping file names to their respective coverage data.
    """
    total_coverage: float
    file_coverage: Dict[str, CoverageData]

class CoverageProcessor(ABC):
    """
    Abstract base class for processing coverage reports.

    Attributes:
        file_path (str): The path to the coverage report file.
        src_file_path (str): The path to the source file.
        logger (Logger): The logger object for logging messages.
    Methods:
        parse_coverage_report() -> Union[Tuple[list, list, float], dict]:
            Abstract method to parse the coverage report.
        
        process_coverage_report(time_of_test_command: int) -> Union[Tuple[list, list, float], dict]:
            Processes the coverage report and returns the coverage data.
        
        _is_report_exist():
            Checks if the coverage report file exists.
        
        _is_report_obsolete(time_of_test_command: int):
            Checks if the coverage report file is obsolete based on the test command time.
    """
    def __init__(
        self,
        file_path: str,
        src_file_path: str,
    ):
        self.file_path = file_path
        self.src_file_path = src_file_path
        self.logger = CustomLogger.get_logger(__name__)

    @abstractmethod
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        """
        Parses the coverage report and extracts coverage data.

        This method should be implemented by subclasses to parse the specific
        coverage report format and return a dictionary mapping file names to
        their respective coverage data.

        Returns:
            Dict[str, CoverageData]: A dictionary where keys are file names and
                                    values are CoverageData instances containing
                                    coverage information for each file.
        """
        pass
    
    def process_coverage_report(self, time_of_test_command: int) -> CoverageReport:
        """
        Processes the coverage report and returns the coverage data.
        """
        self._is_coverage_valid(time_of_test_command=time_of_test_command)
        coverage = self.parse_coverage_report()
        report = CoverageReport(0.0, coverage)
        if coverage:
            total_covered = sum(cov.covered for cov in coverage.values())
            total_missed = sum(cov.missed for cov in coverage.values())
            total_lines = total_covered + total_missed
            report.total_coverage = (float(total_covered) / float(total_lines)) if total_lines > 0 else 0.0
        return report

    def _is_coverage_valid(
        self, time_of_test_command: int
    ) ->  None:
        """
        Checks if the coverage report is valid and up-to-date.

        Args:
            time_of_test_command (int): The timestamp of the test command.

        Raises:
            FileNotFoundError: If the coverage report file does not exist.
            ValueError: If the coverage report file is outdated.
        """
        if not self._is_report_exist():
            raise FileNotFoundError(f'Coverage report "{self.file_path}" not found')
        if self._is_report_obsolete(time_of_test_command):
            raise ValueError("Coverage report is outdated")

    def _is_report_exist(self) -> bool:
        """
        Checks if the coverage report file exists.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.exists(self.file_path)

    def _is_report_obsolete(self, time_of_test_command: int) -> bool:
        """
        Checks if the coverage report file is obsolete based on the test command time.

        Args:
            time_of_test_command (int): The timestamp of the test command.

        Returns:
            bool: True if the report is obsolete, False otherwise.
        """
        return int(round(os.path.getmtime(self.file_path) * 1000)) < time_of_test_command
    
class CoberturaProcessor(CoverageProcessor):
    """
    A class to process Cobertura code coverage reports.
    Inherits from CoverageProcessor class and implements
    the parse_coverage_report method.
    """
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        coverage = {}
        for cls in root.findall(".//class"):
            cls_filename = cls.get("filename")
            if cls_filename:
                if cls_filename not in coverage:
                    coverage[cls_filename] = self._parse_coverage_data_for_class(cls)
                else:
                    coverage[cls_filename] = self._merge_coverage_data(coverage[cls_filename], self._parse_coverage_data_for_class(cls))
        return coverage

    def _merge_coverage_data(self, existing_coverage: CoverageData, new_coverage: CoverageData) -> CoverageData:
        covered_lines = existing_coverage.covered_lines + new_coverage.covered_lines
        missed_lines = existing_coverage.missed_lines + new_coverage.missed_lines
        covered = existing_coverage.covered + new_coverage.covered
        missed = existing_coverage.missed + new_coverage.missed
        total_lines = covered + missed
        coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0.0
        return CoverageData(covered_lines, covered, missed_lines, missed, coverage_percentage)

    def _parse_coverage_data_for_class(self, cls) -> CoverageData:
        lines_covered, lines_missed = [], []
        for line in cls.findall(".//line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered.append(line_number)
            else:
                lines_missed.append(line_number)
        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (float(len(lines_covered)) / total_lines) if total_lines > 0 else 0.0
        return CoverageData(lines_covered, len(lines_covered), lines_missed, len(lines_missed), coverage_percentage)

class LcovProcessor(CoverageProcessor):
    """
    A class to process LCOV code coverage reports.
    Inherits from CoverageProcessor class and implements
    the parse_coverage_report method.
    """
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        coverage = {}
        try:
            with open(self.file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("SF:"):
                        filename = line[3:]
                        lines_covered, lines_missed = [], []
                        for line in file:
                            line = line.strip()
                            if line.startswith("DA:"):
                                line_number, hits = map(int, line[3:].split(","))
                                if hits > 0:
                                    lines_covered.append(int(line_number))
                                else:
                                    lines_missed.append(int(line_number))
                            elif line.startswith("end_of_record"):
                                break
                        total_lines = len(lines_covered) + len(lines_missed)
                        coverage_percentage = (float(len(lines_covered)) / total_lines) if total_lines > 0 else 0.0
                        coverage[filename] = CoverageData(lines_covered, len(lines_covered), lines_missed, len(lines_missed), coverage_percentage)
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise
        return coverage

class JacocoProcessor(CoverageProcessor):
    """
    A class to process JaCoCo code coverage reports.
    Inherits from CoverageProcessor class and implements
    the parse_coverage_report method.

    This class supports parsing JaCoCo code coverage
    reports in both XML and CSV formats.
    """
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        coverage = {}
        source_file_extension = self._get_file_extension(self.src_file_path)

        package_name, class_name = "",""
        if source_file_extension == 'java':
            package_name, class_name = self._extract_package_and_class_java()
        elif source_file_extension == 'kt':
            package_name, class_name = self._extract_package_and_class_kotlin()
        else:
            self.logger.warn(f"Unsupported Bytecode Language: {source_file_extension}. Using default Java logic.")
            package_name, class_name = self.extract_package_and_class_java()

        file_extension = self._get_file_extension(self.file_path)

        if file_extension == 'xml':
            lines_missed, lines_covered = self._parse_jacoco_xml(class_name=class_name)
            missed, covered = len(lines_missed), len(lines_covered)
        elif file_extension == 'csv':
            lines_missed, lines_covered = [], []
            missed, covered = self._parse_jacoco_csv(package_name=package_name, class_name=class_name)
        else:
            raise ValueError(f"Unsupported JaCoCo code coverage report format: {file_extension}")
        total_lines = missed + covered
        coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0.0
        coverage[class_name] = CoverageData(covered_lines=lines_covered, covered=covered, missed_lines=lines_missed, missed=missed, coverage=coverage_percentage)
        return coverage
    
    def _get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")

    def _extract_package_and_class_kotlin(self):
        package_pattern = re.compile(r"^\s*package\s+([\w.]+)\s*(?:;)?\s*(?://.*)?$")
        class_pattern = re.compile(r"^\s*(?:public|internal|abstract|data|sealed|enum|open|final|private|protected)*\s*class\s+(\w+).*")
        package_name = ""
        class_name = ""
        try:
            with open(self.src_file_path, "r") as file:
                for line in file:
                    if not package_name:  # Only match package if not already found
                        package_match = package_pattern.match(line)
                        if package_match:
                            package_name = package_match.group(1)
                    if not class_name:  # Only match class if not already found
                        class_match = class_pattern.match(line)
                        if class_match:
                            class_name = class_match.group(1)
                    if package_name and class_name:  # Exit loop if both are found
                        break
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.src_file_path}: {e}")
            raise
        return package_name, class_name
    
    def _extract_package_and_class_java(self):
        package_pattern = re.compile(r"^\s*package\s+([\w\.]+)\s*;.*$")
        class_pattern = re.compile(r"^\s*public\s+class\s+(\w+).*")

        package_name = ""
        class_name = ""
        try:
            with open(self.src_file_path, "r") as file:
                for line in file:
                    if not package_name:  # Only match package if not already found
                        package_match = package_pattern.match(line)
                        if package_match:
                            package_name = package_match.group(1)

                    if not class_name:  # Only match class if not already found
                        class_match = class_pattern.match(line)
                        if class_match:
                            class_name = class_match.group(1)

                    if package_name and class_name:  # Exit loop if both are found
                        break
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.src_file_path}: {e}")
            raise

        return package_name, class_name
    
    def _parse_jacoco_xml(
        self, class_name: str
    ) -> tuple[list, list]:
        """Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file."""
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        sourcefile = (
                root.find(f".//sourcefile[@name='{class_name}.java']") or
                root.find(f".//sourcefile[@name='{class_name}.kt']")
        )

        if sourcefile is None:
            return [], []

        missed, covered = [], []
        for line in sourcefile.findall('line'):
            if line.attrib.get('mi') == '0':
                covered += [int(line.attrib.get('nr', 0))]
            else :
                missed += [int(line.attrib.get('nr', 0))]

        return missed, covered
    def _parse_jacoco_csv(self, package_name, class_name) -> Dict[str, CoverageData]:
        with open(self.file_path, "r") as file:
            reader = csv.DictReader(file)
            missed, covered = 0, 0
            for row in reader:
                if row["PACKAGE"] == package_name and row["CLASS"] == class_name:
                    try:
                        missed = int(row["LINE_MISSED"])
                        covered = int(row["LINE_COVERED"])
                        break
                    except KeyError as e:
                        self.logger.error(f"Missing expected column in CSV: {e}")
                        raise

        return missed, covered

class DiffCoverageProcessor(CoverageProcessor):
    """
    A class to process diff coverage reports.
    Inherits from CoverageProcessor class and implements
    the parse_coverage_report method.

    This class is used to process diff coverage reports in JSON format.
    """
    def __init__(
        self,
        diff_coverage_report_path: str,
        file_path: str,
        src_file_path: str,
    ):
        super().__init__(file_path, src_file_path)
        self.diff_coverage_report_path = diff_coverage_report_path

    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        """
        Parses a JSON-formatted diff coverage report to extract covered lines, missed lines,
        and the coverage percentage for the specified src_file_path.
        Returns:
            Tuple[List[int], List[int], float]: A tuple containing lists of covered and missed lines,
                                                and the coverage percentage.
        """
        with open(self.diff_coverage_report_path, "r") as file:
            report_data = json.load(file)

        # Create relative path components of `src_file_path` for matching
        src_relative_path = os.path.relpath(self.src_file_path)
        src_relative_components = src_relative_path.split(os.sep)

        # Initialize variables for covered and missed lines
        relevant_stats = None
        coverage = {}
        for file_path, stats in report_data["src_stats"].items():
            # Split the JSON's file path into components
            file_path_components = file_path.split(os.sep)

            # Match if the JSON path ends with the same components as `src_file_path`
            if (
                file_path_components[-len(src_relative_components) :]
                == src_relative_components
            ):
                relevant_stats = stats
                break

        # If a match is found, extract the data
        if relevant_stats:
            covered_lines = relevant_stats["covered_lines"]
            violation_lines = relevant_stats["violation_lines"]
            coverage_percentage = (
                relevant_stats["percent_covered"] / 100
            )  # Convert to decimal
        else:
            # Default values if the file isn't found in the report
            covered_lines = []
            violation_lines = []
            coverage_percentage = 0.0

        coverage[self.file_path] = CoverageData(covered_lines=covered_lines, covered=len(covered_lines), missed_lines=violation_lines,missed=len(violation_lines), coverage=coverage_percentage)
        return coverage

class CoverageReportFilter:
    """
    A class to filter coverage reports based on
    file patterns. This class abstracts the logic
    for filtering coverage reports based on file
    patterns.
    """
    def filter_report(self, report: CoverageReport, file_pattern: str) -> CoverageReport:
        """
        Filters the coverage report based on the specified file pattern.

        Args:
            report (CoverageReport): The coverage report to filter.
            file_pattern (str): The file pattern to filter by.

        Returns:
            CoverageReport: The filtered coverage report.
        """
        filtered_coverage = {
            file: coverage 
            for file, coverage in report.file_coverage.items()
            if file_pattern in file
        }
        total_lines = sum(len(cov.covered_lines) + len(cov.missed_lines) for cov in filtered_coverage.values())
        total_coverage = (sum(len(cov.covered_lines) for cov in filtered_coverage.values()) / total_lines) if total_lines > 0 else 0.0
        return CoverageReport(total_coverage = total_coverage, file_coverage=filtered_coverage)

class CoverageProcessorFactory:
    """Factory for creating coverage processors based on tool type."""
    
    @staticmethod
    def create_processor(
        tool_type: str,
        report_path: str, 
        src_file_path: str,
        diff_coverage_report_path: Optional[str] = None
    ) -> CoverageProcessor:
        """
        Creates appropriate coverage processor instance.
        
        Args:
            tool_type: Coverage tool type (cobertura/jacoco/lcov)
            report_path: Path to coverage report
            src_file_path: Path to source file
            
        Returns:
            CoverageProcessor instance
            
        Raises:
            ValueError: If invalid tool type specified
        """
        processors = {
            'cobertura': CoberturaProcessor,
            'jacoco': JacocoProcessor,
            'lcov': LcovProcessor,
            'diff_cover_json': DiffCoverageProcessor
        }
        if tool_type.lower() not in processors:
            raise ValueError(f"Invalid coverage type specified: {tool_type}")
        if tool_type.lower() == 'diff_cover_json':
            return DiffCoverageProcessor(diff_coverage_report_path, report_path, src_file_path)
        return processors[tool_type.lower()](report_path, src_file_path)

def process_coverage(
    tool_type: str,
    time_of_test_command: int,
    report_path: str,
    src_file_path: str,
    is_global_coverage_enabled: bool = True,
    file_pattern: Optional[str] = None,
    diff_coverage_report_path: Optional[str] = None
) -> CoverageReport:
    # Create appropriate processor
    processor = CoverageProcessorFactory.create_processor(tool_type, report_path, src_file_path, diff_coverage_report_path)
    
    # Process full report
    report = processor.process_coverage_report(time_of_test_command=time_of_test_command)
    
    if is_global_coverage_enabled:
        return report

    # Apply filtering if needed
    if file_pattern:
        filter = CoverageReportFilter()
        report = filter.filter_report(report, file_pattern)
    return report