import argparse
import inspect
import logging
import os
import re

from typing import List

import yaml

from dynaconf import Dynaconf
from grep_ast import filename_to_lang

from cover_agent.lsp_logic.utils.utils import is_forbidden_directory
from cover_agent.settings.config_loader import get_settings
from cover_agent.settings.token_handling import TokenEncoder, clip_tokens
from cover_agent.version import __version__


def load_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    """
    Load and parse YAML data from a given response text.

    Parameters:
    response_text (str): The response text containing YAML data.
    keys_fix_yaml (List[str]): A list of keys to fix YAML formatting (default is an empty list).

    Returns:
    dict: The parsed YAML data.

    If parsing the YAML data directly fails, it attempts to fix the YAML formatting using the 'try_fix_yaml' function.

    Example:
        load_yaml(response_text, keys_fix_yaml=['key1', 'key2'])

    """
    response_text = response_text.strip().removeprefix("```yaml").rstrip("`")
    try:
        data = yaml.safe_load(response_text)
    except Exception as e:
        logging.info(f"Failed to parse AI prediction: {e}. Attempting to fix YAML formatting.")
        data = try_fix_yaml(response_text, keys_fix_yaml=keys_fix_yaml)
        if not data:
            logging.info(f"Failed to parse AI prediction after fixing YAML formatting.")
    return data


def try_fix_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    """
    Attempt to fix YAML formatting issues in the given response text.

    Parameters:
    response_text (str): The response text that may contain YAML data with formatting issues.
    keys_fix_yaml (List[str]): A list of keys to fix YAML formatting (default is an empty list).

    Returns:
    dict: The parsed YAML data after attempting to fix formatting issues.

    The function tries multiple fallback strategies to fix YAML formatting issues:
    1. Tries to convert lines containing specific keys to multiline format.
    2. Tries to extract YAML snippet enclosed between ```yaml``` tags.
    3. Tries to remove leading and trailing curly brackets.
    4. Tries to remove last lines iteratively to fix the formatting.

    If none of the strategies succeed, an empty dictionary is returned.

    Example:
        try_fix_yaml(response_text, keys_fix_yaml=['key1', 'key2'])
    """
    response_text_lines = response_text.split("\n")

    # first fallback - try to convert 'relevant line: ...' to relevant line: |-\n        ...'
    response_text_lines_copy = response_text_lines.copy()
    for i in range(0, len(response_text_lines_copy)):
        for key in keys_fix_yaml:
            if key in response_text_lines_copy[i] and not "|-" in response_text_lines_copy[i]:
                response_text_lines_copy[i] = response_text_lines_copy[i].replace(f"{key}", f"{key} |-\n        ")
    try:
        data = yaml.safe_load("\n".join(response_text_lines_copy))
        logging.info(f"Successfully parsed AI prediction after adding |-\n")
        return data
    except:
        pass

    # second fallback - try to extract only range from first ```yaml to ````
    snippet_pattern = r"```(yaml)?[\s\S]*?```"
    snippet = re.search(snippet_pattern, "\n".join(response_text_lines_copy))
    if snippet:
        snippet_text = snippet.group()
        try:
            data = yaml.safe_load(snippet_text.removeprefix("```yaml").rstrip("`"))
            logging.info(f"Successfully parsed AI prediction after extracting yaml snippet")
            return data
        except:
            pass

    # third fallback - try to remove leading and trailing curly brackets
    response_text_copy = response_text.strip().rstrip().removeprefix("{").removesuffix("}").rstrip(":\n")
    try:
        data = yaml.safe_load(response_text_copy)
        logging.info(f"Successfully parsed AI prediction after removing curly brackets")
        return data
    except:
        pass

    # fourth fallback - try to remove last lines
    data = {}
    for i in range(1, len(response_text_lines)):
        response_text_lines_tmp = "\n".join(response_text_lines[:-i])
        try:
            data = yaml.safe_load(response_text_lines_tmp)
            if "language" in data:
                logging.info(f"Successfully parsed AI prediction after removing {i} lines")
                return data
        except:
            pass

    ## fifth fallback - brute force:
    ## detect 'language:' key and use it as a starting point.
    ## look for last '\n\n' after last 'test_code:' and extract the yaml between them
    try:
        # (1) find index of '\nlanguage:' string:
        index_start = response_text.find("\nlanguage:")
        if index_start == -1:
            index_start = response_text.find("language:")  # if response starts with 'language:'
        # (2) find last appearance ot 'test_code:' string:
        index_last_code = response_text.rfind("test_code:")
        # (3) find the first place after 'test_code:' where there is a '\n\n' character:
        index_end = response_text.find("\n\n", index_last_code)
        if index_end == -1:
            index_end = len(response_text)  # response ends with valid yaml
        response_text_copy = response_text[index_start:index_end].strip()
        try:
            data = yaml.safe_load(response_text_copy)
            logging.info(f"Successfully parsed AI prediction when using the language: key as a starting point")
            return data
        except:
            pass
    except:
        pass


