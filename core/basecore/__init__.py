from screen import context, Screen
from settings import Settings
from screen.formatting import Formatter, set_effect, Effect, set_viewport_title, wipe_line, clear_viewport, change_cursor_visibility, Fore, Back, Cursor
import os
import sys
import PIL
import time
import re
from typing import Any, NoReturn
from NCapybaraLib import String as string
from NCapybaraLib.Math import clamp
import hashlib
from difflib import SequenceMatcher

DIRECTORY = 1
MEDIA = 2
OTHER = 0

ASCII_ICONS = [
    """██████▓▓ # [i] files (any type of files that are not media)
██████▓▓▓▓
██████▓▓▓▓▓▓
████████████
████████████
████████████
████████████""",
       
    """  ▅▅▅▅ # [i] directories
███████████████
██▓▓▓▓▓▓▓▓▓▓▓▓██
██▓▓▓▓▓███████████
██▓▓▓███████████
██▓███████████
█████████████""",

    """      ▇■■■■■■■■■■■■▇ # [i] media (any type of it - can be videos, pictures, audio)
      █            █
      █            █
      █            █
      █       ██████
 ██████      ███████
███████       █████
 █████"""
]


class InvalidSelection(Exception): ...


# [*] Constants
MAX_FILENAME_LENGHT_GRID2 = 100
MAX_FILENAME_LENGHT_GRID3 = 55


def abspath(path: str, cwd: str | None = None) -> str:
    return os.path.join(cwd, path) if cwd else os.path.abspath(path)


def curate_quick_access_list(quick_access_list: list[str], cwd: str) -> list[str]:
    # [*] 1st: eliminate duplicates
    quick_access_list.sort()

    indexes = []

    for i, v in enumerate(quick_access_list, 0):
        if quick_access_list.count(v) > 1:
            indexes += [i + n for n in range(0, quick_access_list.count(v))] # [i] we can only do this safely cuz the list is sorted

    indexes.sort(reverse=True) # [i] why do this in reverse? 'cuz otherwise, we're gonna get errors :)

    for index in indexes:
        quick_access_list.pop(index)

    # [*] 2nd: eliminate wrong paths or filepaths
    indexes = []

    quick_access_list.sort()

    for i in quick_access_list:
        if not test_path(i, cwd):
            indexes.append(quick_access_list.index(i))

    indexes.sort(reverse=True)

    for index in indexes:
        quick_access_list.pop(index)

    # [*] 3rd: more than 30 items? be-gone!
    quick_access_list = quick_access_list[:30]

    return quick_access_list


def hash_md5(input_string: str) -> str:
    return hashlib.md5(input_string.encode()).hexdigest()


def list_difference(a: list[Any], b: list[Any] | None = None):
    if not b:
        return a

    return [i for i in a if i not in b]


def split_list(l: list[Any], a: Any) -> list[Any] | tuple[list[Any], list[Any]]:
    if a not in l:
        return l

    return l[:l.index(a)], l[l.index(a) + 1:]


def are_strings_similar(given_string: str, match: str, case_sensitive: bool = False, optimization_level: int = 3, perform_previous_verification: bool = True):
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

    if not case_sensitive:
        given_string = given_string.casefold()
        match = match.casefold()
        # [i] casefold is used to make the comparison case-insensitive
        # [<] fun fact: casefold is better than lower because it can handle more characters than lower can
        # [<] or should I say inter-lingual characters like the German ß or the Turkish ı, ü, ş, ğ, ö, ç

    if perform_previous_verification and given_string == match:
        return 1.0 # [i] if the strings are the same, the similarity ratio is 1.0

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
                # [<] funny shit
            ratio = seq_matcher.real_quick_ratio()

        case _:
            _ = seq_matcher.get_matching_blocks()
            ratio = seq_matcher.ratio()
            del _

    return ratio


