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
    is_target_file: bool
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

    def filter_to_target_coverage(self) -> "CoverageReport":
        """
        Returns a new CoverageReport object with only the target file's coverage data.
        """
        target_coverage = {
            file: coverage
            for file, coverage in self.file_coverage.items()
            if coverage.is_target_file
        }
        total_lines = sum(len(cov.covered_lines) + len(cov.missed_lines) for cov in target_coverage.values())
        total_coverage = (sum(len(cov.covered_lines) for cov in target_coverage.values()) / total_lines) if total_lines > 0 else 0.0
        return CoverageReport(total_coverage, target_coverage)

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
        coverage_data = self.parse_coverage_report()
        total_covered = sum(cov.covered for cov in coverage_data.values())
        total_missed = sum(cov.missed for cov in coverage_data.values())
        total_lines = total_covered + total_missed
        total_coverage = (total_covered / total_lines) if total_lines > 0 else 0.0
        return CoverageReport(total_coverage, coverage_data)

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
        for package in root.findall(".//package"):
            # Package name could be '.' if the class is in the default package
            # Eg: <package name="." line-rate="0.8143" branch-rate="0" complexity="0">
            # In such cases, lets use default as the package name.
            package_name = package.get("name", ".")
            if package_name == ".":
                package_name = "default"
            for cls in package.findall(".//class"):
                # In languages where Class is not a first class citizen,
                # the class name is set to the file name as you can see
                # in the below example from the Cobertura XML report.
                # Usually this could be your util files. So we are good
                # to consier name as the key for the CoverageData.
                # Eg: <class name="utils.py" filename="utils.py" complexity="0" line-rate="0.8794" branch-rate="0">
                class_name = cls.get("name", "")
                fully_qualified_name = f"{package_name}.{class_name}".strip('.')
                coverage[fully_qualified_name] = self._parse_class_coverage(cls)
        return coverage

    def _parse_class_coverage(self, cls) -> CoverageData:
        lines_covered = []
        lines_missed = []
        for line in cls.findall(".//line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered.append(line_number)
            else:
                lines_missed.append(line_number)
        total_lines = len(lines_covered) + len(lines_missed)
        coverage = (len(lines_covered) / total_lines) if total_lines > 0 else 0.0
        is_target = False
        if self.src_file_path.endswith(cls.get("filename")):
            is_target = True
        return CoverageData(is_target, lines_covered, len(lines_covered), lines_missed, len(lines_missed), coverage)
    
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
                        is_target = False
                        if filename == self.src_file_path:
                            is_target = True
                        coverage[filename] = CoverageData(is_target, lines_covered, len(lines_covered), lines_missed, len(lines_missed), coverage_percentage)
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
        extension = os.path.splitext(self.file_path)[1].lower()
        if extension == ".xml":
            return self._parse_xml()
        elif extension == ".csv":
            return self._parse_csv()
        else:
            raise ValueError(f"Unsupported JaCoCo report format: {extension}")
    
    def _parse_xml(self) -> Dict[str, CoverageData]:
        """Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file."""
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        coverage = {}
        for package in root.findall(".//package"):
            package_name = package.get("name", "")
            for cls in package.findall(".//class"):
                class_name = cls.get("sourcefilename", "")
                fully_qualified_name = f"{package_name}.{class_name}".replace("/", ".")
                missed = 0
                covered = 0
                for counter in cls.findall('counter'):
                    if counter.attrib.get('type') == 'LINE':
                        missed += int(counter.attrib.get('missed', 0))
                        covered += int(counter.attrib.get('covered', 0))
                        break
                total_lines = covered + missed
                coverage_percentage = (covered / total_lines) if total_lines > 0 else 0.0
                is_target = False
                src_path = cls.get("name", "")
                if f"{src_path}/{class_name}" == self.src_file_path:
                    is_target = True
                # TODO: Add support for identifying which lines are covered and missed
                coverage[fully_qualified_name] = CoverageData(is_target, [], covered, [], missed, coverage_percentage)
        return coverage

    def _parse_csv(self) -> Dict[str, CoverageData]:
        coverage = {}
        with open(self.file_path, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                group = row.get("GROUP", "").strip()
                package_name = row.get("PACKAGE", "").strip()
                class_name = row.get("CLASS", "").strip()
                fully_qualified_name = f"{group}.{package_name}.{class_name}".strip('.')

                covered = int(row.get("LINE_COVERED", 0))
                missed = int(row.get("LINE_MISSED", 0))
                total = covered + missed
                coverage_percentage = (covered / total) if total > 0 else 0.0
                is_target = False
                src_path = package_name.replace(".", "/")
                if f"{src_path}/{class_name}" == self.src_file_path:
                    is_target = True
                coverage[fully_qualified_name] = CoverageData(is_target, [], covered, [], missed, coverage_percentage)
        return coverage

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

        # Consider every file as target file during diff coverage
        coverage[self.file_path] = CoverageData(is_target_file=True, covered_lines=covered_lines, covered=len(covered_lines), missed_lines=violation_lines,missed=len(violation_lines), coverage=coverage_percentage)
        return coverage

class CoverageProcessorFactory:
    """Factory for creating coverage processors based on tool type."""
    @staticmethod
    def create_processor(
        tool_type: str,
        report_path: str, 
        src_file_path: str,
        diff_report_path: Optional[str] = None
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
        processor_map = {
            "cobertura": CoberturaProcessor,
            "lcov": LcovProcessor,
            "jacoco": JacocoProcessor,
            "diff_cover_json": DiffCoverageProcessor,
        }
        if tool_type.lower() not in processor_map:
            raise ValueError(f"Unsupported tool type: {tool_type}")

        if tool_type.lower() == "diff_cover_json":
            if not diff_report_path:
                raise ValueError("Diff report path must be provided for diff processor.")
            return DiffCoverageProcessor(report_path, src_file_path, diff_report_path)

        return processor_map[tool_type.lower()](report_path, src_file_path)

def process_coverage(
    tool_type: str,
    time_of_test_command: int,
    report_path: str,
    src_file_path: str,
    is_global_coverage_enabled: bool = True,
    diff_coverage_report_path: Optional[str] = None
) -> CoverageReport:
    # Create appropriate processor
    processor = CoverageProcessorFactory.create_processor(tool_type, report_path, src_file_path, diff_coverage_report_path)
    
    # Process full report
    report = processor.process_coverage_report(time_of_test_command=time_of_test_command)
    
    if is_global_coverage_enabled:
        return report

    # If global coverage is disabled, filter to target coverage
    return report.filter_to_target_coverage()