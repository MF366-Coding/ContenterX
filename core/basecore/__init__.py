from screen import context, Screen, formatting
import os
import sys
import PIL
from typing import Any

filebrowser_formatter = formatting.Formatter(True, {})


def test_path(path: str, supposed_file: bool = False) -> bool:
    test1 = os.path.exists(path)
    test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
    test3 = os.path.exists(os.path.abspath(path))
    
    return all((test1, test2, test3))
    

class PhotoViewer(context.Context):
    

class FileBrowser(context.Context):
    def __init__(self, value, initial_directory: str = '~', keyword_formatters = None, title = None):
        if initial_directory == '~':
            self._directory = os.path.expanduser('~')
        
        super().__init__(value, keyword_formatters, title)
    
    def handle_value(self, id, value) -> tuple[str, Any]:
        match id:
            case 'Please input a path: ':
                # [i] it must pass all the path tests
                if test_path(value):
                    
        
        return super().handle_value(id, value)
    
    def handle_hierarchy(self)