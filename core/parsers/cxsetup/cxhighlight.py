from rich.console import Console
from rich.text import Text
import re
import os
import json
from colorama import Fore, Style
from cxconst import DOCS_URL, AUTHOR, YEAR, LICENSE
from argparse import ArgumentParser


VERSION = 'v1.0.0'
DEFAULT_COLORMAP = {
    "FUNCTION": "bold red",
    "NEGATION": "bold magenta",
    "SEPARATOR": "dim yellow",
    "SEMICOLON": "dim bold italic red",
    "COMMENT": "dim italic white",
    "NUMBER": "bold blue",
    "STRING": "green",
    "CACHE_GRAB": "bold cyan",
    "TEXT": "white",
    "UNREACHABLE_CODE": "dim italic white"
}


def syntax_highlight(code: str, colormap: dict[str, str] | None = None, ignore_unreachable_code: bool = True):
    colormap = DEFAULT_COLORMAP if colormap is None else colormap
    lines = code.splitlines()
    text = Text()
    terminated = [False, False]
    comment = False

    for line in lines:
        if ignore_unreachable_code:
            terminated = [False, False]

        if line.strip().startswith(('#', '//')):
            text.append(f'{line}\n', colormap['COMMENT'])
            continue

        tokens = re.split(r'(\s+|".*?"|[?:;]|[\?]{2}|c[0-9]+:[0-9]+[el]:[0-9]+:[0-9]+:[rlbn])', line)
        semicolon = False
        comment = False

        for token in tokens:
            if ignore_unreachable_code:
                terminated = [False, False]

            if sum(terminated) == 2:
                text.append(token, colormap['UNREACHABLE_CODE'])
                continue

            if not token.strip():
                text.append(token, colormap['TEXT'])
                continue

            token = token.strip()

            if comment:
                text.append(token, colormap['COMMENT'])
                continue

            # [*] Negations
            if token in {'!INVERT', '!ENDL', '!ENDL2', '!GETPASS', '!COUT', '!ECHO', '!CIN', '!TERMINATE', '!REQUIRES', '!REQINSTALL', '!STYLE', '!FORE', '!BACK', '!CLEAR', '!SET', '!ECHORDIE', '!SAFECIN', '!YAYORNAY', '!PKGRUN', '!RUN', '!PIPRUN', '!NPMRUN'}:
                text.append(token, colormap['NEGATION'])
                semicolon = False

                if token == "!TERMINATE":
                    terminated[1] = True

                continue

            # [*] Keywords/Functions
            if token in {'INVERT', 'ENDL', 'ENDL2', 'GETPASS', 'COUT', 'ECHO', 'CIN', 'TERMINATE', 'REQUIRES', 'REQINSTALL', 'STYLE', 'FORE', 'BACK', 'CLEAR', 'SET', 'ECHORDIE', 'SAFECIN', 'YAYORNAY', 'PKGRUN', 'RUN', 'PIPRUN', 'NPMRUN'}:
                text.append(token, colormap['FUNCTION'])
                semicolon = False

                if token == "TERMINATE":
                    terminated[0] = True

                continue

            # [*] Strings
            if re.fullmatch(r'"[^"]*"', token):
                text.append(token, colormap['STRING'])
                semicolon = False
                continue

            # [*] Cache Grabs
            if re.match(r'c[0-9]+:[0-9]+[el]:[0-9]+:[0-9]+:[rlbn]', token):
                text.append(token, colormap['CACHE_GRAB'])
                semicolon = False
                continue

            # [*] Floats
            if re.fullmatch(r'[0-9]+\.[0-9]+', token) or re.fullmatch('[0-9]+[e][0-9]+', token):
                text.append(token, colormap['NUMBER'])
                semicolon = False
                continue

            # [*] Integer
            if re.fullmatch(r'[0-9]+', token):
                text.append(token, colormap['NUMBER'])
                semicolon = False
                continue

            # [*] Semicolon
            if token == ';':
                text.append(token, colormap['SEMICOLON'])
                semicolon = True
                continue

            # [*] Comment
            if token.startswith('//') and semicolon:
                comment = True
                semicolon = False
                text.append(token, colormap['COMMENT'])
                continue

            # [*] Argument Separator
            if token.strip() == '?':
                text.append(token, colormap['SEPARATOR'])
                semicolon = False
                continue

            # [*] Normal text
            text.append(token, colormap['TEXT'])

        text.append('\n', colormap['TEXT'])

    return text


def get_code_from_file(file: str) -> str:
    if not file.lower().endswith('.cxsetup'):
        raise NameError('file must be a CX Setup script')

    with open(file, 'r', encoding='utf-8') as f:
        data = f.read()

    return data


