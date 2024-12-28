from screen import context, Screen
from screen.formatting import Formatter, set_effect, Effect, set_viewport_title, wipe_line, clear_viewport, change_cursor_visibility, Fore, Back, Cursor
import os
import sys
import PIL
from typing import Any
from NCapybaraLib import String as string
from difflib import SequenceMatcher

# [<] why the fuck is this up here?
filebrowser_formatter = Formatter(True, {})


def are_strings_similar(given_string: str, match: str, optimization_level: int = 3):
    """
    ## are_strings_similar
    
    Determine if two strings are similar based on a given optimization level using the SequenceMatcher algorithm.
    
    The SequenceMatcher algorithm is used to compare pairs of sequences. It calculates a similarity ratio based on the number of matching blocks between the sequences.
    
    Optimization levels:
        - 0: Very unoptimized - slow - finds the average between ALL the ratios.
        - 1: Unoptimized - finds the average between the quickest ratios.
        - 2: Slightly unoptimized - uses the full ratio calculation.
        - 3: Recommended optimization - uses the quick ratio.
        - 4: Way too optimized - may return a very distant upper bound using the real quick ratio.

    :param str given_string: The first string to compare.
    :param str match: The second string to compare.
    :param int optimization_level: The level of optimization to use for the comparison (default is 3).
    :return float: The similarity ratio between the two strings.
    """
    
    seq_matcher = SequenceMatcher(None, given_string, match)
   
    match optimization_level:
        case 0: # [i] very unoptimized - slow as fuck - finds the average between ALL the ratios
            ratio = (seq_matcher.real_quick_ratio() + seq_matcher.quick_ratio() + seq_matcher.ratio()) / 3
        
        case 1: # [i] unoptimized, finds the average between the quickest ratios
            ratio = (seq_matcher.real_quick_ratio() + seq_matcher.quick_ratio()) / 2
        
        case 2: # [i] slightly unoptimized
            ratio = seq_matcher.ratio()
            
        case 3: # [i] recommended optimization
            ratio = seq_matcher.quick_ratio()

        case 4: # [i] way too optimized lol - may return a very distant upper bound like 1.0 to a value that would be 0.75
            ratio = seq_matcher.real_quick_ratio()
            
        case _:
            _ = seq_matcher.get_matching_blocks()
            ratio = seq_matcher.ratio()
            del _
            
    return ratio


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


