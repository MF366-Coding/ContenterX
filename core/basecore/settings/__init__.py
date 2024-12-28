import json
from typing import Any
import sys


class Settings:
    def __init__(self, filepath: str, defaults: dict[str, Any]):
        self._path = filepath
        self._defaults = defaults
        
    def load_settings(self):
        """
        ## Settings.load_settings
        
        Load settings from a JSON file and handle various exceptions.
        
        :return int: 0 if settings are loaded successfully, 1 if file is not found or is a directory, 2 if there is a JSON or Unicode decode error, 3 for any other exceptions.
        """
        
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
            
            return 0
                
        except (FileNotFoundError, IsADirectoryError):
            self._settings = self._defaults
            return 1
        
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._settings = self._defaults
            return 2
        
        except Exception:
            self._settings = self._defaults
            return 3
            
    def save_settings(self):
        """
        ## Settings.save_settings

        Wrapper for `Settings.dump_object` that uses the cached settings as the object to dump.
        
        :return int: 0 if the settings are dumped successfully, 1 if there is a JSON or Unicode error, 2 for any other exceptions.
        """
        
        return self.dump_object(self._settings)
            
    def dump_object(self, dictionary: dict[str, Any]):
        """
        ## Settings.dump_object
        
        Dump a dictionary object to a JSON file and handle various exceptions.
        
        :param dict[str, Any] dictionary: The dictionary to overwrite the current settings with.
        :return int: 0 if the object is dumped successfully, 1 if there is a JSON or Unicode error, 2 for any other exceptions.
        """
        
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(dictionary, f, indent=4)
                
            return 0
        
        except IsADirectoryError: # [!] CRITICAL ERROR, oh noes!
            sys.exit(f"Cannot save the object to a directory: {self._path}")
        
        except (json.JSONDecodeError, UnicodeError):
            self.overwrite_settings(self._defaults)
            return 1
        
        except Exception:
            self.overwrite_settings(self._defaults)
            return 2
            
    def overwrite_settings(self, dictionary: dict[str, Any]):
        """
        ## Settings.overwrite_settings
        
        Overwrite the current settings with a provided dictionary and save them to the JSON file.
        
        :param dict[str, Any] dictionary: The dictionary to overwrite the current settings with.
        :return tuple[int, int]: A tuple containing the return types of the dumping and the loading.
        """
        
        a = self.dump_object(dictionary)
        b = self.load_settings()
        return a, b