def get_included_files(included_files: list, project_root: str = "", disable_tokens=False) -> str:
    if included_files:
        included_files_content = []
        file_names_rel = []
        for file_path in included_files:
            try:
                with open(file_path, "r") as file:
                    included_files_content.append(file.read())
                    file_path_rel = os.path.relpath(file_path, project_root) if project_root else file_path
                    file_names_rel.append(file_path_rel)
            except IOError as e:
                print(f"Error reading file {file_path}: {str(e)}")
        out_str = ""
        if included_files_content:
            for i, content in enumerate(included_files_content):
                out_str += f"file_path: `{file_names_rel[i]}`\ncontent:\n```\n{content}\n```\n\n\n"

        out_str = out_str.strip()
        if not disable_tokens and get_settings().get("include_files.limit_tokens", False):
            encoder = TokenEncoder.get_token_encoder()
            num_input_tokens = len(encoder.encode(out_str))
            if num_input_tokens > get_settings().get("include_files.max_tokens"):
                print(
                    f"Clipping included files content from {num_input_tokens} to {get_settings().get('include_files.max_tokens')} tokens"
                )
                out_str = clip_tokens(
                    out_str,
                    get_settings().get("include_files.max_tokens"),
                    num_input_tokens=num_input_tokens,
                )
        return out_str
    return ""


def parse_args_full_repo(settings: Dynaconf) -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description=f"Cover Agent v{__version__}")

    # Accepts from environment variables first
    log_db_path = os.getenv("LOG_DB_PATH") or settings.get("log_db_path")

    parser.add_argument(
        "--max-test-files-allowed-to-analyze",
        type=int,
        default=settings.get("max_test_files_allowed_to_analyze"),
        help="The maximum number of test files to analyze. Default: %(default)s.",
    )
    parser.add_argument(
        "--look-for-oldest-unchanged-test-file",
        action="store_true",
        help="If set, Cover-Agent will look for the oldest unchanged test file to analyze.",
    )

    parser.add_argument(
        "--project-language",
        required=True,
        default=settings.get("project_language"),
        help="The programming language of the project ([python, javascript, typescript]). Default: %(default)s.",
    )
    parser.add_argument("--project-root", required=True, help="Path to the root of the project.")

    parser.add_argument(
        "--test-folder",
        help="Relative path to the relevant tests folder.",
    )

    parser.add_argument(
        "--test-file",
        help="Relative path to the specific test file we want to extend.",
    )

    parser.add_argument(
        "--run-each-test-separately",
        type=bool,
        default=True,
        help="Run each test separately. Default: True",
    )

    parser.add_argument(
        "--code-coverage-report-path",
        required=True,
        help="Path to the code coverage report file.",
    )
    parser.add_argument(
        "--test-command",
        required=True,
        help="The command to run tests and generate coverage report.",
    )
    parser.add_argument(
        "--test-command-dir",
        default=os.getcwd(),
        help="The directory to run the test command in. Default: %(default)s.",
    )
    parser.add_argument(
        "--coverage-type",
        default=settings.get("coverage_type"),
        help="Type of coverage report. Default: %(default)s.",
    )
    parser.add_argument(
        "--report-filepath",
        default=settings.get("report_filepath"),
        help="Path to the output report file. Default: %(default)s.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=settings.get("max_iterations"),
        help="The maximum number of iterations. Default: %(default)s.",
    )
    parser.add_argument(
        "--max-run-time-sec",
        type=int,
        default=settings.get("max_run_time_sec"),
        help=(
            "Maximum time (in seconds) allowed for test execution. Overrides the value in configuration.toml "
            "if provided. Default: %(default)s."
        ),
    )
    parser.add_argument(
        "--additional-instructions",
        default="",
        help="Any additional instructions you wish to append at the end of the prompt. Default: %(default)s.",
    )
    parser.add_argument(
        "--model",
        default=settings.get("model_full_repo"),
        help="Which LLM model to use. Default: %(default)s.",
    )
    parser.add_argument(
        "--api-base",
        default=settings.get("api_base"),
        help="The API url to use for Ollama or Hugging Face. Default: %(default)s.",
    )
    parser.add_argument(
        "--strict-coverage",
        action="store_true",
        help="If set, Cover-Agent will return a non-zero exit code if the desired code coverage is not achieved. Default: False.",
    )
    parser.add_argument(
        "--run-tests-multiple-times",
        type=int,
        default=settings.get("run_tests_multiple_times"),
        help="Number of times to run the tests generated by Cover Agent. Default: %(default)s.",
    )
    parser.add_argument(
        "--log-db-path",
        default=log_db_path,
        help="Path to optional log database. Default: %(default)s",
    )
    parser.add_argument(
        "--test-file-output-path",
        type=str,
        default="",
        help="Path to the output test file.",
    )
    parser.add_argument(
        "--desired-coverage",
        type=int,
        default=settings.get("desired_coverage_full_repo"),
        help="The desired coverage percentage. Default: %(default)s.",
    )
    parser.add_argument(
        "--branch",
        type=str,
        default=settings.get("branch"),
        help="The branch to compare against when using --diff-coverage. Default: %(default)s.",
    )
    parser.add_argument(
        "--record-mode",
        action="store_true",
        help="Enable record mode for LLM responses. Default: False.",
    )
    parser.add_argument(
        "--suppress-log-files",
        action="store_true",
        default=False,
        help="Suppress all generated log files (HTML, logs, DB files).",
    )

    # Create mutually exclusive group
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use-report-coverage-feature-flag",
        action="store_true",
        help=(
            "Setting this to True considers the coverage of all the files in the coverage report. This means "
            "we consider a test as good if it increases coverage for a different file other than the source file. "
            "Default: False. Not compatible with --diff-coverage."
        ),
    )
    group.add_argument(
        "--diff-coverage",
        action="store_true",
        help=(
            "If set, Cover-Agent will only generate tests based on the diff between branches. Default: False. "
            "Not compatible with --use-report-coverage-feature-flag."
        ),
    )

    return parser.parse_args()


