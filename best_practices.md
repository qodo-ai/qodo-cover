
<b>Pattern 1: Always provide default values for optional parameters in method signatures to improve usability and prevent runtime errors, especially in abstract base classes or interfaces.
</b>

Example code before:
```
def generate_tests(
    self,
    source_file_name: str,
    max_tests: int,
    source_file_numbered: str,
    code_coverage_report: str,
    additional_instructions_text: str,
    additional_includes_section: str,
    language: str,
    test_file: str,
    failed_tests_section: str,
    test_file_name: str,
    testing_framework: str,
) -> Tuple[str, int, int, str]:
```

Example code after:
```
def generate_tests(
    self,
    source_file_name: str,
    max_tests: int,
    source_file_numbered: str,
    code_coverage_report: str,
    additional_instructions_text: str = None,
    additional_includes_section: str = None,
    language: str = "python",
    test_file: str = "",
    failed_tests_section: str = "",
    test_file_name: str = "",
    testing_framework: str = "pytest",
) -> Tuple[str, int, int, str]:
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/qodo-cover/pull/282#discussion_r1962272952
</details>


___

<b>Pattern 2: Use standard library functions for file operations rather than implementing custom solutions. For example, use os.path.splitext() to extract file extensions instead of regex patterns.
</b>

Example code before:
```
def get_file_extension(self, filename: str) -> str | None:
    """Get the file extension from a given filename."""
    match = re.search(r'\.(\w+)$', filename)
    if match:
        return match.group(1)
    else:
        return None
```

Example code after:
```
def get_file_extension(self, filename: str) -> str | None:
    """Get the file extension from a given filename."""
    return os.path.splitext(filename)[1].lstrip(".")
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/qodo-cover/pull/132#discussion_r1699234435
</details>


___

<b>Pattern 3: Use dictionary get() method with default values when accessing potentially missing keys to avoid KeyError exceptions, especially when processing data from external sources or user input.
</b>

Example code before:
```
for failed_test in self.failed_test_runs:
    failed_test_dict = failed_test['code']
    # dump dict to str
    code = json.dumps(failed_test_dict)
```

Example code after:
```
for failed_test in self.failed_test_runs:
    failed_test_dict = failed_test.get('code', {})
    # dump dict to str
    code = json.dumps(failed_test_dict)
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/qodo-cover/pull/50#discussion_r1615420296
- https://github.com/qodo-ai/qodo-cover/pull/50#discussion_r1615419981
</details>


___

<b>Pattern 4: Log warnings instead of raising exceptions for non-critical issues to improve robustness and user experience, especially when handling different file formats or language support.
</b>

Example code before:
```
if source_file_extension == 'java':
    package_name, class_name = self.extract_package_and_class_java()
elif source_file_extension == 'kt':
    package_name, class_name = self.extract_package_and_class_kotlin()
else:
    raise ValueError(f"Unsupported Byte Class Language: {source_file_extension}")
```

Example code after:
```
if source_file_extension == 'java':
    package_name, class_name = self.extract_package_and_class_java()
elif source_file_extension == 'kt':
    package_name, class_name = self.extract_package_and_class_kotlin()
else:
    self.logger.warn(f"Unsupported Bytecode Language: {source_file_extension}. Using default Java logic.")
    package_name, class_name = self.extract_package_and_class_java()
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/qodo-cover/pull/221#discussion_r1844110505
</details>


___
