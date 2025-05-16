# [DRAFT] Configuration Parameters

Explanation of parameters from the `configuration.toml` file.

## [default]

### LLM Configuration
- `model`: The LLM model to use for test generation (default: `gpt-4o-2024-11-20`)
- `api_base`: Base URL for API calls, used for local LLM servers (default: `http://localhost:11434`)
- `model_retries`: Number of retry attempts for failed LLM calls (default: `3`)

### Coverage Settings
- `desired_coverage`: Target code coverage percentage to achieve (default: `70`)
- `coverage_type`: Type of coverage report to generate (default: `cobertura`)

### Execution Limits
- `max_iterations`: Maximum number of test generation iterations (default: `3`)
- `max_run_time_sec`: Maximum runtime in seconds for each test generation attempt (default: `30`)
- `max_tests_per_run`: Maximum number of tests to generate per run (default: `4`)
- `allowed_initial_test_analysis_attempts`: Number of attempts for initial test analysis (default: `3`)
- `run_tests_multiple_times`: Number of times to run each test for consistency (default: `1`)

### File Paths
- `log_file_path`: Path to the main log file and its name (default: `run.log`)
- `log_db_path`: Path to the SQLite database for logging and its name (default: `cover_agent_unit_test_runs.db`)
- `report_filepath`: Path to the HTML test results report and its name (default: `test_results.html`)
- `responses_folder`: Directory for storing LLM responses (default: `stored_responses`)

### Docker Settings
- `cover_agent_host_folder`: Host machine folder for cover-agent (default: `dist/cover-agent`)
- `cover_agent_container_folder`: Container folder for cover-agent (default: `/usr/local/bin/cover-agent`)
- `docker_hash_display_length`: Length of displayed Docker hash (default:`12`)
- `record_replay_hash_display_length`: Length of displayed record/replay hash (default: `12`)

### Git Settings
- `branch`: Git branch to use (default: `main`)

### Fuzzy Lookup Settings
- `fuzzy_lookup_threshold`: Threshold for fuzzy matching (default:`95`)
- `fuzzy_lookup_prefix_length`: Prefix length for fuzzy lookup (default: `1000`)
- `fuzzy_lookup_best_ratio`: Best ratio for fuzzy matching (default: `0`)

## [include_files]
- `limit_tokens`: Whether to limit tokens for included files (default: `true`)
- `max_tokens`: Maximum tokens allowed for included files (default: `20000`)

## [tests]
- `max_allowed_runtime_seconds`: Maximum allowed runtime for tests in seconds (default: `30`)
