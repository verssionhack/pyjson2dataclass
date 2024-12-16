# Parse json to python dataclass
## Usage
```sh
./__main__.py <json file1> <json file2> ...
```
```sh
python -m pyjson2dataclass <json file1> <json file2> ...
```

```python
from pyjson2dataclass import parse
import json


filepath = 'json/example1.json'

parse_text = parse('Example', json.load(open(filepath)))
open('example.py', 'w').write(parse_text)
```

## Examples

### [json/example1.json]
```json
{
    "pascalName1": {
        "pascalName2": [
            1,
            2
        ]
    },
    "pascalName3": [
        {
            "pascalName4": [
                {
                    "pascalName5": {
                        "data": 1
                    }
                }
            ]
        }
    ]
}
```
### [example.py]
```python
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



```

## Use example.py
### Run
```python
from example import Example
import json

filepath = 'json/example1.json'

example = Example(json.load(open(filepath)))
print(example)
print(example.pascal_name1)
print(example.pascal_name3)
```
### Output
```txt
Example(pascal_name1=PascalName1(pascal_name2=[1, 2]), pascal_name3=[PascalName3Item(pascal_name4=[PascalName4Item(pascal_name5=PascalName5(data=1))])])
PascalName1(pascal_name2=[1, 2])
[PascalName3Item(pascal_name4=[PascalName4Item(pascal_name5=PascalName5(data=1))])]
```

## Back to HomePage [https://github.com/verssionhack/pyjson2dataclass]
