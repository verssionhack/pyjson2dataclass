from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PascalName5:
    data: int

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.data = data["data"]


@dataclass
class PascalName4Item:
    pascal_name5: PascalName5

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name5 = PascalName5(data["pascalName5"])


@dataclass
class PascalName1:
    pascal_name2: List[int]

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name2 = []
        if data.get("pascalName2"):
            for i in data["pascalName2"]:
                self.pascal_name2.append(i)


@dataclass
class PascalName3Item:
    pascal_name4: List[PascalName4Item]

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name4 = []
        if data.get("pascalName4"):
            for i in data["pascalName4"]:
                self.pascal_name4.append(PascalName4Item(i))


@dataclass
class Example:
    pascal_name1: PascalName1
    pascal_name3: List[PascalName3Item]

    def __init__(self, data: dict | None):
        if not data:
            return None
        self.pascal_name1 = PascalName1(data["pascalName1"])
        self.pascal_name3 = []
        if data.get("pascalName3"):
            for i in data["pascalName3"]:
                self.pascal_name3.append(PascalName3Item(i))


