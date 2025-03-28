"""
Interpreter for CX Setup Scripts (`cxsetup.py`)
-----------------------------
This program was made by MF366 and is licensed under the permissive MIT License.

If you use this shitty ass interpreter in a project of yours, I'd appreciate it if you credited me, by keeping this docstring here, for example.

Thank you!
"""


from enum import IntEnum
from typing import Any, Literal
import struct


class CacheOverflow(Exception): ...


class char(object):
    def __init__(self, byte: bytes) -> None:
        if not byte:
            raise ValueError('one byte must be given')

        self.CHAR: bytes = byte[0:1]

    def ToEncodedString(self, encoding: str = 'utf-8') -> str:
        return str(self.CHAR, encoding)

    def ToInt(self) -> int:
        return(ord(self.CHAR))

    def AsBytes(self) -> bytes:
        return self.CHAR

    def ToBool(self) -> bool:
        return self.ToInt() != 0

    @classmethod
    def FromString(cls, string: str, *, encoding: str = 'utf-8'):
        return cls(bytes(string, encoding=encoding))

    from_string = FromString
    to_int = ToInt
    to_bool = ToBool
    to_string = to_encoded_string = ToEncodedString
    as_bytes = AsBytes

    def __str__(self) -> str:
        return str(self.CHAR, 'utf-8')

    def __len__(self) -> int:
        return 1 # [i] even if empty, it's 1

    def __repr__(self) -> str:
        return f"char({self.CHAR.__repr__()})"

    def __eq__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR == other.CHAR

        if isinstance(other, bytes):
            return self.CHAR == other

        if isinstance(other, str):
            return self.__str__() == other

        if isinstance(other, int):
            return self.ToInt() == other

        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR < other.CHAR

        if isinstance(other, bytes):
            return self.CHAR < other

        if isinstance(other, str):
            return self.__str__() < other

        if isinstance(other, int):
            return self.ToInt() < other

        return False

    def __le__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR <= other.CHAR

        if isinstance(other, bytes):
            return self.CHAR <= other

        if isinstance(other, str):
            return self.__str__() <= other

        if isinstance(other, int):
            return self.ToInt() <= other

        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR > other.CHAR

        if isinstance(other, bytes):
            return self.CHAR > other

        if isinstance(other, str):
            return self.__str__() > other

        if isinstance(other, int):
            return self.ToInt() > other

        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, char):
            return self.CHAR >= other.CHAR

        if isinstance(other, bytes):
            return self.CHAR >= other

        if isinstance(other, str):
            return self.__str__() >= other

        if isinstance(other, int):
            return self.ToInt() >= other

        return False

    def __hash__(self) -> int:
        return hash(self.CHAR)



class DataType(IntEnum):
    VOID = 0
    INTEGER = 1
    FLOAT = 2
    STRING = 3
    BOOLEAN = 4
    CHAR = 5
    GARBAGE = 6


