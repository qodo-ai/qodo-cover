import datetime
import os
import shutil
import sys
import wandb

from typing import List

from cover_agent.CustomLogger import CustomLogger
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.UnitTestValidator import UnitTestValidator
from cover_agent.UnitTestDB import UnitTestDB
from cover_agent.AICaller import AICaller
from cover_agent.AgentCompletionABC import AgentCompletionABC
from cover_agent.DefaultAgentCompletion import DefaultAgentCompletion


class CoverAgent:
    def __init__(self, args, agent_completion: AgentCompletionABC = None):
        """
        Initialize the CoverAgent class with the provided arguments and run the test generation process.

        Parameters:
            args (Namespace): The parsed command-line arguments containing necessary information for test generation.

        Returns:
            None
        """
        self.args = args
        self.logger = CustomLogger.get_logger(__name__)

        self._validate_paths()
        self._duplicate_test_file()

        # Configure the AgentCompletion object
        if agent_completion:
            self.agent_completion = agent_completion
        else:
            # Default to using the DefaultAgentCompletion object with AICaller
            self.ai_caller = AICaller(
                model=args.model, api_base=args.api_base, max_tokens=8192
            )
            self.agent_completion = DefaultAgentCompletion(caller=self.ai_caller)

        # To run only a single test file, we need to modify the test command
        test_command = args.test_command
        new_command_line = None
        if hasattr(args, "run_each_test_separately") and args.run_each_test_separately:
            test_file_relative_path = os.path.relpath(
                args.test_file_output_path, args.project_root
            )
            if "pytest" in test_command:
                try:
                    ind1 = test_command.index("pytest")
                    ind2 = test_command[ind1:].index("--")
                    new_command_line = f"{test_command[:ind1]}pytest {test_file_relative_path} {test_command[ind1 + ind2:]}"
                except ValueError:
                    print(
                        f"Failed to adapt test command for running a single test: {test_command}"
                    )
            else:
                new_command_line, _, _, _ = (
                    self.agent_completion.adapt_test_command_for_a_single_test_via_ai(
                        test_file_relative_path=test_file_relative_path,
                        test_command=test_command,
                        project_root_dir=self.args.test_command_dir,
                    )
                )
        if new_command_line:
            args.test_command_original = test_command
            args.test_command = new_command_line
            print(
                f"Converting test command: `{test_command}`\n to run only a single test: `{new_command_line}`"
            )

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
        )

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
        )

    def _validate_paths(self):
        """
        Validate the paths provided in the arguments.

        Raises:
            FileNotFoundError: If the source file or test file is not found at the specified paths.
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
        self.test_db = UnitTestDB(
            db_connection_string=f"sqlite:///{self.args.log_db_path}"
        )

    def _duplicate_test_file(self):
        """
        Initialize the CoverAgent class with the provided arguments and run the test generation process.

        Parameters:
            args (Namespace): The parsed command-line arguments containing necessary information for test generation.

        Returns:
            None
        """
        # If the test file output path is set, copy the test file there
        if self.args.test_file_output_path != "":
            shutil.copy(self.args.test_file_path, self.args.test_file_output_path)
        else:
            # Otherwise, set the test file output path to the current test file
            self.args.test_file_output_path = self.args.test_file_path

    def init(self):
        """
        Prepare for test generation process

        1. Initialize the Weights & Biases run if the WANDS_API_KEY environment variable is set.
        2. Initialize variables to track progress.
        3. Run the initial test suite analysis.

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

    def _generate_and_validate_tests(self, failed_test_runs, language, test_framework, coverage_report):
        """Generate new tests and validate them using list comprehension."""
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
            for result in test_results:
                result["prompt"] = self.test_gen.prompt
                self.test_db.insert_attempt(result)
                
        except AttributeError as e:
            self.logger.error(f"Failed to validate the tests within {generated_tests_dict}. Error: {e}")

    def _check_iteration_progress(self):
        """Check coverage progress and return info needed for next iteration."""
        failed_runs, lang, framework, report = self.test_validator.get_coverage()
        target_reached = self.test_validator.current_coverage >= (self.test_validator.desired_coverage / 100)
        return failed_runs, lang, framework, report, target_reached

    def _finalize_test_generation(self, iteration_count):
        """Handle final logging, reporting and cleanup."""
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

        # Generate report and cleanup
        self.test_db.dump_to_report(self.args.report_filepath)
        if "WANDB_API_KEY" in os.environ:
            wandb.finish()

    def log_coverage(self):
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
        """Main execution loop for test generation."""
        iteration_count = 0
        failed_test_runs, language, test_framework, coverage_report = self.init()

        while iteration_count < self.args.max_iterations:
            self._generate_and_validate_tests(failed_test_runs, language, test_framework, coverage_report)
            
            failed_test_runs, language, test_framework, coverage_report, target_reached = self._check_iteration_progress()
            if target_reached:
                break
                
            iteration_count += 1

        self._finalize_test_generation(iteration_count)
