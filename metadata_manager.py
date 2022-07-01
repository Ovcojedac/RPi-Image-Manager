import json
from pathlib import Path
from xmlrpc.client import Boolean
from typing import Callable, List

class MetadataManager:
    
    def __init__(self, filepath: Path, newfile: Boolean = False):
        self.__filepath = filepath
        self.__data = {}
        if not newfile:
            self.__load()
        
    def __load(self) -> None:
        with open(self.__filepath, 'r') as f:
            self.__data = json.load(f)
            
    def __write(self, filepath: Path = None) -> None:
        if filepath == None:
            filepath = self.__filepath
        with open(filepath, 'w') as f:
            json.dump(self.__data, f, indent=4)

    def __do_if_field_exists(self, path_to_field: List[str], do: Callable) -> Boolean:
        
        if len(path_to_field) == 0:
            print("Empty list of fields to check!")
            return True
        fields_processed = []
        result = True
        data = self.__data
        while result and len(path_to_field) > 0:
            field_name = path_to_field.pop(0)
            result = field_name in data
            if result:
                data = data[field_name]
                fields_processed.append(field_name)
        
        if result:
            if do:
                do(data)
        
        return result
    
    def get_field(self, path_to_field: List[str]) -> str:
        result = []
        def get_field_value(json_data):
            result.append(json_data)
        
        if self.__do_if_field_exists(path_to_field, get_field_value):
            return result[0]
        return ''
    
    def add_field(self, path_to_field: List[str], field_name: str, field_value: str, overwrite_if_exists: Boolean = False) -> Boolean:
        
        def create_and_add_data(json_base):
            if (not field_name in json_base) or overwrite_if_exists:
                json_base[field_name] = field_value
        
        if len(path_to_field) == 0:
            create_and_add_data(self.__data)
            return True
        
        return self.__do_if_field_exists(path_to_field, create_and_add_data)
    
    def update_field(self, path_to_field: List[str], field_name: str, field_value: str, add_if_missing: Boolean = False) -> Boolean:
        
        def update(json_base):
            if field_name in json_base or add_if_missing:
                json_base[field_name] = field_value
        
        if len(path_to_field) == 0:
            update(self.__data)
            return True
        
        return self.__do_if_field_exists(path_to_field, update)
        
    def remove_field(self, path_to_field: List[str]) -> Boolean:
        
        if len(path_to_field) == 1:
            self.__data.pop(path_to_field[0])
            return True
        
        field_name = path_to_field.pop()
        
        def remove_field(json_base):
            json_base.pop(field_name)
        
        return self.__do_if_field_exists(path_to_field, remove_field)
    
    def check_if_field_exists(self, path_to_field: List[str]) -> Boolean:
        return self.__do_if_field_exists(path_to_field, None)
    
    
    def store(self):
        self.__write()