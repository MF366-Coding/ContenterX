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
    
    def newline(self, count: int = 1) -> None:
        self.write('\n' * count)

    def write(self, __s: str, __stdout: bool = True) -> int | Any:
        __outputter = sys.stdout

        if not __stdout:
            __outputter = sys.stderr
        
        return __outputter.write(__s)

    def writelines(self, __iterable: list[str], __stdout: bool = True):
        __outputter = sys.stdout

        if not __stdout:
            __outputter = sys.stderr

        __outputter.writelines(__iterable)
        
    def clear_screen(self):
        self._formatter.clear_viewport()

    def change_context(self, new_context):
        self._cur_context = new_context
        self.clear_screen()

        self.write(self._cur_context.format())
        self._formatter.set_viewport_title(self._TITLE)
        self.read_input()
    
    def read_input(self):
        self.write(f"\n{'.' * 50}\n")
        
        key = keyboard.read_key()
        
        if key == 'shift':
            value = input('An input is required: ')
            handled_input = self._CONTEXT.handle_input(value)
            
            if isinstance(handled_input, str):
                self._CONTEXT.edit(handled_input)
                
            else:
                self.change_context(handled_input)
                
            return
        
        if key not in self._CONTEXT.events:
            self.clear_screen()
            self.write(f"{self._formatter.Fore.RED}Invalid Key Input!!{self._COLORMAP['RESET_ALL']}\n\n{str(self._cur_context)}")
            self.read_input()
            return

        event = self._CONTEXT.handle_key_press(key)
        
        if isinstance(event, str):
            self._CONTEXT.edit(event)
            
        else:
            self.change_context(event)

