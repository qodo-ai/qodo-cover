import os
from time import sleep

from jinja2 import Environment, StrictUndefined

from cover_agent.lsp_logic.file_map.file_map import FileMap
from cover_agent.lsp_logic.multilspy import LanguageServer
from cover_agent.lsp_logic.multilspy.multilspy_config import MultilspyConfig
from cover_agent.lsp_logic.multilspy.multilspy_logger import MultilspyLogger

from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import load_yaml


async def analyze_context(test_file, context_files, args, ai_caller):
    """
    # we now want to analyze the test file against the source files and determine several things:
    # 1. If this test file is a unit test file
    # 2. Which of the context files can be seen as the main source file for this test file, for which we want to increase coverage
    # 3. Set all other context files as additional 'included_files' for the CoverAgent
    """
    source_file = None
    context_files_include = context_files
    try:
        test_file_rel_str = os.path.relpath(test_file, args.project_root)
        context_files_rel_filtered_list_str = ""
        for file in context_files:
            context_files_rel_filtered_list_str += (
                f"`{os.path.relpath(file, args.project_root)}\n`"
            )
        variables = {
            "language": args.project_language,
            "test_file_name_rel": test_file_rel_str,
            "test_file_content": open(test_file, "r").read(),
            "context_files_names_rel": context_files_rel_filtered_list_str,
        }
        environment = Environment(undefined=StrictUndefined)
        system_prompt = environment.from_string(
            get_settings().analyze_test_against_context.system
        ).render(variables)
        user_prompt = environment.from_string(
            get_settings().analyze_test_against_context.user
        ).render(variables)
        response, prompt_token_count, response_token_count = ai_caller.call_model(
            prompt={"system": system_prompt, "user": user_prompt}, stream=False
        )
        response_dict = load_yaml(response)
        if int(response_dict.get("is_this_a_unit_test", 0)) == 1:
            source_file_rel = response_dict.get("main_file", "").strip().strip("`")
            source_file = os.path.join(args.project_root, source_file_rel)
            for file in context_files:
                file_rel = os.path.relpath(file, args.project_root)
                if file_rel == source_file_rel:
                    context_files_include = [f for f in context_files if f != file]

        if source_file:
            print(
                f"Test file: `{test_file}`,\nis a unit test file for source file: `{source_file}`"
            )
        else:
            print(f"Test file: `{test_file}` is not a unit test file")
    except Exception as e:
        print(f"Error while analyzing test file {test_file} against context files: {e}")

    return source_file, context_files_include


async def find_test_file_context(args, lsp, test_file):
    try:
        target_file = test_file
        rel_file = os.path.relpath(target_file, args.project_root)

        # get tree-sitter query results
        # print("\nGetting tree-sitter query results for the target file...")
        fname_summary = FileMap(
            target_file,
            parent_context=False,
            child_context=False,
            header_max=0,
            project_base_path=args.project_root,
        )
        query_results, captures = fname_summary.get_query_results()
        # print("Tree-sitter query results for the target file done.")

        # print("\nGetting context ...")
        context_files, context_symbols = await lsp.get_direct_context(
            captures, args.project_language, args.project_root, rel_file
        )
        # filter empty files
        context_files_filtered = []
        for file in context_files:
            with open(file, "r") as f:
                if f.read().strip():
                    context_files_filtered.append(file)
        context_files = context_files_filtered
        # print("Getting context done.")
    except Exception as e:
        print(f"Error while getting context for test file {test_file}: {e}")
        context_files = []

    return context_files


async def initialize_language_server(args):
    logger = MultilspyLogger()
    config = MultilspyConfig.from_dict({"code_language": args.project_language})
    if args.project_language == "python":
        lsp = LanguageServer.create(config, logger, args.project_root)
        sleep(0.1)
        return lsp
    else:
        raise NotImplementedError(
            "Unsupported language: {}".format(args.project_language)
        )
