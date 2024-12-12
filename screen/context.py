from typing import Any

class Context:
    def __init__(self, value: str, keyword_formatters: dict[str, Any] | Any = None, title: str | None = None) -> None:
        self._VALUE: str = value
        self._TITLE = title
        
        if not keyword_formatters:
            keyword_formatters = {}
        
        self._FORMATTERS: dict[str, Any] = keyword_formatters
        
    def format(self) -> str:
        if self._VALUE.count('{') == 0 or self._VALUE.count('}') == 0:
            return self._VALUE
        
        return self._VALUE.format(**self._FORMATTERS)
    
    @property
    def title(self):
        return self._TITLE

    def __str__(self) -> str:
        return self._VALUE # [i] no formatting is you do __str__
 