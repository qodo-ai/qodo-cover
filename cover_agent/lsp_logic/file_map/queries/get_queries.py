import os
from pathlib import Path


def get_queries_scheme(lang: str) -> str:
    try:
        # Load the relevant queries
        curr_path = Path(__file__).parent
        path = os.path.join(curr_path, f"tree-sitter-{lang}-tags.scm")
        with open(path, "r") as f:
            return f.read()
    except KeyError:
        return ""
