import asyncio
import copy

from cover_agent.ai_caller import AICaller
from cover_agent.cover_agent import CoverAgent
from cover_agent.lsp_logic.ContextHelper import ContextHelper
from cover_agent.settings.config_loader import get_settings
from cover_agent.settings.config_schema import CoverAgentConfig
from cover_agent.utils import find_test_files, parse_args_full_repo


async def run():
    settings = get_settings().get("default")
    args = parse_args_full_repo(settings)

    if args.project_language == "python":
        context_helper = ContextHelper(args)
    else:
        raise NotImplementedError("Unsupported language: {}".format(args.project_language))

    # scan the project directory for test files
    test_files = find_test_files(args)
    print("============\nTest files to be extended:\n" + "".join(f"{f}\n============\n" for f in test_files))

    # start the language server
    async with context_helper.start_server():
        print("LSP server initialized.")

        generate_log_files = not args.suppress_log_files
        api_base = getattr(args, "api_base", "")
        ai_caller = AICaller(model=args.model, api_base=api_base, generate_log_files=generate_log_files)

        # main loop for analyzing test files
        for test_file in test_files:
            # Find the context files for the test file
            context_files = await context_helper.find_test_file_context(test_file)
            print("Context files for test file '{}':\n{}".format(test_file, "".join(f"{f}\n" for f in context_files)))

            # Analyze the test file against the context files
            print("\nAnalyzing test file against context files...")
            source_file, context_files_include = await context_helper.analyze_context(
                test_file, context_files, ai_caller
            )

            if source_file:
                try:
                    # Run the CoverAgent for the test file
                    args_copy = copy.deepcopy(args)
                    args_copy.source_file_path = source_file
                    args_copy.test_command_dir = args.project_root
                    args_copy.test_file_path = test_file
                    args_copy.included_files = context_files_include

                    config = CoverAgentConfig.from_cli_args_with_defaults(args_copy)
                    agent = CoverAgent(config)
                    agent.run()
                except Exception as e:
                    print(f"Error running CoverAgent for test file '{test_file}': {e}")
                    pass


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
