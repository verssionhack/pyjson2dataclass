RAW_TYPES = ['int', 'float', 'bool', 'str', 'list', 'dict', 'Any']
LAYERS_TYPES = ['Optional', 'Dict', 'List']
RESERVED_NAMES = ['async', 'def', 'if', 'raise', 'del', 'import', 'return', 'elif', 'in', 'try', 'and', 'else', 'is', 'while', 'as', 'except', 'lambda', 'with', 'assert', 'finally', 'nonlocal', 'yield', 'break', 'for', 'not', 'class', 'from', 'or', 'continue', 'global', 'pass'] + RAW_TYPES
ESCAPE_CHAR = {
        '_': '-/|:;.\\',
        '': '!@#$%^&*()[]\'"<>,~`{}?+=',
        }

DATACLASS_FILE_HEADER = 'from typing import Dict, List, Any, Optional\nfrom dataclasses import dataclass\n\n\n'


def repair_name(name):
    if name in RESERVED_NAMES:
        name += '_'
    for k, v in ESCAPE_CHAR.items():
        for vv in v:
            while vv in name:
                name = name.replace(vv, k)
    return name
