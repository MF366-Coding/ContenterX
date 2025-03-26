from sys import platform as sysname
from platform import machine as arch
import os
import secrets
import subprocess


curfile = __file__
PY = 'python' if sysname == 'win32' else 'python3'


class InvalidUseOfAny(ValueError): ...
class MissingSentence(ValueError): ...
class MissingBackslash(ValueError): ...
class InvalidStatement(ValueError): ...


class MFRoadParser:
    """
    MFRoad is a small markup language designed to do different things based on what OS, distro (if applicable) and system architecture the user uses.
    
    This is a crappy ass small implementation of a half functional parser for MFRoad. Feel free to use it in projects or to verify if your MFRoads are valid.
    """
    
    def __init__(self, data: list[str], tab_space: str = '    '):
        self._data: list[str] = []
        self._code: str = ''
        self.TAB = tab_space
        
        for index, line in enumerate(data, 0):
            if line.count('\\') % 2:
                raise MissingBackslash(f'line {index + 1}: each line must have an even amount of backslashes')
            
            if not (line.replace(' ', '')):
                continue
            
            if line.startswith(('#', '//')):
                continue
            
            if len(line.split(':')) != 2:
                raise MissingSentence(f"line {index + 1}: each line must have exactly 2 main sentences (only the second one can have subsentences)")
            
            self._data.append(line)
            
    def parse(self):
        self._code = 'def mfroad(system: str, architecture: str) -> str:' # [i] system will take the value of a distro if it is one
        aux: list[str] | None = None
        
        for line in self._data:
            aux = None
            aux = line.split(':')
            
            if aux[0] == 'any':                
                # [i] No matter the OS, this will run                
                if len(aux[1].split('<<')) > 1:
                    if aux[1].split('<<')[0] == 'any':
                        self._code += f'\n{self.TAB}print("{"\n".join(aux[1].split("<<")[1:])}")' # [i] If it's a COUT, just run it
                    
                    else:
                        self._code += f'\n{self.TAB}if "{aux[1].split("<<")[0]}" == architecture:\n{self.TAB * 2}print("{"\n".join(aux[1].split("<<")[1:])}")'

                elif len(aux[1].split('!!!')) > 1:
                    if aux[1].split('!!!')[0] == 'any':
                        self._code += f"\n{self.TAB}raise Exception('{' - '.join(aux[1].split('!!!')[1:])}')" # [i] If it's a RAISE, just raise it
                        # [!!] this should never be done, as it means the error is being raised no matter what

                    else:
                        self._code += f'\n{self.TAB}if "{aux[1].split("!!!")[0]}" == architecture:\n{self.TAB * 2}raise Exception("{" - ".join(aux[1].split("!!!")[1:])}")'
                        
                elif len(aux[1].split('???')) > 1:
                    if aux[1].split('???')[0] == 'any':
                        raise InvalidUseOfAny('cannot use "any" under such context - any:any???<path> is not allowed') # [i] any:any followed by a path is not valid as it literally means "screw this, anything will work out"
                    
                    else:
                        self._code += f'\n{self.TAB}if "{aux[1].split("???")[0]}" == architecture:\n{self.TAB * 2}return "{aux[1].split("???")[1]}"'
                        
                else:
                    raise InvalidStatement('a statement must have a path identifier (???), an abortion (!!!) or an output (<<)')
                
            else:
                if len(aux[1].split('<<')) > 1:
                    if aux[1].split('<<')[0] == 'any':
                        self._code += f'\n{self.TAB}if system == "{aux[0]}":\n{self.TAB * 2}print("{"\n".join(aux[1].split("<<")[1:])}")' # [i] the architecture doesn't matter
                    
                    else:
                        self._code += f'\n{self.TAB}if ("{aux[1].split("<<")[0]}" == architecture) and (system == "{aux[0]}"):\n{self.TAB * 2}print("{"\n".join(aux[1].split("<<")[1:])}")'

                elif len(aux[1].split('!!!')) > 1:
                    if aux[1].split('!!!')[0] == 'any':
                        self._code += f"\n{self.TAB}if system == '{aux[0]}':\n{self.TAB * 2}raise Exception('{' - '.join(aux[1].split('!!!')[1:])}')"

                    else:
                        self._code += f'\n{self.TAB}if ("{aux[1].split("!!!")[0]}" == architecture) and (system == "{aux[0]}"):\n{self.TAB * 2}raise Exception("{" - ".join(aux[1].split("!!!")[1:])}")'
                        
                elif len(aux[1].split('???')) > 1:
                    if aux[1].split('???')[0] == 'any':
                        self._code += f'\n{self.TAB}if system == "{aux[0]}":\n{self.TAB * 2}return "{"\n".join(aux[1].split("???")[1:])}"' # [i] the architecture doesn't matter
                        
                    else:
                        self._code += f'\n{self.TAB}if ("{aux[1].split("???")[0]}" == architecture) and (system == "{aux[0]}"):\n{self.TAB * 2}return "{aux[1].split("???")[1]}"'
                        
                else:
                    raise InvalidStatement('a statement must have a path identifier (???), an abortion (!!!) or an output (<<)')
                
        self._code += f'\n{self.TAB}return'
        # [*] If nothing else works, return None
        
        return self._code # [i] in case the user wants to see their mfroad to Python totally 100% accurate bug-free "translation"
    
    def exec(self, system_or_distro: str = sysname, architecture: str = arch()) -> None:
        return exec(f"{self._code}\n\nmfroad('{system_or_distro}', '{architecture}')")
    
    def write_to_garbage_file(self, system_or_distro: str = sysname, architecture: str = arch()) -> str:
        TOKEN = secrets.token_urlsafe(16)
        
        with open(f'garbage/{TOKEN}.py', 'w', encoding='utf-8') as f:
            f.write(f"{self._code}\n\nif __name__ == '__main__':\n{self.TAB}print(mfroad('{system_or_distro}', '{architecture}'))\n\n")
            
        return TOKEN
    
    def run_garbage(self, token: str, py: str = PY) -> str:
        result = subprocess.run([PY, os.path.join('garbage', f'{token}.py')], text=True, capture_output=True)
        return result.stdout
    
    @property
    def mfroad(self) -> list[str]:
        return self._data


def init(data: str, tabsize: int = 4) -> MFRoadParser:
    raw_data_lines = data.split('\n')
    formatted_data = []
    
    for i in raw_data_lines:
        formatted_data += i.split(';')
    
    return MFRoadParser(formatted_data, ' ' * tabsize)


if __name__ == '__main__':
    a = """win32:any<<Windows detected!;
# Comment??;
// Another one, I guess;
linux:AMD64???LICENSE;
darwin:any!!!MacOS not supported lolz;
win32:ARM64???README.md;
linux:any???__init__.py;# This will act as a anything else type of thing;
win32:any???mfroad.py;
win32:AMD64???cxsetup.py;
//any:any???mfroad.py;
any:any<<what os fr?;
"""
    b = init(a)
    print(b.parse())
    print('\n\n')
    c = b.write_to_garbage_file()
    print(b.run_garbage(c))
            