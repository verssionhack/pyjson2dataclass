from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PascalName4Item:
    pascal_name5: dict

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name5 = dict(data["pascalName5"])


@dataclass
class PascalName3Item:
    pascal_name4: List[PascalName4Item]

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name4 = [PascalName4Item(i0) for i0 in data["pascalName4"]]


@dataclass
class Example1:
    pascal_name1: Dict[str, List[int]]
    pascal_name3: List[PascalName3Item]

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name1 = dict([(k0, [int(i1) for i1 in v0]) for k0, v0 in data["pascalName1"].items()])
        self.pascal_name3 = [PascalName3Item(i0) for i0 in data["pascalName3"]]


