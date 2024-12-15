import sys
import keyboard
from typing import Any


class Screen:
    def __init__(self, title: str, initial_context, formatter, globals_affected: dict[str, Any]):
        self._TITLE = title
        self._CONTEXT = initial_context
        self._formatter = formatter
        self._globals = globals_affected
        
        self._formatter.set_viewport_title(self._TITLE)
        
    def send_value(self, id: str, value: Any):
        handled_value: tuple[str, Any] = self._CONTEXT.handle_value(id, value)
        self._globals[str(handled_value[0])] = handled_value[1]
    
    def refresh(self):
        self._formatter.clear_viewport()
        self._formatter.set_viewport_title(self._TITLE)
        sys.stdout.write(self._CONTEXT.format())
        
        key = keyboard.read_key()
        
        if key not in self._CONTEXT.events:
            key = '#DEFAULT#'
        
        what_to_run: list[str] = self._CONTEXT.events[key]
        
        for i in what_to_run:
            # [*] Case I: 'i' represents a Screen indication
            if i.startswith('#') and i.endswith('#'):
                if i.startswith("#GET_INPUT:::"):
                    input_val = input(i[13:-1])
                    self.send_value(i[13:-1], input_val)
                          
                match i:
                    case '#FORCEQUIT#':
                        sys.exit()
                        
                    case _:
                        pass
                        
            # [*] Case II: 'i' is a Callable
            i()
