from dataclasses import dataclass
import re
from colorama import Fore


# [*] Patterns
CACHE_GRAB_PATTERN = re.compile("c[0-9]+:[0-9]+[el]:[0-9]+:[0-9]+:[rlbn]")


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
    def e001_semicolon(line: str, lineno: int):
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

        if lineno == 0:
            return

        # TODO


class Linter:
    def __init__(self):
        self.ISSUES: list[Issue] = []

    def lint_code():
        # TODO
        return 0