def test_path(path: str, cwd: str | None, supposed_file: bool = False, method_mode: int = 0) -> bool:
    """
    ## test_path

    Test the path using 3 different tests.

    ### About Method Modes
    - 0 to do all tests
    - 1 to do Test 1
    - 2 to do Test 2
    - 3 to do Test 3
    - 4 to do Tests 1 and 3
    - 5 to do Tests 2 and 3
    - 6 to do Tests 1 and 2

    :param str path: the path of the directory or file to test
    :param bool supposed_file: to interpret this path as a file or a directory, defaults to False (interpret as a directory)
    :param int method_mode: the mode of the method to use for testing the path, defaults to 0
    :return bool: whether the path passed all tests (True) or failed at least one (False)
    """

    match method_mode:
        case 0:
            test1 = os.path.exists(path)
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
            test3 = os.path.exists(abspath(path, cwd))

        case 1:
            test1 = os.path.exists(path)
            test2 = test3 = True

        case 2:
            test1 = test3 = True
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)

        case 3:
            test1 = test2 = True
            test3 = os.path.exists(abspath(path, cwd))

        case 4:
            test1 = os.path.exists(path)
            test2 = True
            test3 = os.path.exists(abspath(path, cwd))

        case 5:
            test1 = True
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
            test3 = os.path.exists(abspath(path, cwd))

        case 6:
            test1 = os.path.exists(path)
            test2 = os.path.isfile(path) if supposed_file else os.path.isdir(path)
            test3 = True

    return all((test1, test2, test3))


def sort_files_by_criteria(list_of_paths: list[str], criteria: str = 'AZ', *_, fuzzy_ratios: list[float] | None = None):
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

        case 'fuzzy':
            if not fuzzy_ratios:
                raise ValueError("fuzzy_ratios must be provided when sorting by fuzzy criteria")

            list_of_paths.sort(key=lambda i: fuzzy_ratios[list_of_paths.index(i)], reverse=True)

        case _:
            list_of_paths.sort()


def __search_files(type_of_search: int, list_of_files: list[str], what_to_match: str, **kwargs) -> list[str] | NoReturn:
    match type_of_search:
        case 'regex':
            regex_matches: list[str] = []

            for filename in list_of_files:
                if re.search(what_to_match, filename):
                    regex_matches.append(filename)

            regex_matches.sort()
            new_list: list[str] = list_of_files.copy()
            new_list.sort()

            return regex_matches + [1] + list_difference(new_list, regex_matches) # [i] why is there a 1, you might be wondering
                                                                                  # [i] it's basically a very spaghetti code way of separating the 2 lists lol

        case 'strict': # [i] what_to_match must be contained in the filename, but doesn't have to be exactly the same as it
            if not kwargs.get('case_sensitive', False):
                what_to_match = what_to_match.casefold()
                temp: list[str] = [i.casefold() for i in list_of_files]

            else:
                temp: list[str] = list_of_files.copy()

            matches: list[str] = [i for i in temp if what_to_match in i]
            matches.sort()
            temp.sort()
            return matches + [1] + list_difference(temp, matches)

        case 'exact': # [i] what_to_match must be EXACTLY the same as the filename for it to be considered a match
            if not kwargs.get('case_sensitive', False):
                what_to_match = what_to_match.casefold()
                temp: list[str] = [i.casefold() for i in list_of_files]

            else:
                temp: list[str] = list_of_files.copy()

            matches: list[str] = [i for i in temp if what_to_match == i]
            matches.sort()
            temp.sort()
            return matches + [1] + list_difference(temp, matches)

        case 'filetype': # [i] what_to_match's file extension must be EXACTLY the same as the filename for it to be considered a match
                        # [i] will ALWAYS be case insensitive
            what_to_match: str = what_to_match.split('.')[-1].casefold() # [i] in case the user introduces a full filename, that part gets snapped
            temp: list[str] = [i.casefold() for i in list_of_files]

            matches = [temp.pop(temp.index(i)) for i in temp if what_to_match == i.split('.')[-1]]
            matches.sort()
            temp.sort()
            return matches + [1] + list_difference(temp, matches)

        case _:
            raise ValueError('no such search type exists' if type_of_search != 'fuzzy' else 'fuzzy search is not supported in this function - please use the fuzzy_search function')


