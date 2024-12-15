from typing import Any
import keyboard


class Context:
    def __init__(self, value: str, events: dict[keyboard._Key, list[str]], keyword_formatters: dict[str, Any] | Any = None, title: str | None = None) -> None:
        self._VALUE: str = value
        self._EVENTS: dict[int | str, list[str]] = events
        self._TITLE = title
                
        if not keyword_formatters:
            keyword_formatters = {}
        
        self._FORMATTERS: dict[str, Any] = keyword_formatters
    
    def handle_value(self, id: str, value: Any):
        return id, value
    
    def format(self) -> str:
        if self._VALUE.count('{') == 0 or self._VALUE.count('}') == 0:
            return self._VALUE
        
        return self._VALUE.format(**self._FORMATTERS)
    
    def edit(self, new_value: str | tuple[str], char: str = '\n'):
        if isinstance(new_value, str):
            self._VALUE = new_value
            
        else:
            self._VALUE = char.join(new_value)
            
    def run_operation(self, operation: str, *args, **kwargs):
        return eval(f"{self}._VALUE.{operation}(*{args}, **{kwargs})")
    
    @property
    def title(self) -> str | None:
        return self._TITLE
    
    @title.setter
    def title(self, value: str) -> None:
        self._TITLE: str = value
        
    @property
    def events(self) -> dict[int | str, list[str]]:
        return self._EVENTS

    def __str__(self) -> str:
        return self._VALUE # [i] no formatting is you do __str__
 