"""
Defines the settings for multilspy.
"""

import os
import pathlib


class MultilspySettings:
    """
    Provides the various settings for multilspy.
    """

    @staticmethod
    def get_language_server_directory() -> str:
        """Returns the directory for language servers"""
        user_home = pathlib.Path.home()
        multilspy_dir = str(pathlib.PurePath(user_home, ".multilspy"))
        lsp_dir = str(pathlib.PurePath(multilspy_dir, "lsp"))
        os.makedirs(lsp_dir, exist_ok=True)
        return lsp_dir

    @staticmethod
    def get_global_cache_directory() -> str:
        """Returns the cache directory"""
        global_cache_dir = os.path.join(
            str(pathlib.Path.home()), ".multilspy", "global_cache"
        )
        os.makedirs(global_cache_dir, exist_ok=True)
        return global_cache_dir
