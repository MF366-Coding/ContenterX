"""
Interpreter for CX Setup Scripts (`cxsetup.py`)
-----------------------------
This program was made by MF366 and is licensed under the permissive MIT License.

If you use this shitty ass interpreter in a project of yours, I'd appreciate it if you credited me, by keeping this docstring here, for example.

Thank you!
"""


from enum import IntEnum
from argparse import ArgumentParser
import os
import sys
from typing import Any, Literal, NoReturn
import struct
import subprocess
from getpass import getpass
from cxconst import VERSION, NAME, AUTHOR, LICENSE, YEAR, GITHUB, DOCS_URL
import re
from colorama import Fore, Back, Style
import requests


class CacheOverflow(Exception): ...


SOURCE_CONVTABLE: list[str] = [
    "system", "cx", "pip", "npm", "binary"
]


class FlagMarker:
    def __init__(self, on_true, state: bool = False, on_false = None):
        self._state = state
        self._on_true = on_true
        self._on_false = on_false

    def toggle(self):
        self._state: bool = not self._state

        match self._state:
            case False:
                if self._on_false is not None:
                    self._on_false()

            case True:
                self._on_true()

            case _:
                raise Exception('flag marker is not working correctly')


class char(object):
    def __init__(self, byte: bytes) -> None:
        if not byte:
            raise ValueError('one byte must be given')

        self.CHAR: bytes = byte[0:1]

    def ToEncodedString(self, encoding: str = 'utf-8') -> str:
        return str(self.CHAR, encoding)

    def ToInt(self) -> int:
        return(ord(self.CHAR))

    def AsBytes(self) -> bytes:
        return self.CHAR

    def ToBool(self) -> bool:
        return self.ToInt() != 0

    @classmethod
    def FromString(cls, string: str, *, encoding: str = 'utf-8'):
        return cls(bytes(string, encoding=encoding))

    from_string = FromString
    to_int = ToInt
    to_bool = ToBool
    to_string = to_encoded_string = ToEncodedString
    as_bytes = AsBytes

    def __str__(self) -> str:
        return str(self.CHAR, 'utf-8')

    def __len__(self) -> int:
        return 1 # [i] even if empty, it's 1

    def __repr__(self) -> str:
        return f"char({self.CHAR.__repr__()})"

    def __eq__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR == other.CHAR

        if isinstance(other, bytes):
            return self.CHAR == other

        if isinstance(other, str):
            return self.__str__() == other

        if isinstance(other, int):
            return self.ToInt() == other

        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR < other.CHAR

        if isinstance(other, bytes):
            return self.CHAR < other

        if isinstance(other, str):
            return self.__str__() < other

        if isinstance(other, int):
            return self.ToInt() < other

        return False

    def __le__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR <= other.CHAR

        if isinstance(other, bytes):
            return self.CHAR <= other

        if isinstance(other, str):
            return self.__str__() <= other

        if isinstance(other, int):
            return self.ToInt() <= other

        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR > other.CHAR

        if isinstance(other, bytes):
            return self.CHAR > other

        if isinstance(other, str):
            return self.__str__() > other

        if isinstance(other, int):
            return self.ToInt() > other

        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR >= other.CHAR

        if isinstance(other, bytes):
            return self.CHAR >= other

        if isinstance(other, str):
            return self.__str__() >= other

        if isinstance(other, int):
            return self.ToInt() >= other

        return False

    def __hash__(self) -> int:
        return hash(self.CHAR)



class DataType(IntEnum):
    VOID = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    BOOLEAN = 4
    CHAR = 5
    GARBAGE = 6