def get_colormap_from_file(file: str) -> dict[str, str]:
    if not file.lower().endswith('.json'):
        raise NameError('colormaps must be in JSON format')

    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def _handle_arguments(args):
    if args.where:
        print(f'\n{Fore.MAGENTA}The CX Setup Syntax Highlighter can be found at local path: {Fore.LIGHTCYAN_EX}\033[4m{__file__}{Style.RESET_ALL}')
        os._exit(0)

    if args.docs:
        print(f'\n{Fore.MAGENTA}The CX Setup documentation can be found online at: {Fore.LIGHTCYAN_EX}\033[4m{DOCS_URL}{Style.RESET_ALL}')
        os._exit(0)

    colormap = None

    if args.colormap:
        try:
            colormap = get_colormap_from_file(args.colormap)

        except Exception as e:
            print(f'{Fore.RED}⌦  Could not load colormap succesfully (reverting to the default one).{Fore.RESET} Error details: {e}')
            colormap = None

    try:
        code = get_code_from_file(args.file)

    except Exception as e:
        print(f'{Fore.RED}⌦  Could not load script succesfully.{Fore.RESET} Error details: {e}\n{Fore.BLUE}Goodbye :({Fore.RESET}')
        os._exit(0)

    console = Console()
    text = syntax_highlight(code, colormap, not args.highlight_unreachable)
    console.print(text)
    return 0


if __name__ == '__main__':
    parser = ArgumentParser('CX Setup Syntax Highlighter', description='Syntax Highlighter for CX Setup Files and Instructions')

    print(f"""\n\n{Fore.YELLOW}      ███              █████████  █████ █████        █████████                        █████   █████  ███           █████                 ███
 ███ ░███  ███        ███░░░░░███░░███ ░░███        ███░░░░░███                      ░░███   ░░███  ░░░           ░░███             ███ ░███  ███
░░░█████████░        ███     ░░░  ░░███ ███        ░███    ░░░  █████ ████ ████████   ░███    ░███  ████   ███████ ░███████        ░░░█████████░
  ░░░█████░         ░███           ░░█████         ░░█████████ ░░███ ░███ ░░███░░███  ░███████████ ░░███  ███░░███ ░███░░███         ░░░█████░
   █████████        ░███            ███░███         ░░░░░░░░███ ░███ ░███  ░███ ░███  ░███░░░░░███  ░███ ░███ ░███ ░███ ░███          █████████
 ███░░███░░███      ░░███     ███  ███ ░░███        ███    ░███ ░███ ░███  ░███ ░███  ░███    ░███  ░███ ░███ ░███ ░███ ░███        ███░░███░░███
░░░  ░███ ░░░        ░░█████████  █████ █████      ░░█████████  ░░███████  ████ █████ █████   █████ █████░░███████ ████ █████      ░░░  ░███ ░░░
     ░░░              ░░░░░░░░░  ░░░░░ ░░░░░        ░░░░░░░░░    ░░░░░███ ░░░░ ░░░░░ ░░░░░   ░░░░░ ░░░░░  ░░░░░███░░░░ ░░░░░            ░░░
                                                                 ███ ░███                                 ███ ░███
                                                                ░░██████                                 ░░██████
                                                                 ░░░░░░                                   ░░░░░░

{Fore.RED}{AUTHOR}{Fore.RESET} * {Fore.GREEN}{LICENSE} License{Fore.RESET} * {Fore.MAGENTA}{YEAR}{Style.RESET_ALL}\n{Fore.YELLOW}{VERSION}{Fore.RESET} * {Fore.BLUE}\033[4mhttps://github.com/MF366-Coding/ContenterX/blob/main/core/parsers/cxhighlight.py{Style.RESET_ALL}\n""")

    parser.add_argument("file", type=str, help=f"{Fore.GREEN}specify a file to perform syntax highlighting on{Fore.RESET} ({Fore.BLUE}path as str{Fore.RESET})")
    parser.add_argument("--colormap", "-c", type=str, default="", help=f"{Fore.GREEN}specify a colormap to use instead of the default one{Fore.RESET} ({Fore.BLUE}path as str{Fore.RESET}, defaults to {Fore.BLUE}none{Fore.RESET})")
    parser.add_argument("--highlight-unreachable", "-u", action='store_true', default=False, help=f"{Fore.GREEN}apply syntax highlighting to unreachable code{Fore.RESET} (defaults to {Fore.BLUE}NO{Fore.RESET})")
    parser.add_argument("--where", "-W", action="store_true", help=f"{Fore.GREEN}locate the highlighter{Fore.RESET} on your device")
    parser.add_argument("--docs", "-D", "--documentation", action="store_true", help=f"visit the {Fore.GREEN}online documentation for CX Setup{Fore.RESET}")

    _handle_arguments(parser.parse_args())
