import asyncio
import copy
import os
from cover_agent.AICaller import AICaller
from cover_agent.utils import parse_args_full_repo, find_test_files
from cover_agent.CoverAgent import CoverAgent
from cover_agent.lsp_logic.ContextHelper import ContextHelper


async def run():
    args = parse_args_full_repo()

    if args.project_language == "python":
        context_helper = ContextHelper(args)
    else:
        raise NotImplementedError(
            "Unsupported language: {}".format(args.project_language)
        )

    # scan the project directory for test files
    test_files = find_test_files(args)
    print(
        "============\nTest files to be extended:\n"
        + "".join(f"{f}\n============\n" for f in test_files)
    )

    # start the language server
    async with context_helper.start_server():
        print("LSP server initialized.")

        ai_caller = AICaller(model=args.model)

        # main loop for analyzing test files
        for test_file in test_files:
            # Find the context files for the test file
            context_files = await context_helper.find_test_file_context(test_file)
            print(
                "Context files for test file '{}':\n{}".format(
                    test_file, "".join(f"{f}\n" for f in context_files)
                )
            )

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
                    agent = CoverAgent(args_copy)
                    agent.run()
                except Exception as e:
                    print(f"Error running CoverAgent for test file '{test_file}': {e}")
                    pass


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
