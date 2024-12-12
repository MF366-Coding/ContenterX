from colorama.ansi import Fore, Back, Cursor, clear_screen, clear_line, code_to_chars, set_title
import sys
from typing import Any


def change_cursor_visibility(effect: int):
    match effect:
        case 1: # [i] hide the cursor
            sys.stdout.write("\033[?25l")
            
        case 2: # [i] enable cursor blinking
            sys.stdout.write("\033[?12h")
            
        case 3: # [i] disable cursor blinking
            sys.stdout.write("\033[?12l")
            
        case _: # [i] show the cursor
            sys.stdout.write("\033[?25h")


def clear_viewport(**kw):
    kw.pop('mode', 2)
    sys.stdout.write(clear_screen(2))


def wipe_line(**kw):
    kw.pop('mode', 2)
    sys.stdout.write(clear_line(2))


def set_effect(effect_code: int):
    return code_to_chars(effect_code)


def set_viewport_title(title: str):
    sys.stdout.write(set_title(title))


class Effect:
    RESET               = 0
    
    # *** Text Styles I *** #
    BOLD                = 1
    FAINT     = DIM     = 2
    ITALIC              = 3 # [i] not widely supported and sometimes might be treated as inverse or blink
    UNDERLINE           = 4
    
    # *** Blinking *** #
    SLOW_BLINK          = 5
    FAST_BLINK          = 6 # [i] not widely supported
    
    # *** Color Styles I *** #
    NEGATIVE            = 7
    CONCEAL             = 8 # [i] not widely supported
    
    # *** Text Styles II *** #
    STRIKETHROUGH       = 9
    PRIMARY_FONT        = 10
    ALT_FONT_1          = 11
    ALT_FONT_2          = 12
    ALT_FONT_3          = 13
    ALT_FONT_4          = 14
    ALT_FONT_5          = 15
    ALT_FONT_6          = 16
    ALT_FONT_7          = 17
    ALT_FONT_8          = 18
    ALT_FONT_9          = 19
    GOTHIC_FONT         = 20 # [i] rarely supported
    DOUBLE_UNDERLINE    = 21 # [i] disables bold on several terminals instead of doubly underlining text
    RESET_BOLD          = 22
    RESET_ITALIC        = 23
    RESET_UNDERLINED    = 24
    DISABLE_BLINKING    = 25
    POSITIVE            = 27
    REVEAL              = 28
    RESET_STRIKETHROUGH = 29
    OVERLINED           = 53
    RESET_OVERLINED     = 55


class Formatter:
    def __init__(self, include_builtin: bool = True, user_values: dict[str, Any] | None = None):
        if (not include_builtin) and (not user_values):
            raise ValueError('if include_builtin is False, there must use defined values and vice-versa')
        
        self._FORMATTING = {}
        
        if include_builtin:
            for i in dir(Fore):
                if i.startswith('__') and i.endswith('__'):
                    continue
                
                self._FORMATTING[f"Fore.{i}"] = eval(f"Fore.{i}")
                
            for i in dir(Back):
                if i.startswith('__') and i.endswith('__'):
                    continue
                
                self._FORMATTING[f"Back.{i}"] = eval(f"Back.{i}")
                
            for i in dir(Cursor):
                if i.startswith('__') and i.endswith('__'):
                    continue
                
                self._FORMATTING[f"Cursor.{i}"] = eval(f"Cursor.{i}")
                
            for i in dir(Effect):
                if i.startswith('__') and i.endswith('__'):
                    continue
                
                self._FORMATTING[i] = eval(f"Effect.{i}")
                
        if user_values:
            for k, v in user_values:
                self._FORMATTING[k] = v
                
    def as_dict(self):
        return self._FORMATTING.copy()
    
    def as_dict_raw(self):
        return self._FORMATTING