def find_test_files(args) -> list:
    """
    Scan the project directory for test files.
    """
    project_dir = args.project_root
    language = args.project_language

    # If a specific test file is provided, return it
    if hasattr(args, "test_file") and args.test_file:
        full_path = os.path.join(project_dir, args.test_file)
        if os.path.exists(full_path):
            print(f"\nExtending the test file: `{full_path}`\n")
            return [args.test_file]
        else:
            print(f"Test file not found: `{full_path}`, exiting.\n")
            exit(-1)

    # validate that the test folder exists
    if hasattr(args, "test_folder") and args.test_folder:
        full_path = os.path.join(project_dir, args.test_folder)
        if os.path.exists(full_path):
            print(f"\nExtending the test folder: `{full_path}`\n")
        else:
            print(f"Test folder not found: `{full_path}`, exiting.\n")
            exit(-1)

    MAX_TEST_FILES = args.max_test_files_allowed_to_analyze
    test_files = []
    for root, dirs, files in os.walk(project_dir):
        # Check if the current directory is a 'test' directory
        if not is_forbidden_directory(root.__add__(os.sep), language):
            if hasattr(args, "test_folder") and args.test_folder:
                if args.test_folder not in root:
                    continue
            if "test" in root.split(os.sep):
                for file in files:
                    if filename_to_lang(file) == language:
                        test_files.append(os.path.join(root, file))
            else:
                # Check if any file contains 'test' in its name
                for file in files:
                    if "test" in file:
                        if filename_to_lang(file) == language:
                            test_files.append(os.path.join(root, file))
        if len(test_files) >= MAX_TEST_FILES and args.look_for_oldest_unchanged_test_file:
            print(f"Found {len(test_files)} test files. Stopping at {MAX_TEST_FILES} test files.")
            break

    if args.look_for_oldest_unchanged_test_file:
        test_files.sort(key=os.path.getmtime)
        test_files = test_files[:MAX_TEST_FILES]

    return test_files


def get_original_caller() -> str:
    """
    Gets the name of the original calling function by traversing the call stack
    and skipping framework/internal function calls.

    Returns:
        str: The name of the original calling function with parentheses
    """
    frames_to_skip = {
        "retry_wrapper",
        "wrapper",
        "call_model",
        "get_original_caller",
        "__call__",
        "decorator",
        "wrapped_f",
        "wrap",
        "wrapper_descriptor",
        "actualfunc",
        "wrapped",
        "inner",
    }

    for frame in inspect.stack()[1:]:
        function_name = frame.function
        if not any(function_name.startswith(skip) for skip in ["__", "wrap"]) and function_name not in frames_to_skip:

            return f"{function_name}"

    return "unknown_caller"


def truncate_hash(hash_value: str, hash_display_length: int) -> str:
    """
    Truncate a hash string to a specified length.

    Parameters:
    hash_value (str): The original hash string to be truncated.
    hash_display_length (int): The desired length of the truncated hash.

    Returns:
    str: The truncated hash string.

    Example:
        truncate_hash("abcdef123456", 6)  # Returns "abcdef"
    """
    return hash_value[:hash_display_length]