class Cache:
    def __init__(self, reserved_bytes: int):
        self.cache = bytearray(reserved_bytes)
        self._RESERVED = reserved_bytes
        self._pointer = 0

    def __len__(self):
        length = len(self.cache)

        if length > self._RESERVED:
            raise CacheOverflow(f"the cache is taking up {self._RESERVED - length} byte(s) more than it should")

        return length

    def __str__(self) -> str:
        return str(bytes(self.cache.copy()), 'utf-8')

    def __repr__(self):
        return self.__str__()

    def get_cache(self, pos: int, len: int = -2, end: int = -2, step: int = 1) -> bytes:
        """
        Cache.get_cache
        ------------------

        Collects and returns cache values.

        :param int pos: starting position for cache grab
        :param int len: length of cache grab, defaults to -2 meaning DISABLED
        :param int end: alternatively, end position of cache grab; defaults to -2 meaning DISABLED
        :param int step: _description_, defaults to 1
        :raises ValueError: both len and end were given - only one is allowed per call
        :return bytes: cached values as bytes
        """
        
        if (len == end) and len != -2: # [i] we use -2 cuz -1 stands for LAST_POS
            raise ValueError('only one of the arguments len and end should be given values')

        if (len == end):
            end = pos + 1

        elif len > 0:
            end = pos + len

        else:
            end = max(end, -1)

        return bytes(self.cache.copy())[pos:end:step]

    def readable_cache(self, cached_bytes: bytearray, data_type: int) -> bytes | bool | int | str | char | float | Any:
        """
        Cache.readable_cache
        ---------------------
        
        Turns previously obtained values (`Cache.get_cache`) into more versatile formats (other than `bytes`).

        :param bytearray cached_bytes: data to parse (obtained values)
        :param int data_type: the data type (see `DataTypes` enum -> GARBAGE/6+ reverts back to `bytes`)
        :raises TypeError: an invalid type was processed (such as VOID)
        :return bytes | bool | int | str | char | float | Any: the parsed data
        """
        
        if data_type >= 6:
            return bytes(cached_bytes.copy())

        match data_type:
            case DataType.INTEGER | DataType.BOOLEAN:
                parsed_integer = int.from_bytes(cached_bytes, byteorder='big', signed=True)

                if data_type == DataType.BOOLEAN:
                    return parsed_integer != 0

                return parsed_integer

            case DataType.CHAR | DataType.STRING:
                parsed_char = char(cached_bytes)

                if data_type == DataType.STRING:
                    return parsed_char.ToEncodedString()

                return parsed_char

            case DataType.FLOAT:
                return struct.unpack('>f', cached_bytes)[0]

            case _:
                raise TypeError('type is not valid')

    def set_cache(self, data: bytes | bool | int | str | float, allow_overwrite: bool = True) -> Literal[0]:
        """
        Cache.set_cache
        ----------------

        Caches a value, which can be of types `int`, `bool`, `float`, `str`, `char` (via string) or `bytes`

        :param bytes | bool | int | str | float data: the data to cache
        :param bool allow_overwrite: allows for data to be overwritten by pointer iterations, defaults to True
        :raises CacheOverflow: the storage for the cache has been exhausted
        :return Literal[0]: success code
        """
        
        if not data:
            return 0 # [i] no more data

        if self._pointer >= self._RESERVED:
            if allow_overwrite:
                self._pointer = 0 # [i] loop back to 0 and start overwriting previous shit
                                    # [<] cuz I don't give a fuck tbh

            else:
                if 0x0 in self.cache:
                    first_empty_slot = self.cache.index(0x0)
                    self._pointer = first_empty_slot
                    
                else:
                    raise CacheOverflow('cache storage has been exhausted')

        else:
            self._pointer += 1

        if isinstance(data, bool):
            # [*] Instantly set the cache for that, as it's either a 0 or a 1
            self.cache[self._pointer] = data.to_bytes(1, 'big')
            return 0 # [i] no more data

        if isinstance(data, int):
            # [?] Is it a large int??
            if data > 255:
                # [*] Split the beast into multiple bytes
                int_bytes: bytes = data.to_bytes((data.bit_length() + 7) // 8, byteorder='big')
                self.cache[self._pointer] = int_bytes[0]
                return self.set_cache(int_bytes[1:], allow_overwrite) # [i] more data to go buddy

            self.cache[self._pointer] = data.to_bytes(1, 'big') # [i] will always "fit" into 1 byte exactly
            return 0 # [i] no more data
        
        if isinstance(data, str):
            # [?] Is it a string or a char??
            if len(data) == 1:
                # [*] Character
                CHAR = True
                first_char = data
            
            else:
                # [*] String
                CHAR = False
                first_char = data[0]
            
            self.cache[self._pointer] = char.FromString(first_char).AsBytes()
            
            if CHAR:
                return 0 # [i] no more data
            
            return self.set_cache(data[1:], allow_overwrite)
        
        if isinstance(data, float):
            # [?] Does it represent an integer??
                # [<] If yes, we're gonna do a bit of black magic.
                # [i] Basically, we're gonna treat it as an integer so we're gonna
                # [i] call the function again but with an integer instead of the float
                # [i] The only issue is that the pointer will increment TWICE
                # [*] Solution: decrement the pointer
            if int(data) == data:
                if self._pointer <= 0:
                    self._pointer: int = self._RESERVED - 1
                
                else:
                    self._pointer -= 1
                    
                return self.set_cache(int(data), allow_overwrite)
            
            float_bytes: bytes = struct.pack('>f', data)
            self.cache[self._pointer] = float_bytes[0]
            return self.set_cache(float_bytes[1:], allow_overwrite)
        
        # [*] If nothing worked ut, it's bytes
        if len(data) > 1:
            self.cache[self._pointer] = data[0]
            return self.set_cache(data[1:], allow_overwrite)
        
        self.cache[self._pointer] = data[0]
        return 0 # [i] no more data

# TODO
