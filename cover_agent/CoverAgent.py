import datetime
import os
import shutil
import sys
import wandb

from typing import Optional

from cover_agent.CustomLogger import CustomLogger
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.UnitTestValidator import UnitTestValidator
from cover_agent.UnitTestDB import UnitTestDB
from cover_agent.AICaller import AICaller
from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.DefaultAgentCompletion import DefaultAgentCompletion
from cover_agent.ai_caller_replay import AICallerReplay
from cover_agent.record_replay_manager import RecordReplayManager


class CoverAgent:
    """
    A class that manages the generation and validation of unit tests to achieve desired code coverage.
    
    This agent coordinates between test generation and validation components, handles file management,
    and tracks the progress of coverage improvements over multiple iterations.
    """
    
    def __init__(self, args, agent_completion: AgentCompletionABC=None, logger: Optional[CustomLogger]=None):
        """
        Initialize the CoverAgent with configuration and set up test generation environment.

        Parameters:
            args (Namespace): Command-line arguments containing:
                - paths for source and test files
                - project configuration
                - coverage requirements
                - test execution settings
            agent_completion (AgentCompletionABC, optional): Custom completion agent for test generation.
                                                           Defaults to DefaultAgentCompletion.

        Raises:
            FileNotFoundError: If required source files or directories are not found.
        """
        self.args = args
        self.generate_log_files = not args.suppress_log_files
        # Initialize logger with file generation flag
        self.logger = logger or CustomLogger.get_logger(__name__, generate_log_files=self.generate_log_files)
        if args.suppress_log_files:
            self.logger.info("Suppressed all generated log files.")

        self._validate_paths()
        self._duplicate_test_file()

        # Configure the AgentCompletion object
        if agent_completion:
            self.agent_completion = agent_completion
        else:
            self.ai_caller = self._initialize_ai_caller()
            self.agent_completion = DefaultAgentCompletion(
            caller=self.ai_caller, generate_log_files=self.generate_log_files
            )

        # Modify test command for a single test execution if needed
        test_command = args.test_command
        new_command_line = None
        if hasattr(args, "run_each_test_separately") and args.run_each_test_separately:
            # Calculate a relative path for a test file
            test_file_relative_path = os.path.relpath(
                args.test_file_output_path, args.project_root
            )
            # Handle pytest commands specifically
            if "pytest" in test_command:
                try:
                    # Modify pytest command to target a single test file
                    ind1 = test_command.index("pytest")
                    ind2 = test_command[ind1:].index("--")
                    new_command_line = f"{test_command[:ind1]}pytest {test_file_relative_path} {test_command[ind1 + ind2:]}"
                except ValueError:
                    self.logger.error(f"Failed to adapt test command for running a single test: {test_command}")
            else:
                # Use AI to adapt non-pytest test commands
                new_command_line, _, _, _ = (
                    self.agent_completion.adapt_test_command_for_a_single_test_via_ai(
                        test_file_relative_path=test_file_relative_path,
                        test_command=test_command,
                        project_root_dir=self.args.test_command_dir,
                    )
                )

        # Update the test command if successfully modified
        if new_command_line:
            args.test_command_original = test_command
            args.test_command = new_command_line
            self.logger.info(
                f"Converting test command: `{test_command}`\n to run only a single test: `{new_command_line}`"
            )

        # Initialize test generator with configuration
        self.test_gen = UnitTestGenerator(
            source_file_path=args.source_file_path,
            test_file_path=args.test_file_output_path,
            project_root=args.project_root,
            code_coverage_report_path=args.code_coverage_report_path,
            test_command=args.test_command,
            test_command_dir=args.test_command_dir,
            included_files=args.included_files,
            coverage_type=args.coverage_type,
            additional_instructions=args.additional_instructions,
            llm_model=args.model,
            use_report_coverage_feature_flag=args.use_report_coverage_feature_flag,
            agent_completion=self.agent_completion,
            generate_log_files=self.generate_log_files,
        )

        # Initialize test validator with configuration
        self.test_validator = UnitTestValidator(
            source_file_path=args.source_file_path,
            test_file_path=args.test_file_output_path,
            project_root=args.project_root,
            code_coverage_report_path=args.code_coverage_report_path,
            test_command=args.test_command,
            test_command_dir=args.test_command_dir,
            included_files=args.included_files,
            coverage_type=args.coverage_type,
            desired_coverage=args.desired_coverage,
            additional_instructions=args.additional_instructions,
            llm_model=args.model,
            use_report_coverage_feature_flag=args.use_report_coverage_feature_flag,
            diff_coverage=args.diff_coverage,
            comparison_branch=args.branch,
            num_attempts=args.run_tests_multiple_times,
            agent_completion=self.agent_completion,
            max_run_time=args.max_run_time,
            generate_log_files=self.generate_log_files,
        )

    def _initialize_ai_caller(self):
        """
        Initialize the appropriate AI caller based on mode and response file availability.

        Returns:
            Union[AICaller, AICallerReplay]: The initialized AI caller instance
        """
        ai_caller_params = {
            "model": self.args.model,
            "api_base": self.args.api_base,
            "max_tokens": 8192,
            "source_file": self.args.source_file_path,
            "test_file": self.args.test_file_path,
            "record_mode": True,
        }
        if self.args.record_mode:
            # In record mode, always use AICaller
            self.logger.info("Initializing AICaller in Record mode...")
            return AICaller(**ai_caller_params)
        else:
            # Try to use replay mode if a response file exists
            try:
                replay_manager = RecordReplayManager(record_mode=False)
                replay_manager.source_file = self.args.source_file_path
                replay_manager.test_file = self.args.test_file_path

                if replay_manager.has_response_file(
                        source_file=self.args.source_file_path, test_file=self.args.test_file_path
                ):
                    self.logger.info("Initializing AICallerReplay (found recorded responses)...")
                    return AICallerReplay(source_file=self.args.source_file_path, test_file=self.args.test_file_path)
            except Exception as e:
                self.logger.debug(f"Failed to initialize replay mode: {e}")

            # Fall back to regular AICaller without recording
            self.logger.info("Initializing AICaller without recording (no recorded responses found)")
            ai_caller_params["record_mode"] = False
            return AICaller(**ai_caller_params)

    def _validate_paths(self):
        """
        Validate all required file paths and initialize the test database.
        
        This method ensures that source files, test files, and project directories exist.
        It also sets up the SQLite database for logging test runs.

        Raises:
            FileNotFoundError: If any required files or directories are missing.
        """
        # Ensure the source file exists
        if not os.path.isfile(self.args.source_file_path):
            raise FileNotFoundError(
                f"Source file not found at {self.args.source_file_path}"
            )
        # Ensure the test file exists
        if not os.path.isfile(self.args.test_file_path):
            raise FileNotFoundError(
                f"Test file not found at {self.args.test_file_path}"
            )

        # Ensure the project root exists
        if self.args.project_root and not os.path.isdir(self.args.project_root):
            raise FileNotFoundError(
                f"Project root not found at {self.args.project_root}"
            )

        # Create default DB file if not provided
        if not self.args.log_db_path:
            self.args.log_db_path = "cover_agent_unit_test_runs.db"
        # Connect to the test DB

        if self.generate_log_files:
            self.test_db = UnitTestDB(db_connection_string=f"sqlite:///{self.args.log_db_path}")

    def _duplicate_test_file(self):
        """
        Create a copy of the test file at the output location if specified.
        
        If no output path is provided, uses the original test file path.
        This allows for non-destructive test generation without modifying the original file.
        """
        # If the test file output path is set, copy the test file there
        if self.args.test_file_output_path != "":
            shutil.copy(self.args.test_file_path, self.args.test_file_output_path)
        else:
            # Otherwise, set the test file output path to the current test file
            self.args.test_file_output_path = self.args.test_file_path

    def init(self):
        """
        Initialize the test generation environment and perform initial analysis.
        
        Sets up Weights & Biases logging if configured and performs initial test suite analysis
        to establish baseline coverage metrics.

        Returns:
            tuple: Contains failed test runs, language detection results, test framework info,
                  and initial coverage report.
        """
        # Check if user has exported the WANDS_API_KEY environment variable
        if "WANDB_API_KEY" in os.environ:
            # Initialize the Weights & Biases run
            wandb.login(key=os.environ["WANDB_API_KEY"])
            time_and_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            run_name = f"{self.args.model}_" + time_and_date
            wandb.init(project="cover-agent", name=run_name)

        # Run initial test suite analysis
        self.test_validator.initial_test_suite_analysis()
        failed_test_runs, language, test_framework, coverage_report = (
            self.test_validator.get_coverage()
        )

        return failed_test_runs, language, test_framework, coverage_report

    def generate_and_validate_tests(self, failed_test_runs, language, test_framework, coverage_report):
        """
        Generate new tests and validate their effectiveness.
        
        Parameters:
            failed_test_runs (list): Previously failed test executions
            language (str): Detected programming language
            test_framework (str): Identified testing framework
            coverage_report (dict): Current coverage metrics
        """
        self.log_coverage()
        generated_tests_dict = self.test_gen.generate_tests(
            failed_test_runs, language, test_framework, coverage_report
        )

        try:
            test_results = [
                self.test_validator.validate_test(test)
                for test in generated_tests_dict.get("new_tests", [])
            ]
            
            # Insert results into database
            if self.has_test_db():
                for result in test_results:
                    result["prompt"] = self.test_gen.prompt
                    self.test_db.insert_attempt(result)
                
        except AttributeError as e:
            self.logger.error(f"Failed to validate the tests within {generated_tests_dict}. Error: {e}")

    def has_test_db(self) -> bool:
        """
        Check if the test database is initialized.

        Returns:
            bool: True if the test database is initialized, False otherwise.
        """
        return hasattr(self, "test_db") and self.test_db is not None

    def check_iteration_progress(self):
        """
        Evaluate current progress towards coverage goals.
        
        Returns:
            tuple: Contains updated test results, language info, framework details,
                  coverage report, and boolean indicating if target is reached.
        """
        failed_runs, lang, framework, report = self.test_validator.get_coverage()
        target_reached = self.test_validator.current_coverage >= (self.test_validator.desired_coverage / 100)
        return failed_runs, lang, framework, report, target_reached

    def finalize_test_generation(self, iteration_count):
        """
        Complete the test generation process and produce final reports.
        
        Parameters:
            iteration_count (int): Number of iterations performed
            
        Side effects:
            - Logs final coverage statistics
            - Generates report file
            - Closes Weights & Biases logging if enabled
            - May exit program if strict coverage requirements not met
        """
        current_coverage = round(self.test_validator.current_coverage * 100, 2)
        desired_coverage = self.test_validator.desired_coverage

        if self.test_validator.current_coverage >= (desired_coverage / 100):
            self.logger.info(
                f"Reached above target coverage of {desired_coverage}% (Current Coverage: {current_coverage}%) in {iteration_count} iterations."
            )
        elif iteration_count == self.args.max_iterations:
            coverage_type = "diff coverage" if self.args.diff_coverage else "coverage"
            failure_message = f"Reached maximum iteration limit without achieving desired {coverage_type}. Current Coverage: {current_coverage}%"
            
            if self.args.strict_coverage:
                self.logger.error(failure_message)
                sys.exit(2)
            else:
                self.logger.info(failure_message)

        # Log token usage
        self.logger.info(
            f"Total number of input tokens used for LLM model {self.args.model}: {self.test_gen.total_input_token_count + self.test_validator.total_input_token_count}"
        )
        self.logger.info(
            f"Total number of output tokens used for LLM model {self.args.model}: {self.test_gen.total_output_token_count + self.test_validator.total_output_token_count}"
        )

        # Only generate report if file generation is enabled
        if self.generate_log_files:
            # Generate report and cleanup
            self.test_db.dump_to_report(self.args.report_filepath)

        if "WANDB_API_KEY" in os.environ:
            wandb.finish()

    def log_coverage(self):
        """Log current coverage metrics, differentiating between diff coverage and full coverage."""
        if self.args.diff_coverage:
            self.logger.info(
                f"Current Diff Coverage: {round(self.test_validator.current_coverage * 100, 2)}%"
            )
        else:
            self.logger.info(
                f"Current Coverage: {round(self.test_validator.current_coverage * 100, 2)}%"
            )
        self.logger.info(f"Desired Coverage: {self.test_validator.desired_coverage}%")

    def run(self):
        """
        Execute the main test generation loop until coverage goals are met or iterations exhausted.
        
        The process involves:
        1. Initializing the environment
        2. Repeatedly generating and validating tests
        3. Checking progress after each iteration
        4. Finalizing and reporting results
        """
        iteration_count = 0
        failed_test_runs, language, test_framework, coverage_report = self.init()

        while iteration_count < self.args.max_iterations:
            self.generate_and_validate_tests(failed_test_runs, language, test_framework, coverage_report)
            
            failed_test_runs, language, test_framework, coverage_report, target_reached = self.check_iteration_progress()
            if target_reached:
                break
                
            iteration_count += 1

        self.finalize_test_generation(iteration_count)
