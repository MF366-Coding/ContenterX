from screen import context, Screen, formatting
import os
import sys
import PIL
from typing import Any
from NCapybaraLib import String as string

# [<] why the fuck is this up here?
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


def sort_files_by_criteria(list_of_paths: list[str], criteria: str = 'AZ'):
    match criteria:
        case 'ZA':
            # Placeholder for sorting alphabetically Z-A
            pass
        
        case 'time-up':
            list_of_times = [os.path.getctime() for i in list_of_paths]
        
        case 'time-down':
            # Placeholder for sorting by creation time descending
            pass
        case 'size-up':
            # Placeholder for sorting by size ascending
            pass
        case 'size-down':
            # Placeholder for sorting by size descending
            pass
        case 'tch-up':
            # Placeholder for sorting by last change time ascending
            pass
        case 'tch-down':
            # Placeholder for sorting by last change time descending
            pass
        case 'tac-up':
            # Placeholder for sorting by last access time ascending
            pass
        case 'tac-down':
            # Placeholder for sorting by last access time descending
            pass
        case _:
            # Placeholder for default sorting (if criteria doesn't match any case)
            pass


class FileBrowser(context.Context):
    def __init__(self, screen, quick_access_items: tuple[str] | None = None, keyword_formatters = None, title = None):
        self.SCREEN = screen
                
        self._rendering_method = 'list' # [i] can be "grid" or "list"
        self._rendering_order = 'AZ' # [i] can be "AZ", "ZA", "time-up", "time-down", "size-up", "size-down", "tch-up", "tch-down", "tac-up", "tac-down"
                                     # [i] "AZ" and "ZA" are for alphabetical order
                                     # [i] "time-up" and "time-down" are for time of creation
                                     # [i] "size-up" and "size-down" are for size of the file
                                     # [i] "tch-up" and "tch-down" are for time of last change
                                     # [i] "tac-up" and "tac-down" are for time of last access
                                     # [<] now who the fuck thought these alias would be a good idea?
        self._selection = 0
        self._cur_dir = os.getcwd()
        
        if not quick_access_items:
            quick_access_items = (os.path.expanduser('~'), os.path.expanduser('~'))
        
        self._quick_access_field_values = [f"({i + 1}) {quick_access_items[i] if len(quick_access_items[i]) < 28 else f'{quick_access_items[i][:25]}...'}" for i in range(0, min(len(quick_access_items), 25))]
        self._quick_access_field = ["╔==========================╗", "║                          ║", "╠====== Quick Access ======╣", "║                          ║"]
        self._file_browser_field = ["╔==================================================================╗", "║                                                                  ║", "╠========================== File Browser ==========================╣", "║                                                                  ║"]
        self._details_field = None # TODO

        self._cur_dir_content = ['..'] + os.listdir(self._cur_dir)
        
        value = None
        
        super().__init__(screen, value, keyword_formatters, title)
    
    def get_file_browser_ready(self):
        self._cur_dir_content = ['..'] + os.listdir(self._cur_dir)
        designations = self.get_designation_based_on_element_type()
        
        sorted_mountpoints = designations['mountpoint']
        
        
        # [i] the order is gonna be: mountpoints, folders, <everything else ordered by self._rendering_order>
        sorted_files_and_links = [j for j in designations[i] for i in ('file', 'symlink', 'other')]
        
        
    
    def get_quick_access_ready()
    
    def draw_to_screen(self):
        self.SCREEN.writelines(self._lines)        
    
    def get_designation_based_on_element_type(self):
        eggs = {'folder': [], 'file': [], "symlink": [], 'mountpoint': [], 'other': []}
        
        for i in self._cur_dir_content:
            if i == '..':
                eggs['folder'].append('..')
                continue
                
            if os.path.isdir(i):
                eggs['folder'].append(os.path.relpath(i))
                continue
            
            if os.path.islink(i):
                eggs['symlink'].append(os.path.relpath(i))
                continue
            
            if os.path.ismount(i):
                eggs['mountpoint'].append(os.path.relpath(i))
                continue
            
            if os.path.isfile(i):
                eggs['file'].append(os.path.relpath(i))
                continue
            
            eggs['other'].append(os.path.relpath(i))
                
        return eggs
    
    def highlight_selection(self):
        