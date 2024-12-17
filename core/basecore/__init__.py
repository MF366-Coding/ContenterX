from screen import context, Screen, formatting
import os
import sys
import PIL
from typing import Any

filebrowser_formatter = formatting.Formatter(True, {})


def test_path(path: str, supposed_file: bool = False) -> bool:
    """
    ## test_path

    Test the path using 3 different tests.

    :param str path: the path of the directory or file to test
    :param bool supposed_file: to interpret this path as a file or a directory, defaults to False (interpret as a directory)
    :return bool: whether the path passed all tests (True) or failed at least one (False)
    """
    
    test1 = os.path.exists(path)
    test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
    test3 = os.path.exists(os.path.abspath(path))
    
    return all((test1, test2, test3))


class FileBrowser(context.Context):
    def __init__(self, screen, quick_access_items: tuple[str] | None = None, keyword_formatters = None, title = None):
        self._SELECTION
        
        if not quick_access_items:
            quick_access_items = (os.path.expanduser('~'), os.path.expanduser('~'))
        
        self._quick_access_field_values = [f"({i + 1}) {quick_access_items[i] if len(quick_access_items[i]) < 28 else f'{quick_access_items[i][:25]}...'}" for i in range(0, min(len(quick_access_items), 25))]
        self._quick_access_field = ["╔==========================╗", "║                          ║", "╠====== Quick Access ======╣", "║                          ║"]
        self._file_browser_field = ["╔==========================╗", "║                          ║", "╠====== File Browser ======╣", "║                          ║"]
        
        spam = os.listdir(os.getcwd())
    
        self._cur_dir_content: list[list[str | int], list[str | int]] = [['..'] + [i if os.path.isdir(i) else 4 for i in spam], [i if os.path.isfile(i) else 4 for i in spam]]
        
        for _ in range(self._cur_dir_content[0].count(4)):
            self._cur_dir_content[0].remove(4)
            
        for _ in range(self._cur_dir_content[1].count(4)):
            self._cur_dir_content[1].remove(4)
            
        del spam       
        
        value = None
        
        super().__init__(screen, value, keyword_formatters, title)