class Protocol:
    '''
    # Protocol Class
    A class to manage and execute protocols. It allows registering protocols with associated functions
    and running them with provided arguments.

    ## Methods
    - `register(protocol: str, function: Any)`: Registers a protocol with a function.
    - `run_protocol(protocol: str, *args, **kwargs)`: Runs a protocol with the provided arguments.
    - `__str__()`: Returns a string representation of the protocols.
    - `__len__()`: Returns the number of protocols registered.
    '''

    def __init__(self, screen: Screen):
        """
        ## Initialization for Protocol class (__init__)

        Initializes the instance with an empty dictionary for protocols.

        :param Screen screen: The screen object where the protocol will be executed.
        :attribute dict _protocols: A dictionary to store protocol-related information.
        """

        self._SCREEN = screen
        self._protocols: dict[str, Any] = {}

    def register(self, protocol: str, function: Any):
        self._protocols[protocol] = function

    def run_protocol(self, protocol: str, *args, **kwargs):
        ctx, curated_dict = self._protocols[protocol](*args, **kwargs)
        ctx.handle_protocol(protocol, **curated_dict)
        return self._SCREEN.change_context(ctx)

    def __str__(self):
        return str(self._protocols)

    def __len__(self):
        return len(self._protocols)


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
        self._search_method = 0 # [i] 0 for regular search, uses Norb's String Similarity Algorithm
                                # [i] 1 for strict search, must match exactly
                                # [i] 2 for regex search, uses Python's built-in regex engine
                                # [i] 3 for fuzzy search, uses fuzzywuzzy's algorithm
                                # [i] 4 for the SequenceMatcher algorithm, opti0
                                # [i] 5 for the SequenceMatcher algorithm, opti1
                                # [i] 6 for the SequenceMatcher algorithm, opti2
                                # [i] 7 for the SequenceMatcher algorithm, opti3
                                # [i] 8 for the SequenceMatcher algorithm, opti4
                                # [i] 9 for the SequenceMatcher algorithm, optiANY
                                # [<] btw optiX means "optimization level X"
                                # [<] which makes optiANY any other level that isn't 0, 1, 2, 3 or 4

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

    def highlight_based_on_designation(self, designation: str, data: list[str]) -> list[str]:
        """
        ## FileBrowser.highlight_based_on_designation

        This function takes a designation (e.g., 'folder', 'file', etc.) and a list of strings representing items.
        It returns a list of strings where each item is formatted with ANSI escape codes for terminal highlighting.

        :param str designation: The designation of the items (e.g., 'folder', 'file', etc.).
        :param list[str] data: A list of item names to be highlighted.
        :return list[str]: A list of item names formatted with ANSI escape codes.
        """

        match designation:
            case 'mountpoint':
                spam = [f"{Fore.RED}{i}{Fore.RESET}" for i in data]
                
            case 'folder':
                spam = [f"{Fore.BLUE}{i}{Fore.RESET}" for i in data]
            
            case 'file':
                spam = [f"{Fore.GREEN}{i}{Fore.RESET}" for i in data]
                
            case 'symlink':
                spam = [f"{set_effect(Effect.BOLD)}{i}{set_effect(Effect.RESET_BOLD)}" for i in data]
                
            case 'other':
                spam = [f"{set_effect(Effect.UNDERLINE)}{Fore.YELLOW}{i}{set_effect(Effect.RESET_UNDERLINED)}{Fore.RESET}" for i in data]

            case _: # [<] any other value that I did not ask for? well, fuck you; you're getting nothing but unformatted shit from me
                spam = data.copy() # [<] thou shallt remain UNFORMATTED!

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

        # [*] Listing the contents of the current directory
        self._cur_dir_content: list[str] = ['..'] + [os.path.relpath(i) for i in os.listdir(self._cur_dir)]
        designations: dict[str, list[str]] = self.get_designation_based_on_element_type()

        # [*] Sorting the contents of the same directory
        sorted_mountpoints: list[str] = self.highlight_based_on_designation('mountpoint', sort_files_by_criteria(designations['mountpoint'])) # [i] mountpoints are always sorted by name
                                                                                    # [i] because they don't have any other criteria to sort by
        sorted_folders: list[str] = self.highlight_based_on_designation('folder', sort_files_by_criteria(designations['folder'], self._rendering_order))
        sorted_files: list[str] = self.highlight_based_on_designation('file', sort_files_by_criteria(designations['file'], self._rendering_order))
        sorted_symlinks: list[str] = self.highlight_based_on_designation('symlink', sort_files_by_criteria(designations['symlink'], self._rendering_order))
        sorted_others: list[str] = self.highlight_based_on_designation('other', sort_files_by_criteria(designations['other'], self._rendering_order))
        
        sorted_contents: list[str] = sorted_mountpoints + sorted_folders + sorted_files + sorted_symlinks + sorted_others # [i] we now combine all of these into one list
        
        # [*] Setting up the grid/list mechanic
            # [i] List is very simple, as we just place each file/folder/whatever below each other
            # [i] Grid is a bit more complex, as we need to calculate the number of columns and rows, as well as the width of each column
            # [i] not just that but we'll also have to implement a key to swap around between columns,
            # [i] which is gonna be left and right key and they're NOT gonna loop (like pressing right on the right column warping back to the left column)
        if self._rendering_method == 'list':
            filebrowser_lines = []
    
    def highlight_if_match(self, filename: str):
        filebrowser_lines = []
        # TODO

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
