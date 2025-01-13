from cover_agent.CustomLogger import CustomLogger
from typing import Literal, Tuple, Union, List
import csv
import json
import os
import re
import xml.etree.ElementTree as ET


class CoverageProcessor:
    def __init__(
        self,
        file_path: str,
        src_file_path: str,
        coverage_type: Literal["cobertura", "lcov", "jacoco"],
        use_report_coverage_feature_flag: bool = False,
        diff_coverage_report_path: str = None,
    ):
        """
        Initializes a CoverageProcessor object.

        Args:
            file_path (str): The path to the coverage report file.
            src_file_path (str): The fully qualified path of the file for which coverage data is being processed.
            coverage_type (Literal["cobertura", "lcov"]): The type of coverage report being processed.

        Attributes:
            file_path (str): The path to the coverage report file.
            src_file_path (str): The fully qualified path of the file for which coverage data is being processed.
            coverage_type (Literal["cobertura", "lcov"]): The type of coverage report being processed.
            logger (CustomLogger): The logger object for logging messages.

        Returns:
            None
        """
        self.file_path = file_path
        self.src_file_path = src_file_path
        self.coverage_type = coverage_type
        self.logger = CustomLogger.get_logger(__name__)
        self.use_report_coverage_feature_flag = use_report_coverage_feature_flag
        self.diff_coverage_report_path = diff_coverage_report_path

    def process_coverage_report(
        self, time_of_test_command: int
    ) -> Tuple[list, list, float]:
        """
        Verifies the coverage report's existence and update time, and then
        parses the report based on its type to extract coverage data.

        Args:
            time_of_test_command (int): The time the test command was run, in milliseconds.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
        """
        self.verify_report_update(time_of_test_command)
        return self.parse_coverage_report()

    def verify_report_update(self, time_of_test_command: int):
        """
        Verifies the coverage report's existence and update time.

        Args:
            time_of_test_command (int): The time the test command was run, in milliseconds.

        Raises:
            AssertionError: If the coverage report does not exist or was not updated after the test command.
        """
        assert os.path.exists(
            self.file_path
        ), f'Fatal: Coverage report "{self.file_path}" was not generated.'

        # Convert file modification time to milliseconds for comparison
        file_mod_time_ms = int(round(os.path.getmtime(self.file_path) * 1000))

        assert (
            file_mod_time_ms > time_of_test_command
        ), f"Fatal: The coverage report file was not updated after the test command. file_mod_time_ms: {file_mod_time_ms}, time_of_test_command: {time_of_test_command}. {file_mod_time_ms > time_of_test_command}"

    def parse_coverage_report(self) -> Tuple[list, list, float]:
            """
            Parses a code coverage report to extract covered and missed line numbers for a specific file,
            and calculates the coverage percentage, based on the specified coverage report type.
    
            Returns:
                Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
            """
            if self.use_report_coverage_feature_flag:
                if self.coverage_type == "cobertura":
                    return self.parse_coverage_report_cobertura()
                elif self.coverage_type == "lcov":
                    return self.parse_coverage_report_lcov()
                elif self.coverage_type == "jacoco":
                    return self.parse_coverage_report_jacoco()
                else:
                    raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")
            else:
                if self.coverage_type == "cobertura":
                    # Default behavior is to parse out a single file from the report
                    return self.parse_coverage_report_cobertura(filename=os.path.basename(self.src_file_path))
                elif self.coverage_type == "lcov":
                    return self.parse_coverage_report_lcov()
                elif self.coverage_type == "jacoco":
                    return self.parse_coverage_report_jacoco()
                elif self.coverage_type == "diff_cover_json":
                    return self.parse_json_diff_coverage_report()
                else:
                    raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")

    def parse_coverage_report_cobertura(self, filename: str = None) -> Union[Tuple[list, list, float], dict]:
        """
        Parses a Cobertura XML code coverage report to extract covered and missed line numbers
        for a specific file or for all files (if filename is None). Aggregates coverage data from
        multiple <class> entries that share the same filename.

        Args:
            filename (str, optional): Filename to process. If None, process all files.

        Returns:
            If filename is provided, returns (covered_lines, missed_lines, coverage_percent).
            If filename is None, returns a dict: { filename: (covered_lines, missed_lines, coverage_percent) }.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        if filename:
            # Collect coverage for all <class> elements matching the given filename
            all_covered, all_missed = [], []
            for cls in root.findall(".//class"):
                name_attr = cls.get("filename")
                if name_attr and name_attr.endswith(filename):
                    c_covered, c_missed, _ = self.parse_coverage_data_for_class(cls)
                    all_covered.extend(c_covered)
                    all_missed.extend(c_missed)

            # Deduplicate and compute coverage
            covered_set = set(all_covered)
            missed_set = set(all_missed) - covered_set
            total_lines = len(covered_set) + len(missed_set)
            coverage_percentage = (len(covered_set) / total_lines) if total_lines else 0

            return list(covered_set), list(missed_set), coverage_percentage

        else:
            # Collect coverage for every <class>, grouping by filename
            coverage_data = {}
            file_map = {}  # filename -> ([covered], [missed])

            for cls in root.findall(".//class"):
                cls_filename = cls.get("filename")
                if cls_filename:
                    c_covered, c_missed, _ = self.parse_coverage_data_for_class(cls)
                    if cls_filename not in file_map:
                        file_map[cls_filename] = ([], [])
                    file_map[cls_filename][0].extend(c_covered)
                    file_map[cls_filename][1].extend(c_missed)

            # Convert raw lists to sets, compute coverage, store results
            for f_name, (c_covered, c_missed) in file_map.items():
                covered_set = set(c_covered)
                missed_set = set(c_missed) - covered_set
                total_lines = len(covered_set) + len(missed_set)
                coverage_percentage = (len(covered_set) / total_lines) if total_lines else 0
                coverage_data[f_name] = (list(covered_set), list(missed_set), coverage_percentage)

            return coverage_data

    def parse_coverage_data_for_class(self, cls) -> Tuple[list, list, float]:
        """
        Parses coverage data for a single class.

        Args:
            cls (Element): XML element representing the class.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, 
                                    and the coverage percentage.
        """
        lines_covered, lines_missed = [], []

        for line in cls.findall(".//line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered.append(line_number)
            else:
                lines_missed.append(line_number)

        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (len(lines_covered) / total_lines) if total_lines > 0 else 0

        return lines_covered, lines_missed, coverage_percentage

    def parse_coverage_report_lcov(self):

        lines_covered, lines_missed = [], []
        filename = os.path.basename(self.src_file_path)
        try: 
            with open(self.file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("SF:"):
                        if line.endswith(filename):
                            for line in file:
                                line = line.strip()
                                if line.startswith("DA:"):
                                    line_number = line.replace("DA:", "").split(",")[0]
                                    hits = line.replace("DA:", "").split(",")[1]
                                    if int(hits) > 0:
                                        lines_covered.append(int(line_number))
                                    else:
                                        lines_missed.append(int(line_number))
                                elif line.startswith("end_of_record"):
                                    break

        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise

        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (
            (len(lines_covered) / total_lines) if total_lines > 0 else 0
        )

        return lines_covered, lines_missed, coverage_percentage

    def parse_coverage_report_jacoco(self) -> Tuple[list, list, float]:
        """
        Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the coverage percentage.

        Returns: Tuple[list, list, float]: A tuple containing empty lists of covered and missed line numbers,
        and the coverage percentage. The reason being the format of the report for jacoco gives the totals we do not
        sum them up. to stick with the current contract of the code and to do little change returning empty arrays.
        I expect this should bring up a discussion on introduce a factory for different CoverageProcessors. Where the
        total coverage percentage is returned to be evaluated only.
        """
        lines_covered, lines_missed = [], []
        source_file_extension = self.get_file_extension(self.src_file_path)

        package_name, class_name = "",""
        if source_file_extension == 'java':
            package_name, class_name = self.extract_package_and_class_java()
        elif source_file_extension == 'kt':
            package_name, class_name = self.extract_package_and_class_kotlin()
        else:
            self.logger.warn(f"Unsupported Bytecode Language: {source_file_extension}. Using default Java logic.")
            package_name, class_name = self.extract_package_and_class_java()


        file_extension = self.get_file_extension(self.file_path)

        missed, covered = 0, 0
        if file_extension == 'xml':
            lines_missed, lines_covered = self.parse_missed_covered_lines_jacoco_xml(
                class_name
            )
            missed, covered = len(lines_missed), len(lines_covered)
        elif file_extension == 'csv':
            missed, covered = self.parse_missed_covered_lines_jacoco_csv(
                package_name, class_name
            )
        else:
            raise ValueError(f"Unsupported JaCoCo code coverage report format: {file_extension}")

        total_lines = missed + covered
        coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0

        return lines_covered, lines_missed, coverage_percentage

    def parse_missed_covered_lines_jacoco_xml(
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

    def parse_missed_covered_lines_jacoco_csv(
        self, package_name: str, class_name: str
    ) -> tuple[int, int]:
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
                        self.logger.error(f"Missing expected column in CSV: {str(e)}")
                        raise

        return missed, covered

    def extract_package_and_class_java(self):
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
    def extract_package_and_class_kotlin(self):
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

    def parse_json_diff_coverage_report(self) -> Tuple[List[int], List[int], float]:
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

        return covered_lines, violation_lines, coverage_percentage


    def get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")
