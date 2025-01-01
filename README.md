# Parse json to python dataclass

## Installion

```sh
pip3 install pyjson2dataclass
```

## Usage

### json2dataclass

```txt
usage: json2dataclass [-h] [-d SAVE_DIR] [-i [INPUT ...]] [-p] [-f]

options:
  -h, --help            show this help message and exit
  -d SAVE_DIR, --save-dir SAVE_DIR
                        specify the directory parsed dataclass file save to
  -i [INPUT ...], --input [INPUT ...]
                        specify the input json file path
  -p, --pascal          use pascalName for parsed dataclass filename
  -f, --force           enable overwrite exists dataclass

```

```sh
json2dataclass -i <json file1> <json file2> ... -d dataclass
```
What above did is parse json file passed by `-i` to dataclass python file and save them to directory 'dataclass'

### json2dataclass_test

```txt
usage: json2dataclass_test [-h] [-d DATACLASS_DIR] [-j JSON_DIR]

options:
  -h, --help            show this help message and exit
  -d DATACLASS_DIR, --dataclass-dir DATACLASS_DIR
                        specify parsed dataclass directory to be test
  -j JSON_DIR, --json-dir JSON_DIR
                        specify json directory to be test
```

```sh
json2dataclass_test -j json -d dataclass
```

We can use 'json2dataclass_test' to check dataclass python quickly



## Examples

```python
from pyjson2dataclass import json2dataclass
import json


filepath = 'json/example1.json'

parse_text = json2dataclass('Example1', json.load(open(filepath)))
open('example.py', 'w').write(parse_text)
```

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
                    "pascalName5": {}
                }
            ]
        }
    ]
}
```
### [example1.py]
```python
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
```

## Use example.py
### Run
```python
import sys
sys.path.append('./dataclass')

from example1 import Example1
import json

filepath = 'json/example1.json'

example = Example1(json.load(open(filepath)))
print(example)
print(example.pascal_name1)
print(example.pascal_name3)
```
### Output
```txt
Example1(pascal_name1=PascalName1(pascal_name2=[1, 2]), pascal_name3=[PascalName3Item(pascal_name4=[PascalName4Item(pascal_name5={})])])
PascalName1(pascal_name2=[1, 2])
[PascalName3Item(pascal_name4=[PascalName4Item(pascal_name5={})])]
```

## Back to HomePage [https://github.com/verssionhack/pyjson2dataclass]
