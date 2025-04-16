from dataclasses import dataclass
import re
from colorama import Fore


# [*] Patterns
CACHE_GRAB_PATTERN = re.compile("c[0-9]+:[0-9]+[el]:[0-9]+:[0-9]+:[rlbn]")
INTEGER_PATTERN = re.compile("[0-9]+")
FLOAT_PATTERN = re.compile(r"[0-9]+\.[0-9]+")


RECOGNIZED_KEYWORDS = {'!INVERT', '!ENDL', '!ENDL2', '!GETPASS', '!COUT', '!ECHO', '!CIN', '!TERMINATE', '!REQUIRES', '!REQINSTALL', '!STYLE', '!FORE', '!BACK', '!CLEAR', '!SET', '!ECHORDIE', '!SAFECIN', '!YAYORNAY', '!PKGRUN', '!RUN', '!PIPRUN', '!NPMRUN',
                       'INVERT', 'ENDL', 'ENDL2', 'GETPASS', 'COUT', 'ECHO', 'CIN', 'TERMINATE', 'REQUIRES', 'REQINSTALL', 'STYLE', 'FORE', 'BACK', 'CLEAR', 'SET', 'ECHORDIE', 'SAFECIN', 'YAYORNAY', 'PKGRUN', 'RUN', 'PIPRUN', 'NPMRUN'}


@dataclass
class Issue:
    line: int
    statement: int
    code: str
    message: str
    severity: int
    color: str

    def __str__(self) -> str:
        return f"[LINT] Line {self.line}: Global Statement {self.statement}: {self.code}: {self.message}"

    def as_pretty(self) -> str:
        return f"{Fore.LIGHTWHITE_EX}[LINT] {Fore.RESET}Line {Fore.MAGENTA}{self.line}{Fore.RESET}: Global Statement {Fore.MAGENTA}{self.statement}{Fore.RESET}: {self.color}{self.code}: {self.message}{Fore.RESET}"

    def as_json(self) -> dict[str, int | str]:
        return {
            "line": self.line,
            "statement": self.statement,
            "code": self.code,
            "message": self.message,
            "severity": self.severity # [i] starts at 1, cuz 0 is "Nothing to report"
        }

    def as_tuple(self) -> tuple[int, int, str, str, int]:
        return (self.line, self.statement, self.code, self.message, self.severity)


class ErrorCheckers:
    @staticmethod
    def e001_semicolon(line: str, lineno: int, ignore_list: list[str]) -> Issue | None:
        """
        E001 - Missing semicolon at the end of the line
        -----------------------
        ### Example
        ```cxsetup
        COUT ?? 42
        ```
        ### Instead, do:
        ```cxsetup
        COUT ?? 42;
        ```
        """

        if "E001" in ignore_list:
            return # [i] pretend nothing happened

        if lineno == 0 and re.fullmatch(INTEGER_PATTERN, line):
            return

        if not line.endswith(';'):
            return Issue(lineno + 1, -1, "E001", "Missing semicolon at the end of the line", 3, Fore.RED)

        return

    @staticmethod
    def e002_unknown_keyword(statement: str, lineno: int, statement_no: int, ignore_list: list[str]) -> Issue | None:
        """
        E002 - Unknown Keyword
        -----------------------
        ### Example
        ```cxsetup
        FOOBAR ?? "Hello!";
        ```

        ### Explanation
        - `FOOBAR` is not a recognized keyword
        """

        if "E002" in ignore_list:
            return

        if lineno == 0 and re.fullmatch(INTEGER_PATTERN, statement):
            return

        if statement.split('??', maxsplit=1)[0].strip().endswith(';'):
            if statement.split('??', masplit=1)[0][:-1].strip() not in RECOGNIZED_KEYWORDS:
                return Issue(lineno, statement_no, "E002", f"Unknown Keyword {statement.split('??', masplit=1)[0][:-1].strip()}", 3, Fore.RED)

            return

        if statement.split('??', masplit=1)[0].strip() not in RECOGNIZED_KEYWORDS:
            return Issue(lineno, statement_no, "E002", f"Unknown Keyword {statement.split('??', masplit=1)[0].strip()}", 3, Fore.RED)

        return

    @staticmethod
    def e003_arguments(statement: str, lineno: int, statement_no: int, ignore_list: list[str]):
        if "E003" in ignore_list:
            return

        parts = statement.split('??')


class Linter:
    def __init__(self):
        self.ISSUES: list[Issue] = []

    def lint_code():
        # TODO
        return 0