def fuzzy_search(list_of_files: list[str], what_to_match: str, case_sensitive: bool = False, algorithm: int = 1, optimization_level: int = 3, previous_verification: bool = True, round_output: int = 0) -> list[float]:
    """
    ## fuzzy_search

    Perform a fuzzy search on a list of files.

    :param list[str] list_of_files: List of file names to search within.
    :param str what_to_match: The string to match against the file names.
    :param bool case_sensitive: If True, the search will be case sensitive. Defaults to False.
    :param int algorithm: The algorithm to use for the fuzzy search. As for the time being, there are only 2. Defaults to 1.
    :param int optimization_level: The level of optimization to apply to the search. Defaults to 3. [SPECIFIC TO ALGO 2]
    :param bool previous_verification: If True, perform a previous verification step before the search. Defaults to True. [SPECIFIC TO ALGO 2]
    :param int round_output: Round the output to a specified decimal point. Default 0 (no rounding). [SPECIFIC TO ALGO 1]
    :return list[float]: The similarity ratios for all the strings.
    """

    ratios = []

    match algorithm:
        case 1: # [i] NCapybaraLib's Algorithm
            for filename in list_of_files:
                ratios.append(string.string_similarity(filename, what_to_match, case_sensitive, round_output))

        case 2: # [i] SequenceMatcher Algorithm
            for filename in list_of_files:
                ratios.append(are_strings_similar(filename, what_to_match, case_sensitive, optimization_level, previous_verification))

        case _:
            raise ValueError('no such algorithm exists - as for the time being, there are only 2, with IDs 1 and 2')

    return ratios


def regex_search(list_of_files: list[str], what_to_match: str) -> list[str]:
    """
    ## regex_search

    Searches for files matching a regex pattern. Case sensitivity setting is always ignored by this search method.

    :param list[str] list_of_files: List of file paths to search.
    :param str what_to_match: Regex pattern to match in the files.
    :return list[str]: List of file paths that match the regex pattern.
    """
    return __search_files('regex', list_of_files, what_to_match)


def strict_search(list_of_files: list[str], what_to_match: str, case_sensitive: bool = False) -> list[str]:
    """
    ## strict_search

    Searches for files that strictly contain the given string.

    :param list[str] list_of_files: List of file paths to search.
    :param str what_to_match: The string to match in the files.
    :param bool case_sensitive: If True, the search will be case sensitive. Defaults to False.
    :return list[str]: List of file paths that strictly contain the given string.
    """

    return __search_files('strict', list_of_files, what_to_match, case_sensitive=case_sensitive)


def exact_search(list_of_files: list[str], what_to_match: str, case_sensitive: bool = False) -> list[str]:
    """
    ## exact_search

    Searches for files that exactly match the given string.

    :param list[str] list_of_files: List of file paths to search.
    :param str what_to_match: The exact string to match in the files.
    :param bool case_sensitive: If True, the search will be case sensitive. Defaults to False.
    :return list[str]: List of file paths that exactly match the given string.
    """

    return __search_files('exact', list_of_files, what_to_match, case_sensitive=case_sensitive)


