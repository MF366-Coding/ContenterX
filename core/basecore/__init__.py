from screen import context, Screen
from screen.formatting import *
import os
import sys
import PIL
from typing import Any
from NCapybaraLib import String as string

# [<] why the fuck is this up here?
filebrowser_formatter = Formatter(True, {})


def test_path(path: str, supposed_file: bool = False, method_mode: int = 0) -> bool:
    """
    ## test_path

    Test the path using 3 different tests.

    ### About Method Modes
    - 0: All three tests are performed:
        1. Check if the path exists.
        2. Check if the path is a file (if supposed_file is True) or a directory (if supposed_file is False).
        3. Check if the absolute path exists.
    - 1: Only the existence tests are performed:
        1. Check if the path exists.
        2. Always True.
        3. Check if the absolute path exists.
    - 2: Existence and type tests are performed:
        1. Check if the path exists.
        2. Check if the path is a file (if supposed_file is True) or a directory (if supposed_file is False).
        3. Always True.
    - 3: Type test is performed:
        1. Always True.
        2. Check if the path is a file (if supposed_file is True) or a directory (if supposed_file is False).
        3. Always True.
    
    :param str path: the path of the directory or file to test
    :param bool supposed_file: to interpret this path as a file or a directory, defaults to False (interpret as a directory)
    :param int method_mode: the mode of the method to use for testing the path, defaults to 0
    :return bool: whether the path passed all tests (True) or failed at least one (False)
    """
    
    match method_mode:
        case 0:
            test1 = os.path.exists(path)
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
            test3 = os.path.exists(os.path.abspath(path))
            
        case 1:
            test1 = os.path.exists(path)
            test2 = True
            test3 = os.path.exists(os.path.abspath(path))
            
        case 2:
            test1 = os.path.exists(path)
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
            test3 = True
            
        case 3:
            test1 = test3 = True
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
                
    return all((test1, test2, test3))


def sort_files_by_criteria(list_of_paths: list[str], criteria: str = 'AZ'):
    match criteria:
        case 'ZA':
            list_of_paths.sort(reverse=True)
        
        case 'time-up':
            list_of_paths.sort(key=lambda i: os.path.getctime(i))
        
        case 'time-down':
            list_of_paths.sort(key=lambda i: os.path.getctime(i), reverse=True)
            
        case 'size-up':
            list_of_paths.sort(key=lambda i: os.path.getsize(i))
        
        case 'size-down':
            list_of_paths.sort(key=lambda i: os.path.getsize(i), reverse=True)
        
        case 'tch-up':
            list_of_paths.sort(key=lambda i: os.path.getmtime(i))
        
        case 'tch-down':
            list_of_paths.sort(key=lambda i: os.path.getmtime(i), reverse=True)
            
        case 'tac-up':
            list_of_paths.sort(key=lambda i: os.path.getatime(i))
        
        case 'tac-down':
            list_of_paths.sort(key=lambda i: os.path.getatime(i), reverse=True)
            
        case _:
            list_of_paths.sort()


class FileBrowser(context.Context):
    """
    # FileBrowser
    
    The FileBrowser class provides a terminal-based file browsing interface. It allows users to navigate
    directories, view files, and access quick access items. The class supports different rendering methods
    and sorting orders for displaying directory contents.
    
    **The parameters below are used with __init__ to create a FileBrowser object, that is, to initialize it.**

    :param Screen screen: The screen object where the file browser will be rendered.
    :param tuple[str] quick_access_items: A tuple of paths for quick access items. Defaults to only 1 quick access item, which is the user's home directory.
    :param keyword_formatters: Optional keyword formatters for customizing the display.
    :param title: Optional title for the file browser interface.
    """

    def __init__(self, screen: Screen, quick_access_items: tuple[str] | None = None, keyword_formatters = None, title = None):        
        """
        ## Initialization for FileBrowser class (__init__)
        
        Initializes the FileBrowser class with the provided parameters. Sets up the screen, quick access items,
        rendering method, rendering order, and current directory. Also prepares the quick access field values
        and file browser field for display.

        :param Screen screen: The screen object where the file browser will be rendered.
        :param tuple[str] quick_access_items: A tuple of paths for quick access items. Defaults to the user's home directory if not provided.
        :param keyword_formatters: Optional keyword formatters for customizing the display.
        :param title: Optional title for the file browser interface.
        """
        
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
    
    def highlight_based_on_designation(self, designations: dict[str, list[str]]) -> dict[str, list[str]]:
        """
        ## FileBrowser.highlight_based_on_designation

        This function takes a dictionary where the keys are designations (e.g., 'folder', 'file', etc.)
        and the values are lists of strings representing items. It returns a dictionary with the same
        keys, but the items are formatted with ANSI escape codes for terminal highlighting.
        
        :param dict[str, list[str]] designations: A dictionary with designations as keys and lists of item names as values.
        :return dict[str, list[str]]: A dictionary with the same keys, but the item names are formatted with ANSI escape codes.
        """
        
        spam = {'folder': [], 'file': [], "symlink": [], 'mountpoint': [], 'other': []}
        
        for k, v in designations.items():
            for i in v:
                match k:
                    case 'folder':
                        spam['folder'].append(f"{Fore.BLUE}{i}{Fore.RESET}")
                        
                    case 'file':
                        spam['file'].append(f"{Fore.GREEN}{i}{Fore.RESET}")
                        
                    case 'symlink':
                        spam['symlink'].append(f"{set_effect(Effect.BOLD)}{i}{set_effect(Effect.RESET_BOLD)}")       
                        
                    case "mountpoint":
                        spam['mountpoint'].append(f"{Fore.RED}{i}{Fore.RESET}")
                        
                    case 'other':
                        spam['other'].append(f"{set_effect(Effect.UNDERLINE)}{Fore.YELLOW}{i}{set_effect(Effect.RESET_UNDERLINED)}{Fore.RESET}")
        
        return spam
    
    def get_file_browser_ready(self):
        """
        ## FileBrowser.get_file_browser_ready
        
        This function retrieves the current directory contents, classifies them into
        designations (e.g., 'mountpoint', 'folder', 'file', 'symlink', 'other'), and
        sorts them based on specified criteria. The sorted items are then formatted
        with ANSI escape codes for terminal highlighting.
        
        :return: None
        """
        
        self._cur_dir_content = ['..'] + os.listdir(self._cur_dir)
        designations = self.get_designation_based_on_element_type()
        
        sorted_mountpoints = sort_files_by_criteria(designations['mountpoint']) # [i] mountpoints are always sorted by name
                                                                                    # [i] because they don't have any other criteria to sort by

        sorted_folders = sort_files_by_criteria(designations['folder'], self._rendering_order)
        sorted_files_and_links = sort_files_by_criteria(designations['file'] + designations['symlink'] + designations['other'], self._rendering_order)
    
    
    def get_quick_access_ready(self):
        raise NotImplementedError(self.__doc__)
    
    def draw_to_screen(self):
        self.SCREEN.writelines(self._lines)        
    
    def get_designation_based_on_element_type(self) -> dict[str, list[str]]:
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
        raise NotImplementedError(self.__doc__)
        