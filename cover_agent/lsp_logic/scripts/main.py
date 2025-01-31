import argparse
import asyncio
import os
from time import sleep

from grep_ast import filename_to_lang

from cover_agent.lsp_logic.multilspy import LanguageServer
from cover_agent.lsp_logic.file_map.file_map import FileMap
from cover_agent.lsp_logic.multilspy.multilspy_config import MultilspyConfig
from cover_agent.lsp_logic.multilspy.multilspy_logger import MultilspyLogger


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Process project directory and relative file path."
    )
    parser.add_argument(
        "--project_dir", type=str, help="The project directory path.", default="./"
    )
    parser.add_argument(
        "--rel_file",
        type=str,
        help="The relative file path.",
        default="cover_agent/UnitTestGenerator.py",
    )
    parser.add_argument(
        "--project-language",
        type=str,
        help="The language of the file.",
        default="python",
    )
    return parser.parse_args()


async def run():
    # parse arguments
    args = parse_arguments()
    project_dir = args.project_dir
    if args.project_dir == "./":  # convert relative path to absolute path
        project_dir = os.getcwd()
    rel_file = args.rel_file
    print(
        f"Running context analysis for the file '{rel_file}' in the project '{project_dir}'..."
    )

    language = filename_to_lang(rel_file)
    target_file = str(os.path.join(project_dir, rel_file))
    config = MultilspyConfig.from_dict({"code_language": language})
    if not os.path.exists(target_file):
        print(f"File {target_file} does not exist")
        exit(1)

    # get tree-sitter query results
    print("\nGetting tree-sitter query results for the target file...")
    fname_summary = FileMap(
        target_file,
        parent_context=False,
        child_context=False,
        header_max=0,
        project_base_path=project_dir,
    )
    query_results, captures = fname_summary.get_query_results()
    print("Tree-sitter query results for the target file done.")

    # initialize LSP server
    print("\nInitializing LSP server...")
    logger = MultilspyLogger()
    lsp = LanguageServer.create(config, logger, project_dir)
    sleep(0.1)

    async with lsp.start_server():
        print("LSP server initialized.")

        print("\nGetting context ...")
        context_files, context_symbols = await lsp.get_direct_context(
            captures, language, project_dir, rel_file
        )
        print("Getting context done.")

        print("\nGetting reverse context ...")
        reverse_context_files, reverse_context_symbols = await lsp.get_reverse_context(
            captures, project_dir, rel_file
        )
        print("Getting reverse context done.")

    print("\n\n================")
    print(
        f"For the file '{target_file}', here are the files referenced by it (context):\n"
    )
    for file in context_files:
        print(f"'{file}'")
    print("\n\n================")
    print(
        f"For the file '{target_file}', here are the files referencing it (reverse context):\n"
    )
    for file in reverse_context_files:
        print(f"'{file}'")
    print("================")
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(run())