def filetype_search(list_of_files: list[str], what_to_match: str) -> list[str]:
    """
    ## filetype_search

    Searches for files that have the same file extension. Is always case insensitive.

    :param list[str] list_of_files: List of file paths to search.
    :param str what_to_match: The exact string to match in the files.
    :return list[str]: List of file paths that exactly match the given string.
    """

    return __search_files('filetype', list_of_files, what_to_match)


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

    **The parameters below are used with \_\_init\_\_ to create a FileBrowser object, that is, to initialize it.**

    :param Screen screen: The screen object where the file browser will be rendered.
    :param Settings.FileBrowser filebrowser_settings: Settings for the file browser.
    :param tuple[str] quick_access_items: A tuple of paths for quick access items. Defaults to only 1 quick access item, which is the user's home directory.
    :param keyword_formatters: Optional keyword formatters for customizing the display.
    :param title: Optional title for the file browser interface.
    """

    def __init__(self, screen: Screen, filebrowser_settings: Settings.FileBrowser, quick_access_items: tuple[str] | None = None, keyword_formatters = None, title = None):
        """
        ## Initialization for FileBrowser class (\_\_init\_\_)

        Initializes the FileBrowser class with the provided parameters. Sets up the screen, quick access items,
        rendering method, rendering order, and current directory. Also prepares the quick access field values
        and file browser field for display.

        :param Screen screen: The screen object where the file browser will be rendered.
        :param Settings.FileBrowser filebrowser_settings: Settings for the file browser.
        :param tuple[str] quick_access_items: A tuple of paths for quick access items. Defaults to the user's home directory if not provided.
        :param keyword_formatters: Optional keyword formatters for customizing the display.
        :param title: Optional title for the file browser interface.
        """

        self.SCREEN: Screen = screen
        self._SETTINGS: Settings.FileBrowser = filebrowser_settings

        # [*] Current directory's contents
        self._cur_dir_content = []

        # [*] Search-related variables
        self._string_similarity_algo: int = self._SETTINGS['stringSimilarityAlgorithm'] # [i] 1 for NCapybaraLib's Algorithm - by Norb
                                                                                        # [i] 2 for SequenceMatcher Algorithm - by the creators of difflib module
                                                                                        # [<] 0 defaults to 1
        self._search_method: str = self._SETTINGS['searchMethod'] # [i] can be 'fuzzy', 'regex', 'exact', 'strict' or 'filetype'
        self._search_keyword: str | None = None
        self._sequence_matcher_optimization: int = self._SETTINGS['sequenceMatcherOptimization'] # [i] can be 0, 1, 2, 3, 4; any other value defaults to 5, meaning ANY level
        self._sequence_matcher_verify: bool = self._SETTINGS['sequenceMatcherPrevVerification'] # [i] perform previous verification for SequenceMatcher
        self._search_case_sensitivity: bool = self._SETTINGS['searchCaseSensitive'] # [i] do a case sensitive search; ignored by Regex and Filetype Searches
        self._fuzzy_ratios: list[float] = []

        # [*] Render related variables
        self._rendering_method = self._SETTINGS['displayMethod'] # [i] can be "grid2", "grid3", "centeredlist" "list"
        self._rendering_order = self._SETTINGS['displayOrder'] # [i] can be "AZ", "ZA", "time-up", "time-down", "size-up", "size-down", "tch-up", "tch-down", "tac-up", "tac-down"
                                                                   # [i] "AZ" and "ZA" are for alphabetical order
                                                                   # [i] "time-up" and "time-down" are for time of creation
                                                                   # [i] "size-up" and "size-down" are for size of the file
                                                                   # [i] "tch-up" and "tch-down" are for time of last change
                                                                   # [i] "tac-up" and "tac-down" are for time of last access
                                                                   # [<] now who the fuck thought these alias would be a good idea?

        # [*] Selection and current directory
        self._old_selection = -1
        self._selection = 0
        self._cur_dir: str = os.getcwd()

        # [*] Quick Access
        self._quick_access_items = self._SETTINGS['quickAccessPaths']
        
        # [*] Details Field
        self._details = None 

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

    def highlight_search_results(self) -> list[str]:
        match self._search_method.lower():
            case 'regex':
                files: list[str] = regex_search(self._cur_dir_content, self._search_keyword)
                matches, others = split_list(files, 1)

                temp = []

                for match in matches:
                    temp.append(f"{Back.YELLOW}{Fore.BLACK}{match}{Fore.RESET}{Back.RESET}")

                del matches

                return temp + others

            case 'strict':
                files = strict_search(self._cur_dir_content, self._search_keyword, self._search_case_sensitivity)
                matches, others = split_list(files, 1)

                temp = []

                for match in matches:
                    temp.append(f"{Back.YELLOW}{Fore.BLACK}{match}{Fore.RESET}{Back.RESET}")

                del matches

                return temp + others

            case 'exact':
                files = exact_search(self._cur_dir_content, self._search_keyword, self._search_case_sensitivity)
                matches, others = split_list(files, 1)

                temp = []

                for match in matches:
                    temp.append(f"{Back.YELLOW}{Fore.BLACK}{match}{Fore.RESET}{Back.RESET}")

                del matches

                return temp + others

            case 'filetype':
                files = filetype_search(self._cur_dir_content, self._search_keyword)
                matches, others = split_list(files, 1)

                temp = []

                for match in matches:
                    temp.append(f"{Back.YELLOW}{Fore.BLACK}{match}{Fore.RESET}{Back.RESET}")

                del matches

                return temp + others

            case _:
                raise ValueError("no such search method exists" if self._search_method != 'fuzzy' else "fuzzy search is not supported in this function - please use the sorting function but with the argument set to \"fuzzy\" instead")

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
        self._prot_cur_dir_content: list[str] = os.listdir(self._cur_dir)
        self._cur_dir_content = [os.path.basename(i) for i in self._prot_cur_dir_content]
        sorted_contents: list[str] | None = None

        # [?] Is the user searching something?
        # [?] If he is, is he using Fuzzy Searching? - that one is a bit of an odd ball and has to be handled separately
        if self._search_keyword and self._search_method.lower() != 'fuzzy':
            # [i] the user is indeed searching something with either regex, strict, exact or filetype
            # [i] therefore we are not gonna do the regular sorting mechanic
            # [i] we're gonna do the search mechanic instead
            sorted_contents = self.highlight_search_results() # [i] searched and highlighted, how cool :O

        else:
            # [*] Getting the designations of the elements in the current directory
            designations: dict[str, list[str]] = self.get_designation_based_on_element_type()

            # [?] So, at this point, the user could be: not searching or searching with fuzzy. let's see
            if self._search_keyword: # [i] since we already verified it wasn't fuzzy before it has to be fuzzy NOW so we don't need to bother checking
                # [i] the user is searching with fuzzy
                # [i] we're gonna have to sort the files based on the fuzzy ratios
                # [i] and we're also gonna do the regular highlighting according to the designations
                sorted_mountpoints: list[str] = self.highlight_based_on_designation('mountpoint', designations['mountpoint'])
                sorted_folders: list[str] = self.highlight_based_on_designation('folder', designations['folder'])
                sorted_files: list[str] = self.highlight_based_on_designation('file', designations['file'])
                sorted_symlinks: list[str] = self.highlight_based_on_designation('symlink', designations['symlink'])
                sorted_others: list[str] = self.highlight_based_on_designation('other', designations['other'])

                sorted_contents: list[str] = sort_files_by_criteria(sorted_mountpoints + sorted_folders + sorted_files + sorted_symlinks + sorted_others, 'fuzzy', self._fuzzy_ratios) # [i] we now combine all of these into one list

            else:
                # [*] Sorting the contents of the same directory
                sorted_mountpoints: list[str] = self.highlight_based_on_designation('mountpoint', sort_files_by_criteria(designations['mountpoint'])) # [i] mountpoints are always sorted by name
                                                                                            # [i] because they don't have any other criteria to sort by
                sorted_folders: list[str] = self.highlight_based_on_designation('folder', sort_files_by_criteria(designations['folder'], self._rendering_order))
                sorted_files: list[str] = self.highlight_based_on_designation('file', sort_files_by_criteria(designations['file'], self._rendering_order))
                sorted_symlinks: list[str] = self.highlight_based_on_designation('symlink', sort_files_by_criteria(designations['symlink'], self._rendering_order))
                sorted_others: list[str] = self.highlight_based_on_designation('other', sort_files_by_criteria(designations['other'], self._rendering_order))

                sorted_contents: list[str] = sorted_mountpoints + sorted_folders + sorted_files + sorted_symlinks + sorted_others # [i] we now combine all of these into one list

        # [*] Highlight the current selection
        sorted_contents.insert(0, f"{Fore.BLUE}..{Fore.RESET}") # [i] force the parent directory to be the first item, no mather the searching order and/or sorting
        self.highlight_selection(sorted_contents)

        # [*] Setting up the grid/list mechanic
            # [i] List is very simple, as we just place each file/folder/whatever below each other
            # [i] Grid is a bit more complex, as we need to calculate the number of columns and rows, as well as the width of each column
            # [i] not just that but we'll also have to implement a key to swap around between columns,
            # [i] which is gonna be left and right key and they're NOT gonna loop (like pressing right on the right column warping back to the left column)
        if self._rendering_method == 'grid2':
            # [i] stands for grid with 2 columns
            avg_length: int = sum([len(i) for i in sorted_contents]) // len(sorted_contents) # [i] average length of the strings

            if avg_length > MAX_FILENAME_LENGHT_GRID2:
                avg_length = MAX_FILENAME_LENGHT_GRID2 # [i] let's cap this value

            filebrowser_lines = [f"{sorted_contents[i]}{' ' * int(clamp(MAX_FILENAME_LENGHT_GRID2 // avg_length, 1, 10))}{sorted_contents[i + 1]}" for i in range(0, len(sorted_contents), 2)]

        elif self._rendering_method == 'grid3':
            # [i] stands for grid with 3 columns
            avg_length: int = sum([len(i) for i in sorted_contents]) // len(sorted_contents) # [i] average length of the strings

            if avg_length > MAX_FILENAME_LENGHT_GRID3:
                avg_length = MAX_FILENAME_LENGHT_GRID3 # [i] let's cap this value

            filebrowser_lines = [f"{sorted_contents[i]}{' ' * int(clamp(MAX_FILENAME_LENGHT_GRID3 // avg_length, 1, 5))}{sorted_contents[i + 1]}{' ' * int(clamp(MAX_FILENAME_LENGHT_GRID3 // avg_length, 1, 5))}{sorted_contents[i + 2]}" for i in range(0, len(sorted_contents), 3)]

        else: # [i] default to list mode, which can be "list" or "centeredlist". for this step, both work exactly the same so fuck it
            filebrowser_lines = sorted_contents

        max_length: int = clamp(max([len(i) for i in filebrowser_lines]), 16, 7500) # [<] if it somehow reaches this number, please think about re-structuring your directories cuz HOLY SHIT!!!! That's literally 75% of 10000

        for index, value in enumerate(filebrowser_lines.copy(), 0):
            if len(value) < max_length:
                if self._rendering_method != 'centeredlist':
                    filebrowser_lines[index] = f"{value}{' ' * (max_length - len(value))}"

                else:
                    filebrowser_lines[index] = value.center(max_length)

            filebrowser_lines[index] = f"║ {value} ║" # [i] one space on either end will work :))

        filebrowser_lines.insert(0, f'╔{"=" * (max_length + 2)}╗') # [i] the 2 spaces, remember?
        filebrowser_lines.insert(1, f'╠ {" FileBrowser ".center(max_length, "-")} ╣') # [i] dashes makes it less compact than equal signs, which is good for subtitles
        filebrowser_lines.append(f'╚{"=" * (max_length + 2)}╝') # [i] again the 2 bloody spaces... yeah, i had to say that. it was totally necessary

        # [i] alright I think that's everything for this function
        return filebrowser_lines
    
    def get_details_ready(self):
        if self._old_selection == self._selection:
            return self._details # [i] use the previously set details
        

    def get_quick_access_ready(self):
        self._curated_list = curate_quick_access_list(self._quick_access_items.copy(), self._cur_dir)

        if not self._curated_list:
            # [i] if there are exactly 0 items, we'll add only one so the height calculation goes well
            self._curated_list = [os.path.expanduser('~')]

        # [i] the quick access will be left to the actual file browser itself and above the "details" field
        
        

    def draw_to_screen(self):
        self.SCREEN.writelines(self._lines)

    def get_everything_ready(self):
        raise NotImplementedError('TODO') # TODO

    def get_designation_based_on_element_type(self) -> dict[str, list[str]]:
        eggs = {'folder': [], 'file': [], "symlink": [], 'mountpoint': [], 'other': []}

        for i in self._prot_cur_dir_content:
            if os.path.isdir(i):
                eggs['folder'].append(os.path.basename(i))
                continue

            if os.path.islink(i):
                eggs['symlink'].append(os.path.basename(i))
                continue

            if os.path.ismount(i):
                eggs['mountpoint'].append(os.path.basename(i))
                continue

            if os.path.isfile(i):
                eggs['file'].append(os.path.basename(i))
                continue

            eggs['other'].append(os.path.basename(i))

        return eggs


    def highlight_selection(self, sorted_list: list[str], **kw) -> list[str]:
        """
        ## FileBrowser.highlight_selection

        Highlights the current selection, if possible. Otherwise, raises an error.

        ### Test Mode
        See `FileBrowser.highlight_selection.how_to_use_test_mode` for more information on the Test Mode.

        :param list[str] sorted_list: The list of strings where the selection is.
        :raises InvalidSelection: The selection index is out of range, therefore cannot be reached.
        :return list[str]: The list, but with the selection highlighted.
        """

        __test_mode = kw.pop('test_mode', False)

        if __test_mode:
            try:
                _ = sorted_list[self._selection]

            except IndexError:
                # [<] '_' never got assigned, so we can just return False, no need to delete it (in fact it wouldn't even work)
                return False # [i] test failed

            else:
                del _
                return True # [i] test passed

            return -1 # [i] safe barrier: if somehow nothing gets returned, we end with an unconclusive result. Again, most likely unnecessary but I don't like taking risks, sorry.

        try:
            sorted_list[self._selection] = f"{Fore.RESET}{Back.RESET}{set_effect(Effect.NEGATIVE)}{sorted_list[self._selection]}{set_effect(Effect.POSITIVE)}{Fore.RESET}{Back.RESET}" # [i] get rid of all the formatting, then apply the negative effect, then reset the formatting. taht why we have a good black on white (or a white on black if you're an epic nerd who has a terminal in light mode)

        except IndexError as e:
            raise InvalidSelection("The selection index is out of range") from e

        return sorted_list

    highlight_selection.how_to_use_test_mode = """### Test Mode
Test mode for this function completely changes how it works. Instead of highlighting, it tries to access the selection index.
If it fails, it returns False. If it succeeds, it returns True. If it somehow returns nothing, it returns -1.

To enable it, set the `test_mode` keyword argument to True. To keep this function simple, Test Mode was not documented on the docstring."""