class Cache:
    def __init__(self, reserved_bytes: int) -> None:
        self._RESERVED: int = reserved_bytes

        if self.reserved_bytes < 1:
            self._RESERVED = 1

        self.cache = bytearray(reserved_bytes)
        self._pointer = 0

    def clear(self) -> None:
        self.cache = bytearray(self._RESERVED)
        self._pointer = 0

    def __len__(self) -> int:
        length: int = len(self.cache)

        if length > self._RESERVED:
            raise CacheOverflow(f"the cache is taking up {self._RESERVED - length} byte(s) more than it should")

        return length

    def __str__(self) -> str:
        return str(bytes(self.cache.copy()), 'utf-8')

    def __repr__(self) -> str:
        return self.__str__()

    def get_cache(self, pos: int, len: int = -2, end: int = -2, step: int = 1) -> bytes:
        """
        Cache.get_cache
        ------------------

        Collects and returns cache values.

        :param int pos: starting position for cache grab
        :param int len: length of cache grab, defaults to -2 meaning DISABLED
        :param int end: alternatively, end position of cache grab; defaults to -2 meaning DISABLED
        :param int step: _description_, defaults to 1
        :raises ValueError: both len and end were given - only one is allowed per call
        :return bytes: cached values as bytes
        """

        if (len == end) and len != -2: # [i] we use -2 cuz -1 stands for LAST_POS
            raise ValueError('only one of the arguments len and end should be given values')

        if (len == end):
            end = pos + 1

        elif len > 0:
            end = pos + len

        else:
            end = max(end, -1)

        return bytes(self.cache.copy())[pos:end:step]

    def readable_cache(self, cached_bytes: bytearray, data_type: int) -> bytes | bool | int | str | char | float | Any:
        """
        Cache.readable_cache
        ---------------------

        Turns previously obtained values (`Cache.get_cache`) into more versatile formats (other than `bytes`).

        :param bytearray cached_bytes: data to parse (obtained values)
        :param int data_type: the data type (see `DataTypes` enum -> GARBAGE/6+ reverts back to `bytes`)
        :raises TypeError: an invalid type was processed (such as VOID)
        :return bytes | bool | int | str | char | float | Any: the parsed data
        """

        if data_type >= DataType.GARBAGE:
            return bytes(cached_bytes)

        match data_type:
            case DataType.INTEGER | DataType.BOOLEAN:
                parsed_integer = int.from_bytes(cached_bytes, byteorder='big')

                if data_type == DataType.BOOLEAN:
                    return parsed_integer != 0

                return parsed_integer

            case DataType.CHAR:
                try:
                    parsed_char = str(cached_bytes, 'utf-8')

                except UnicodeError:
                    parsed_char = str(int.from_bytes(cached_bytes, byteorder='big'))

                return char.FromString(parsed_char)

            case DataType.STRING:
                try:
                    parsed_string = str(cached_bytes, 'utf-8')

                except UnicodeError:
                    parsed_string = str(int.from_bytes(cached_bytes, byteorder='big'))

                return parsed_string

            case DataType.FLOAT:
                return struct.unpack('>f', cached_bytes)[0]

            case _:
                raise TypeError('type is not valid')

    def _advance_pointer(self):
        if self._RESERVED == 1:
            self._pointer = 1
            return

        if self._pointer >= (self._RESERVED - 1):
            self._pointer = 0

        else:
            self._pointer += 1

    def set_cache(self, data: bytes | bool | int | str | float) -> Literal[0]:
        """
        Cache.set_cache
        ----------------

        Caches a value, which can be of types `int`, `bool`, `float`, `str`, `char` (via string) or `bytes`

        :param bytes | bool | int | str | float data: the data to cache
        :raises CacheOverflow: the storage for the cache has been exhausted
        :return Literal[0]: success code
        """

        if not data:
            return 0 # [i] no more data

        if isinstance(data, bool):
            # [*] Instantly set the cache for that, as it's either a 0 or a 1
            self.cache[self._pointer] = data.to_bytes(1, 'big')[0]
            self._advance_pointer()
            return 0 # [i] no more data

        if isinstance(data, int):
            # [?] Is it a large int??
            if data > 255:
                # [*] Split the beast into multiple bytes
                int_bytes: bytes = data.to_bytes((data.bit_length() + 7) // 8, byteorder='big')
                self.cache[self._pointer] = int_bytes[0]
                self._advance_pointer()
                return self.set_cache(int_bytes[1:]) # [i] more data to go buddy

            self.cache[self._pointer] = data.to_bytes(1, 'big')[0] # [i] will always "fit" into 1 byte exactly
            self._advance_pointer()
            return 0 # [i] no more data

        if isinstance(data, str):
            # [?] Is it a string or a char??
            if len(data) == 1:
                # [*] Character
                CHAR = True
                first_char = data

            else:
                # [*] String
                CHAR = False
                first_char = data[0]

            if CHAR:
                self.cache[self._pointer] = bytes(first_char, 'utf-8')[0]
                self._advance_pointer()
                return 0

            self.cache[self._pointer] = bytes(first_char, 'utf-8')[0]
            self._advance_pointer()
            return self.set_cache(data[1:])

        if isinstance(data, float):
            if int(data) == data:
                return self.set_cache(int(data))

            float_bytes: bytes = struct.pack('>f', data)
            self.cache[self._pointer] = float_bytes[0]
            self._advance_pointer()
            return self.set_cache(float_bytes[1:])

        # [*] If nothing worked out, it's bytes
        if len(data) > 1:
            self.cache[self._pointer] = data[0]
            self._advance_pointer()
            return self.set_cache(data[1:])

        self.cache[self._pointer] = data[0]
        self._advance_pointer()
        return 0 # [i] no more data

    @property
    def reserved_bytes(self) -> int:
        return self._RESERVED


class RequirementSource(IntEnum):
    SYSTEM = 0
    CX = 1
    PIP = 2
    NPM = 3
    BINARY = 4


class Interpreter:
    def __init__(self, script: str, cache_bytes: int, flag_marker: FlagMarker, pkg_command: str, pip_path: str = 'pip', npm_path: str = 'npm') -> None:
        self._cache: Cache = Cache(cache_bytes)
        self._specialized_cache: Cache = Cache(1)
        self._flag_marker: FlagMarker = flag_marker
        self._pippath: str = pip_path
        self._npmpath: str = npm_path
        self._pkgcmd: str = pkg_command
        self._cwd = os.getcwd()
        self.statement = 0
        self.InterpreterRunning = False
        self._script: str = script
        self._requirements: dict[str, list[str]] = {
            "system": [],
            "cx": [],
            "pip": [],
            "npm": [],
            "binary": []
        }
        self._specialized_cache.set_cache(True)

    def cout(self, *data: str) -> Literal[0]:
        print(*data, sep='', end='')
        return 0

    def cin(self, limit: int = -1, *, msg: str = f'{Fore.CYAN}An input is required (press Enter to ignore it): {Fore.RESET}') -> str | Literal[1]:
        print(msg, end='')
        data: str = input()

        if not data:
            return 1 # [!?] no data given

        # [i] my plan was to use curses but shit's broken af so instead I'll just slice
        # [i] by the limit. shitty approach but oh well
        if limit > 0:
            return data[:limit]

        return data

    def full_echo(self, data: str, file: str | int = 0) -> Literal[1] | Literal[0]:
        """
        full_echo (a.k.a. ECHO OR DIE)
        -----------------

        Echo something to a new file OR output it. If none of them works, DIE TRYING!

        :param str data: string to echo
        :param str | int file: the file to echo to (if none, just COUT the data), defaults to 0
        :return Literal[1] | Literal[0]: 1 - reverted back to COUT but success either ways; 0 - ECHOed successfully
        """

        if not file:
            return self.cout(data) + 1

        if not os.path.isabs(file):
            file = os.path.join(self._cwd, file)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(data)

        return 0

    def echo(self, data: str, file: str | int = 0) -> Literal[1] | Literal[0]:
        """
        echo
        -----------------

        Echo something to a new file OR output it.

        :param str data: string to echo
        :param str | int file: the file to echo to (if none, just COUT the data), defaults to 0
        :raises FileExistsError: ECHO cannot overwrite files, try ECHORDIE
        :return Literal[1] | Literal[0]: 1 - reverted back to COUT but success either ways; 0 - ECHOed successfully
        """

        if not file:
            return self.cout(data) + 1

        if not os.path.isabs(file):
            file = os.path.join(self._cwd, file)

        if os.path.exists(file):
            self.raise_error(FileExistsError, 'cannot overwrite file - if you do not care about overwriting, consider using ECHORDIE')

        with open(file, 'w', encoding='utf-8') as f:
            f.write(data)

        return 0

    def raise_error(self, error: BaseException = Exception, message: str = '') -> NoReturn:
        raise error(f"statement {self.statement + 1}: {message}")

    def handle_cache_grab(self, declaration: str) -> bytes | bool | int | str | char | float:
        # [i] It'll look something like this "c0:2l:4:3" or "c0:2e:4:3"
        # [*] Let's use regex
        PATTERN = "c[0-9]+:[0-9]+[el]:[0-9]+:[0-9]+:[rlbn]"
        match: re.Match[str] | None = re.match(PATTERN, declaration)

        if not match:
            return -69 # [i] magic number verification LMFAO

        parsed_declaration: str = declaration[match.start():match.end()] # [i] the only part that matters

        # [*] Is it actually a valid declaration?
        arguments: list[str] = parsed_declaration[1:].split(':')

        # [*] First argument: integer
        if int(arguments[0]) >= self._cache.reserved_bytes - 1:
            self.raise_error(CacheOverflow, "trying to cache grab more than it's possible to")

        # [*] Second argument: integer + literal
        second_arg: int = int(arguments[1][:len(arguments[1]) - 1])
        arg_literal: str = arguments[1][-1]

        match arg_literal:
            case 'l':
                if second_arg < 1:
                    self.raise_error(ValueError, "make sure the lenght argument is an integer larger than 0")

                if int(arguments[0]) + second_arg > self._cache.reserved_bytes:
                    self.raise_error(CacheOverflow, "the given lenght is larger than the amount of bytes reserved for the cache - consider doing step-by-step cache grabs")

            case 'e':
                if not second_arg:
                    second_arg = -1

                elif second_arg > self._cache.reserved_bytes + 1:
                    self.raise_error(CacheOverflow, "the given end value exceeds the amount of bytes reserved for the cache")

            case _:
                self.raise_error("unknown error") # [i] technically will never happen cuz of the regex check but oh well

        # [*] Third argument: integer
        third_arg: int = -1 if not int(arguments[2]) else int(arguments[2])

        # [*] Fourth argument: DataType integer
        fourth_arg: int = int(arguments[3])

        if int(fourth_arg) == DataType.VOID:
            self.raise_error(TypeError, "cannot do a cache grab for a VOID data type")

        if int(fourth_arg) >= DataType.GARBAGE:
            fourth_arg = DataType.GARBAGE
            
        # [*] Fifth argument: char
        fifth_arg = arguments[4][0]

        # [*] Actual cache grab
        cache_data: bytes = self._cache.get_cache(int(arguments[0]), second_arg if arg_literal == 'l' else -2, second_arg if arg_literal == 'e' else -2, third_arg)
        parsed_cache: bytes | bool | int | str | char | float = self._cache.readable_cache(cache_data, fourth_arg)

        match fifth_arg:
            case 'b':
                parsed_cache = parsed_cache.strip()
                
            case 'r':
                parsed_cache = parsed_cache.rstrip()
                
            case 'l':
                parsed_cache = parsed_cache.lstrip()
                
            case _:
                pass
        
        return parsed_cache

    def handle_requirement(self, source: int, arg: str) -> Literal[0]:
        if source < 0:
            self.raise_error(ValueError, "the source must be a positive integer or zero")

        if source > 4:
            self.raise_error(ValueError, "only 5 sources are accounted for, starting at 0, ending at 4")

        if not arg:
            self.raise_error(ValueError, "you must include a valid requirement to install from the source")

        self._requirements[SOURCE_CONVTABLE[source]].append(arg)
        return 0

    def run(self, command: str, *arguments: str, capture_output: bool = False, text: bool = True) -> subprocess.CompletedProcess[Any] | None:
        args = []

        for arg in arguments:
            if not isinstance(arg, (str, char)):
                self.raise_error(TypeError, f"one of the arguments is not of type string or char, as expected, but rather {str(type(arg)).split(chr(39))[1]}")

            args.append(str(arg))

        if not isinstance(command, (str, char)):
            self.raise_error(TypeError, f"the given command is not of type string or char, as expected, but rather {str(type(arg)).split(chr(39))[1]}")

        result: subprocess.CompletedProcess[Any] = subprocess.run([str(command), *args], capture_output=capture_output, text=text)
        return result

    def save_to_cache(self, value: str | int | float) -> Literal[0]:
        self._cache.set_cache(value)
        return 0

    def handle_statement(self, statement: str):
        parts: list[str] = statement.split('??')
        func: str = parts[0]
        negation_char = parts[0][0]

        if negation_char == '!':
            is_positive = 0
            func = parts[0][1:]

        else:
            is_positive = 1

        is_globally_positive = self._specialized_cache.cache[0]
        arguments: list[str] = parts[1:]

        args: list[str] = []
        func = func.strip()

        if (is_globally_positive + is_positive) == 1:
            return # [i] the necessary conditions are not met

        for arg in arguments:
            parsed_arg: str = arg.strip()

            if re.match(r'[0-9]+\.[0-9]+', parsed_arg) or re.match('[0-9]+[e][0-9]+', parsed_arg):
                # [i] data type: float
                args.append(float(parsed_arg))
                continue

            if re.match('[0-9]+', parsed_arg):
                # [i] data type: integer
                args.append(int(parsed_arg))
                continue

            if parsed_arg.startswith('"') and parsed_arg.endswith('"') and parsed_arg.count('"') == 2:
                # [i] data type: string or char
                if len(parsed_arg) == 3:
                    # [i] char
                    args.append(char.from_string(parsed_arg[1:-1]))
                    continue

                args.append(parsed_arg[1:-1])
                continue

            # [*] maybe it's a cache grab declaration
            cgrab: bytes | bool | int | str | char | float = self.handle_cache_grab(parsed_arg)

            if cgrab != -69:
                args.append(cgrab)
                continue

            # [*] is it a variable?
            if parsed_arg.startswith("v'") and parsed_arg.endswith("'"):
                args.append(os.environ.get(parsed_arg[2:-1], parsed_arg[2:-1])) # [i] if the var does not exist, return itself
                continue

            self.raise_error(TypeError, f'argument must be string, char, int or float - {parsed_arg}')

        del arguments

        match func:
            case 'ENDL':
                if args:
                    self.raise_error(SyntaxError, f"no arguments were expected, but {len(args)} argument(s) were received")

                self.cout('\n')
                
            case 'ENDL2':
                if args:
                    self.raise_error(SyntaxError, f"no arguments were expected, but {len(args)} argument(s) were received")

                self.cout('\n\n')
                
            case 'GETPASS':
                if len(args) != 1:
                    self.raise_error(SyntaxError, f"1 argument was expected, but {len(args)} arguments were received")

                if not isinstance(args[0], str):
                    if isinstance(args[0], char):
                        args = [str(args[0])]

                    else:
                        self.raise_error(TypeError, f"a prompt of type string or char was expected, but received {str(type(args[0])).split(chr(39))[1]} instead")

                user_input = getpass(args[0])
                
                if user_input:
                    self.save_to_cache(user_input)

            case 'COUT':
                self.cout(*args)

            case 'ECHO':
                if len(args) != 2:
                    self.raise_error(SyntaxError, f"2 arguments were expected, but {len(args)} arguments were received")

                if not isinstance(args[0], (str, char)):
                    self.raise_error(TypeError, f"ECHO was expecting data to write in the form of a string or a char, but received {str(type(args[0])).split(chr(39))[1]} instead")

                if not isinstance(args[1], (str, char)):
                    self.raise_error(TypeError, f"ECHO was expecting a filepath to write to in the form of a string or a char, but received {str(type(args[1])).split(chr(39))[1]} instead")

                args = [str(args[0]), str(args[1])]

                self.echo(*args)

            case 'CIN':
                if len(args) > 2:
                    self.raise_error(SyntaxError, f"2, 1 or no arguments were expected, but {len(args)} arguments were received")

                elif len(args) < 1:
                    args = [0]

                if len(args) == 2:
                    if not isinstance(args[0], int):
                        self.raise_error(TypeError, f"a prompt length of type int was expected, but one of type {str(type(args[0])).split(chr(39))[1]} was received instead")

                    if not isinstance(args[1], (str, char)):
                        self.raise_error(TypeError, f"a prompt of type string or char was expected, but one of type {str(type(args[1])).split(chr(39))[1]} was received instead")

                    user_input: str | Literal[1] = self.cin(args[0], msg=f'{Fore.CYAN}{str(args[1])}{Fore.RESET}')
                    
                else:
                    if not isinstance(args[0], int):
                        self.raise_error(TypeError, f"a prompt length of type int was expected, but one of type {str(type(args[0])).split(chr(39))[1]} was received instead")

                    user_input: str | Literal[1] = self.cin(args[0])

                if user_input != -1:
                    self._cache.set_cache(user_input)

            case 'TERMINATE':
                if len(args) > 1:
                    self.raise_error(SyntaxError, f"1 or no arguments were expected, but {len(args)} arguments were received")

                if args:
                    if not isinstance(args[0], int):
                        self.raise_error(TypeError, 'an int was expected to serve as error code for TERMINATE but another datatype was received')

                    if args[0] > 0:
                        print(f"{Fore.RED}Terminated with Error Code #{args[0]}{Style.RESET_ALL}", end='')
                        self.InterpreterRunning = False

                self.InterpreterRunning = False

            case 'REQUIRES':
                if len(args) != 2:
                    self.raise_error(SyntaxError, f"2 arguments were expected, but {len(args)} arguments were received")

                if not isinstance(args[0], int):
                        self.raise_error(TypeError, f"a source of type int was expected, but one of type {str(type(args[0])).split(chr(39))[1]} was received instead")

                if not isinstance(args[1], (str, char)):
                    self.raise_error(TypeError, f"a requirement of type string or char was expected, but one of type {str(type(args[1])).split(chr(39))[1]} was received instead")

                self.handle_requirement(args[0], str(args[1]))

            case 'REQINSTALL':
                if args:
                    self.raise_error(SyntaxError, f"0 arguments were expected, but {len(args)} arguments were received")

                self.install_requirements()

            case 'STYLE':
                if len(args) != 1:
                    self.raise_error(SyntaxError, f"1 argument was expected, but {len(args)} arguments were received")

                if args[0] not in ("BRIGHT", "DIM", "NORMAL", "RESET_ALL", "RESET"):
                    self.raise_error(ValueError, "the style argument must be one of the following 5 strings - BRIGHT, DIM, NORMAL, RESET, RESET_ALL")

                self.cout(eval(f"Style.{'RESET_ALL' if args[0] == 'RESET' else args[0]}", globals()))
                
            case 'FORE':
                if len(args) != 1:
                    self.raise_error(SyntaxError, f"1 argument was expected, but {len(args)} arguments were received")

                allowed_args: tuple[str] = ("RESET", 'BLACK', 'BLUE', 'YELLOW', 'RED', 'GREEN', 'MAGENTA', 'CYAN', 'WHITE', *[f"LIGHT{i}_EX" for i in ('BLACK', 'BLUE', 'YELLOW', 'RED', 'GREEN', 'MAGENTA', 'CYAN', 'WHITE')])
                
                if args[0] not in allowed_args:
                    self.raise_error(ValueError, f"the foreground argument must be one of the following strings - {allowed_args}")

                self.cout(eval(f"Fore.{args[0]}", globals()))
                
            case 'BACK':
                if len(args) != 1:
                    self.raise_error(SyntaxError, f"1 argument was expected, but {len(args)} arguments were received")

                allowed_args: tuple[str] = ("RESET", 'BLACK', 'BLUE', 'YELLOW', 'RED', 'GREEN', 'MAGENTA', 'CYAN', 'WHITE', *[f"LIGHT{i}_EX" for i in ('BLACK', 'BLUE', 'YELLOW', 'RED', 'GREEN', 'MAGENTA', 'CYAN', 'WHITE')])
                
                if args[0] not in allowed_args:
                    self.raise_error(ValueError, f"the background argument must be one of the following strings - {allowed_args}")

                self.cout(eval(f"Back.{args[0]}", globals()))
                
            case 'CLEAR':
                if args:
                    self.raise_error(SyntaxError, f"no arguments were expected, but {len(args)} argument(s) were given")

                self._cache.clear()

            case 'SET':
                if len(args) != 1:
                    self.raise_error(SyntaxError, f"1 argument was expected, but {len(args)} arguments were received")

                # [i] Any data type is allowed, 'cuz we cachin' it
                self.save_to_cache(args[0])
                
            case 'ECHORDIE': # [<] literally stands for Echo Or Die!!
                if len(args) != 2:
                    self.raise_error(SyntaxError, f"2 arguments were expected, but {len(args)} arguments were received")

                if not isinstance(args[0], (str, char)):
                    self.raise_error(TypeError, f"ECHORDIE was expecting data to write in the form of a string or a char, but received {str(type(args[0])).split(chr(39))[1]} instead")

                if not isinstance(args[1], (str, char)):
                    self.raise_error(TypeError, f"ECHORDIE was expecting a filepath to write to in the form of a string or a char, but received {str(type(args[1])).split(chr(39))[1]} instead")

                self.full_echo(*args)
                
            case 'SAFECIN': # [<] cin is mid, use this instead
                if len(args) < 1 or len(args) > 2:
                    self.raise_error(SyntaxError, f"1 or 2 arguments were expected, but {len(args)} arguments were received")

                if len(args) == 2:
                    if not isinstance(args[0], int):
                        self.raise_error(TypeError, f"a prompt length of type int was expected, but one of type {str(type(args[0])).split(chr(39))[1]} was received instead")

                    if not isinstance(args[1], (str, char)):
                        self.raise_error(TypeError, f"a prompt of type string or char was expected, but one of type {str(type(args[1])).split(chr(39))[1]} was received instead")

                    user_input: str | Literal[1] = self.cin(args[0], msg=f"{Fore.CYAN}{str(args[1])}{Fore.RESET}")
                    
                else:
                    if not isinstance(args[0], int):
                        self.raise_error(TypeError, f"a prompt length of type int was expected, but one of type {str(type(args[0])).split(chr(39))[1]} was received instead")

                    user_input: str | Literal[1] = self.cin(args[0])

                while user_input == 1:
                    user_input = self.cin(args[0], msg=f'{Fore.RED}Please give a correct input: {Fore.RESET}')

                if len(user_input) < args[0]:
                    user_input = f'{user_input}{" " * (args[0] - len(user_input))}'[:args[0] + 1]

                self._cache.set_cache(user_input) # [i] it's a safe sin, I MEAN, cin eh eh

            case 'YAYORNAY': # [i] a bit like a modified cin or sorts
                if args:
                    self.raise_error(SyntaxError, f"0 arguments were expected, but {len(args)} arguments were received")

                user_input: str | Literal[1] = self.cin(1)

                while user_input not in ('y', 'n'):
                    user_input = self.cin(1, msg=f"{Fore.RED}Please give a correct input ('y' or 'n'): {Fore.RESET}")

                self._specialized_cache.cache[0] = 0 if user_input[0] == 'n' else 1

            case 'RUN':
                if not args:
                    self.raise_error(SyntaxError, '1 or more arguments were expected, but none were received')

                if len(args) > 1:
                    self.run(args[0], *args[1:])

                else:
                    self.run(args[0])

            case 'PKGRUN':
                if not args:
                    self.raise_error(SyntaxError, '1 or more arguments were expected, but none were received')

                self.run(self._pkgcmd, *args)

            case 'PIPRUN':
                if not args:
                    self.raise_error(SyntaxError, '1 or more arguments were expected, but none were received')

                self.run(self._pippath, *args)

            case 'NPMRUN':
                if not args:
                    self.raise_error(SyntaxError, '1 or more arguments were expected, but none were received')

                self.run(self._npmpath, *args)

            case 'INVERT':
                if args:
                    self.raise_error(SyntaxError, f'no arguments were expected, but {len(args)} arguments were received')

                bool_val = self._specialized_cache.cache[0]
                self._specialized_cache.cache[0] = 0 if bool_val == 1 else 1

    def install_requirements(self) -> Literal[0]:
        self._flag_marker.toggle() # [i] this will trigger ContenterX requirement installation
        return 0

    def init(self) -> Literal[0]:
        raw_lines: list[str] = self._script.split('\n')
        parsed_script: str = ''

        for line in raw_lines:
            trimmed_line: str = line.strip()

            if not trimmed_line:
                continue

            if trimmed_line.startswith('//'):
                continue

            parsed_script += trimmed_line

        del raw_lines

        statements: list[str] = parsed_script.split(';')

        self.InterpreterRunning = True
        self.statement = 0

        while self.InterpreterRunning:
            try:
                self.handle_statement(statements[self.statement])

            except IndexError:
                break # [i] we're done here!

            self.statement += 1
            self._cwd = os.getcwd()

        return 0


def _local_req_inst(_i: Interpreter, pip: str, npm: str, pkg: str, cx: str, pkg_inst: str, bin_path: str):
    pip_reqs: list[str] = _i._requirements['pip']
    npm_reqs: list[str] = _i._requirements['npm']
    sys_reqs: list[str] = _i._requirements['system']
    bin_reqs: list[str] = _i._requirements['binary']
    cx_reqs: list[str] = _i._requirements['cx']
    
    for requirement in pip_reqs:
        subprocess.run([pip, 'install', requirement], text=True, capture_output=False)
        print('')
        
    for requirement in npm_reqs:
        subprocess.run([npm, 'install', requirement], text=True, capture_output=False)
        print('')
        
    for requirement in sys_reqs:
        subprocess.run([pkg, pkg_inst, requirement], text=True, capture_output=False)
        print('')
        
    for requirement in cx_reqs:
        subprocess.run([cx, 'install', requirement], text=True, capture_output=False)
        print('')
        
    for requirement in bin_reqs:
        print(f'{Fore.BLUE}▻ Fetching data...{Fore.RESET}')
        
        try:
            response: requests.Response = requests.get(requirement, timeout=1.5)# /-/ , allow_redirects=False)
            response.raise_for_status()
            
        except Exception as e:
            print(f'{Fore.RED}⌦ Could not fetch data.{Fore.RESET} Moving on to the next requirement: {e}...')
            continue
        
        else:
            print(f'{Fore.GREEN}✓ Got a response!{Fore.RESET}')
        
        path = os.path.join(bin_path, requirement.split('/')[-1])
        
        print(f"{Fore.BLUE}▻ Writing to '{path}'{Fore.RESET}")
        
        try:
            with open(path, 'wb') as f:
                f.write(response.content)
                
        except Exception as e:
            print(f'{Fore.RED}⌦  Could not finish writing to the path above.{Fore.RESET} Error details: {e}')
            continue
        
        print(f"{Fore.GREEN}✓ Finish writing to '{path}'!\n✓ Installation of {os.path.basename(path)} was successful!{Fore.RESET}\n\n")
        
    print(f'{Fore.GREEN}✓ Finished installing all requirements.{Fore.RESET}')


def _init_local_interpreter(pkg: str, pip: str, npm: str, cx: str, bin_path: str, pkg_inst: str, cache_size: int):
    Running = True
    interpreter = None
    reqs = None
    cache = None
    special = None
    flag = FlagMarker(lambda: _local_req_inst(interpreter, pip, npm, pkg, cx, pkg_inst, bin_path))
    termination = "TERMINATE;"

    while Running:
        statement: str = input(f'{Fore.BLUE}>> {Fore.RESET}')
        
        if statement.strip() == termination:
            print(f"{Fore.YELLOW}Goodbye :){Fore.RESET}")
            Running = False
        
        if statement.strip().startswith('TERMINATE') and statement.strip() != termination:
            print(f"{Fore.CYAN}Note: {Fore.RESET}If you wish to terminate the Interpreter, press {Fore.RED}Ctrl + C{Fore.RESET} or insert {Fore.RED}TERMINATE;{Fore.RESET} with no arguments")
        
        interpreter = Interpreter(statement, cache_size, flag, pkg, pip, npm)

        if cache is not None:
            interpreter._cache = cache # [i] apply existing cache

        if special is not None:
            interpreter._specialized_cache = special

        if reqs is not None:
            interpreter._requirements = reqs

        try:
            interpreter.init()

        except (SyntaxError, TypeError, ValueError, struct.error, CacheOverflow) as e:
            print(f'{Fore.RED}⌦  Your statement is incorrect.{Fore.RESET} Error details: {e}')

        else:
            cache = interpreter._cache
            reqs = interpreter._requirements
            special = interpreter._specialized_cache
            print('')
            termination = f"{'!' if special.cache[0] == 0 else ''}TERMINATE;"

def _init_file_interpreter(file: str, pkg: str, pip: str, npm: str, cx: str, bin_path: str, pkg_inst: str, cache_size: tuple[int, int]):
    flag = FlagMarker(lambda: _local_req_inst(interpreter, pip, npm, pkg, cx, pkg_inst, bin_path))

    try:
        with open(file, 'r', encoding='utf-8') as f:
            script = '\n'.join(f.read().split('\n')[1:]) if cache_size[1] else f.read()

    except Exception as e:
        print(f'{Fore.RED}⌦  Could not load script succesfully.{Fore.RESET} Error details: {e}\n{Fore.BLUE}Goodbye :({Fore.RESET}')
        sys.exit()

    interpreter = Interpreter(script, cache_size[0], flag, pkg, pip, npm)
    interpreter.init()

    print('')


def _get_cache_size_declaration(file: str) -> tuple[int, int]:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data: str = f.read()

    except Exception as e:
        print(f'{Fore.RED}⌦  Could not load script succesfully.{Fore.RESET} Error details: {e}\n{Fore.BLUE}Goodbye :({Fore.RESET}')
        sys.exit()

    if not data:
        print(f'{Fore.RED}⌦  Script is empty.{Fore.RESET}\n{Fore.BLUE}Goodbye :({Fore.RESET}')
        sys.exit()

    if re.match("[0-9]+", data.split('\n', maxsplit=1)[0]):
        return (int(data.split('\n', maxsplit=1)[0]), 1)

    return (256, 0)


def _handle_arguments(args):
    PRESET_TABLE = {
        "debian": ['apt', 'install'],
        "arch": ['pacman', '-S'],
        "windows": ['winget', 'install'],
        "cx": ['contenterx', 'install'],
        "disabled": ["", ""]
    }

    if args.where:
        print(f'\n{Fore.MAGENTA}The CX Setup Interpreter can be found at local path: {Fore.LIGHTCYAN_EX}\033[4m{__file__}{Style.RESET_ALL}')
        os._exit(0)
        
    if args.docs:
        print(f'\n{Fore.MAGENTA}The CX Setup documentation can be found online at: {Fore.LIGHTCYAN_EX}\033[4m{DOCS_URL}{Style.RESET_ALL}')        
        os._exit(0)

    if args.preset in ('debian', 'arch', 'windows', 'cx', 'disabled'):
        if args.file:
            _init_file_interpreter(args.file, PRESET_TABLE[args.preset][0], args.pip, args.npm, args.contenterx, args.binpath, PRESET_TABLE[args.preset][0], _get_cache_size_declaration(args.file))

        else:
            _init_local_interpreter(PRESET_TABLE[args.preset][0], args.pip, args.npm, args.contenterx, args.binpath, PRESET_TABLE[args.preset][0], args.allocate)

    else:
        if args.file:
            _init_file_interpreter(args.file, args.pkgmanager, args.pip, args.npm, args.contenterx, args.binpath, args.pkg_install_argument, _get_cache_size_declaration(args.file))

        else:
            _init_local_interpreter(args.pkgmanager, args.pip, args.npm, args.contenterx, args.binpath, args.pkg_install_argument, args.allocate)
    

if __name__ == '__main__':
    # [*] Real-time interpreter hooray
    parser = ArgumentParser(NAME, description='Interpreter for CX Setup Files and Instructions')
    
    print(f"""\n\n{Fore.YELLOW}      ███              █████████  █████ █████        █████████            █████                                    ███     
 ███ ░███  ███        ███░░░░░███░░███ ░░███        ███░░░░░███          ░░███                                ███ ░███  ███
░░░█████████░        ███     ░░░  ░░███ ███        ░███    ░░░   ██████  ███████   █████ ████ ████████       ░░░█████████░ 
  ░░░█████░         ░███           ░░█████         ░░█████████  ███░░███░░░███░   ░░███ ░███ ░░███░░███        ░░░█████░   
   █████████        ░███            ███░███         ░░░░░░░░███░███████   ░███     ░███ ░███  ░███ ░███         █████████  
 ███░░███░░███      ░░███     ███  ███ ░░███        ███    ░███░███░░░    ░███ ███ ░███ ░███  ░███ ░███       ███░░███░░███
░░░  ░███ ░░░        ░░█████████  █████ █████      ░░█████████ ░░██████   ░░█████  ░░████████ ░███████       ░░░  ░███ ░░░ 
     ░░░              ░░░░░░░░░  ░░░░░ ░░░░░        ░░░░░░░░░   ░░░░░░     ░░░░░    ░░░░░░░░  ░███░░░             ░░░      
                                                                                              ░███                         
                                                                                              █████                        
                                                                                             ░░░░░                         
                                                                                             
{Fore.RED}{AUTHOR}{Fore.RESET} * {Fore.GREEN}{LICENSE} License{Fore.RESET} * {Fore.MAGENTA}{YEAR}{Style.RESET_ALL}\n{Fore.YELLOW}{VERSION}{Fore.RESET} * {Fore.BLUE}\033[4m{GITHUB}{Style.RESET_ALL}\n""")

    parser.add_argument("--file", "-f", type=str, default="", help=f"{Fore.GREEN}specify a file to run{Fore.RESET} instead of simply launching the Interpreter's TUI ({Fore.BLUE}path as str{Fore.RESET}, defaults to {Fore.BLUE}no file (launches the TUI){Fore.RESET})")
    parser.add_argument("--preset", "-P", type=str, default="none", help=f"{Fore.GREEN}specify a preset to use instead of manually defining arguments for the interpreter{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}none{Fore.RESET})")
    parser.add_argument("--pkgmanager", "-m", "-k", type=str, default="pacman", help=f"{Fore.GREEN}locate the {Fore.RED}package manager{Fore.GREEN} to use{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}pacman{Fore.RESET})")
    parser.add_argument("--binpath", "--bp", "-b", type=str, default=os.path.expanduser('~/.local/bin/'), help=f"{Fore.GREEN}specify the path to install {Fore.RED}the binaries to{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}{os.path.expanduser('~/.local/bin/')}{Fore.RESET})")
    parser.add_argument("--allocate", "-a", type=int, default=256, help=f"{Fore.GREEN}start a session with X bytes for cache{Fore.RESET} ({Fore.BLUE}int{Fore.RESET}, defaults to {Fore.BLUE}256{Fore.RESET})")
    parser.add_argument("--contenterx", "--cx", "-c", type=str, default='contenterx', help=f"{Fore.GREEN}locate {Fore.RED}ContenterX/CX{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}globally installed ContenterX{Fore.RESET})")
    parser.add_argument("--pip", "-p", type=str, default='pip', help=f"{Fore.GREEN}locate {Fore.RED}pip{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}globally installed pip{Fore.RESET})")
    parser.add_argument("--npm", "-n", type=str, default='npm', help=f"{Fore.GREEN}locate {Fore.RED}npm{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}globally installed npm{Fore.RESET})")
    parser.add_argument("--pkg-install-argument", "--pkg-inst", "-I", type=str, default='-S', help=f"{Fore.GREEN}specify the argument to use with the {Fore.RED}package manager to install dependencies{Fore.RESET} ({Fore.BLUE}str{Fore.RESET}, defaults to {Fore.BLUE}-S{Fore.RESET})")
    parser.add_argument("--where", "-W", action="store_true", help=f"{Fore.GREEN}locate the interpreter{Fore.RESET} on your device")
    parser.add_argument("--docs", "-D", "--documentation", action="store_true", help=f"visit the {Fore.GREEN}online documentation{Fore.RESET}")
    
    _handle_arguments(parser.parse_args())
