from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PascalName1:
    pascal_name2: List[int]

    def __init__(self, data):
        if data is None:
            return None
        self.pascal_name2 = [(int(i0)) for i0 in data.get("pascalName2")]


@dataclass
class PascalName4Item:
    pascal_name5: dict

    def __init__(self, data):
        if data is None:
            return None
        self.pascal_name5 = dict(data.get("pascalName5"))


@dataclass
class PascalName3Item:
    pascal_name4: List[PascalName4Item]

    def __init__(self, data):
        if data is None:
            return None
        self.pascal_name4 = [(PascalName4Item(i0)) for i0 in data.get("pascalName4")]


@dataclass
class Example1:
    pascal_name1: PascalName1
    pascal_name3: List[PascalName3Item]

    def __init__(self, data):
        if data is None:
            return None
        self.pascal_name1 = PascalName1(data.get("pascalName1"))
        self.pascal_name3 = [(PascalName3Item(i0)) for i0 in data.get("pascalName3")]