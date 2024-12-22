import json
import re
from typing import Callable, List, Optional, Tuple, Dict, Self
from dataclasses import dataclass
from pprint import pprint

RAW_TYPES = ['int', 'float', 'bool', 'str', 'list', 'dict']
LAYERS_TYPES = ['Optional', 'Dict', 'List']
RESERVED_NAMES = ['async', 'def', 'if', 'raise', 'del', 'import', 'return', 'elif', 'in', 'try', 'and', 'else', 'is', 'while', 'as', 'except', 'lambda', 'with', 'assert', 'finally', 'nonlocal', 'yield', 'break', 'for', 'not', 'class', 'form', 'or', 'continue', 'global', 'pass']
ESCAPE_CHAR = {
        '_': '-/|:;.\\',
        '': '!@#$%^&*()[]\'"<>,~`{}?+=',
        }

DATACLASS_FILE_HEADER = 'from typing import Dict, List, Any, Optional\nfrom dataclasses import dataclass\n\n\n'


def print_json(v):
    print(json.dumps(v, ensure_ascii=False, indent=4))


def json_dup(v):
    return json.loads(json.dumps(v))


def repair_name(name):
    if name in RESERVED_NAMES:
        name += '_'
    for k, v in ESCAPE_CHAR.items():
        for vv in v:
            while vv in name:
                name = name.replace(vv, k)
    return name


def trans_key(value: list | dict, f: Callable[[str], str]):
    if isinstance(value, list):
        for i in range(len(value)):
            trans_key(value[i], f)
    elif isinstance(value, dict):
        keys = list(value.keys())
        for key in keys:
            trans_key(value[key], f)
            value[f(key)] = value.pop(key)


def struct_tree(value):
    if isinstance(value, list):
        ret = []
        for i in value:
            ret.append(struct_tree(i))
        return ret
    elif isinstance(value, dict):
        ret = {}
        for k in value:
            ret[k] = struct_tree(value[k])
        return ret
    else:
        return value.__class__.__name__ if value.__class__.__name__ != 'NoneType' else 'Any'


def pack_field(field: str, layers: List[str]):
    _layers, field, _ = unpack_field(field)
    layers.extend(_layers)
    for layer in reversed(layers):
        if layer == 'Dict':
            field = f'{layer}[str, {field}]'
        else:
            field = f'{layer}[{field}]'
    return field


def unpack_field(field: str, deep: int = -1) -> Tuple[List[str], str, Optional[str]]:
    prefixs = [
            'Optional[',
            'List[',
            'Dict[str, ',
            ]
    unpack_layers = []
    while deep == -1 or deep > 0:
        hit = False
        for prefix in prefixs:
            if field.startswith(prefix):
                unpack_layers.append(prefix[:prefix.find('[')])
                field = field[len(prefix):-1]
                hit = True
                if deep > 0:
                    deep -= 1
                if deep == 0:
                    break
        if not hit:
            break
    _n = [i[:i.find('[')] for i in prefixs if field.startswith(i)]
    return (unpack_layers, field, _n[0] if _n else None)
