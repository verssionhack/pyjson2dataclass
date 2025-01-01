from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ListDictItem:
    name1: str
    age1_opt: Optional[int]

    def __init__(self, data):
        if data is None:
            return None
        self.name1 = str(data.get("name1"))
        self.age1_opt = (int(data.get("age1_opt"))) if data.get("age1_opt") is not None else None


@dataclass
class Example:
    number: int
    string: str
    bool: bool
    as: int
    list_raw: List[int]
    list_list_number: List[List[int]]
    list_dict: List[ListDictItem]
    list_opt_list_opt_number: List[Optional[List[Optional[int]]]]

    def __init__(self, data):
        if data is None:
            return None
        self.number = int(data.get("number_"))
        self.string = str(data.get("string_"))
        self.bool = bool(data.get("bool_"))
        self.as = int(data.get("as"))
        self.list_raw = [(int(i0)) for i0 in data.get("list_raw_")]
        self.list_list_number = [([(int(i1)) for i1 in i0]) for i0 in data.get("list_list_number_")]
        self.list_dict = [(ListDictItem(i0)) for i0 in data.get("list_dict_")]
        self.list_opt_list_opt_number = [(([((int(i2)) if i2 is not None else None) for i2 in i0]) if i0 is not None else None) for i0 in data.get("list_opt_list_opt_number")]