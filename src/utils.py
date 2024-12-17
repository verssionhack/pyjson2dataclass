import json
import re
from typing import DefaultDict, List, Optional, Union
from typing_extensions import Tuple


RAW_TYPES = ['int', 'float', 'bool', 'str', 'list', 'dict']
RESERVED_NAMES = ['async', 'def', 'if', 'raise', 'del', 'import', 'return', 'elif', 'in', 'try', 'and', 'else', 'is', 'while', 'as', 'except', 'lambda', 'with', 'assert', 'finally', 'nonlocal', 'yield', 'break', 'for', 'not', 'class', 'form', 'or', 'continue', 'global', 'pass']
ESCAPE_CHAR = {
        '_': '-/|:;.\\',
        '': '!@#$%^&*()[]\'"<>,~`{}?+=',
        }


def print_json(v):
    print(json.dumps(v, ensure_ascii=False, indent=4))


def v_dup(v):
    return json.loads(json.dumps(v))


def repair_name(name):
    if name in RESERVED_NAMES:
        name += '_'
    for k, v in ESCAPE_CHAR.items():
        for vv in v:
            while vv in name:
                name = name.replace(vv, k)
    return name.replace('-', '_')


def pascal2snake(value: str) -> str:
    if value.isupper():
        return value.lower()
    ret = ''
    for c in value:
        if 'A' <= c <= 'Z':
            if len(ret) > 0:
                ret += '_'
            ret += c.lower()
        else:
            ret += c
    return ret


def snake2pascal(value: str) -> str:
    ret = ''
    upper = False
    for c in value:
        if c == '_':
            upper = True
        else:
            if upper:
                upper = False
                ret += c.upper()
            else:
                ret += c
    return ret


def key2snake(value: list | dict):
    if isinstance(value, list):
        for i in range(len(value)):
            key2snake(value[i])
    elif isinstance(value, dict):
        keys = list(value.keys())
        for key in keys:
            key2snake(value[key])
            value[pascal2snake(key)] = value.pop(key)


def key2pascal(value: list | dict):
    if isinstance(value, list):
        for i in range(len(value)):
            key2pascal(value[i])
    elif isinstance(value, dict):
        keys = list(value.keys())
        for key in keys:
            key2pascal(value[key])
            value[snake2pascal(key)] = value.pop(key)


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


def _parsed_struct2str(value: dict | str):
    return json.dumps(value, ensure_ascii=False)


def _compare_struct_and_concat(a: dict, b: dict, checkd_name: list = []):
    a = v_dup(a)
    b = v_dup(b)
    if _parsed_struct2str(a) == _parsed_struct2str(b):
        return a
    keys = set(a['struct']) | set(b['struct'])
    for key in keys:
        if key in checkd_name:
            continue
        if key in a['struct'] and key not in b['struct']:
            _l, childrenk, _ = unpack_raw_field(a['struct'][key])
            if _l and _l[0] == 'Optional':
                continue
            if childrenk in a['children']:
                a['children'][childrenk]['layers'].append('Optional')
            else:
                a['struct'][key] = _pack_field(a['struct'][key], layers=['Optional'])
            checkd_name.append(key)
        elif key not in a['struct'] and key in b['struct']:
            _l, childrenk, _ = unpack_raw_field(b['struct'][key])
            if childrenk in b['children']:
                a['children'][childrenk] = v_dup(b['children'][childrenk])
            if _l and _l[0] == 'Optional':
                a['struct'][key] = b['struct'][key]
            else:
                if childrenk in b['children']:
                    a['children'][childrenk] = v_dup(b['children'][childrenk])
                    a['children'][childrenk]['layers'].append('Optional')
                else:
                    a['struct'][key] = _pack_field(b['struct'][key], layers=['Optional'])
            a['raw_name'][key] = b['raw_name'][key]
            checkd_name.append(key)
        elif a['struct'][key] != b['struct'][key]:
            raise Exception(f'a[struct][{key}] != b[struct][{key}]\na[struct][{key}]={_parsed_struct2str(a["struct"][key])}\nb[struct][{key}]={_parsed_struct2str(b["struct"][key])}')
        else:
            _, childrenk, _ = unpack_raw_field(a['struct'][key])
            if childrenk not in RAW_TYPES:
                a['children'][childrenk] = _compare_struct_and_concat(a['children'][childrenk], b['children'][childrenk], checkd_name=[])
                '''
                achild_str = _parsed_struct2str(a['children'][childrenk])
                bchild_str = _parsed_struct2str(b['children'][childrenk])
                if achild_str != bchild_str:
                    raise Exception(f'a[children][{childrenk}] != b[children][{childrenk}]\na[children][{childrenk}]={achild_str}\nb[children][{childrenk}]={bchild_str}')
                '''
    return a

def _do_concat_same_struct(values: list[str | dict], layers: list[str] = []):
    values = v_dup(values)
    base_struct = None
    all_eq = True
    parsed_str_list = [_parsed_struct2str(i) for i in values]
    checkd_name = []
    i = 0
    if len(values) == 0:
        return 'list'
    else:
        if 'Any' in values:
            layers.append('Optional')
        for sv in values:
            if sv == 'Any':
                continue
            elif not base_struct:
                base_struct = sv
            elif (base_struct in RAW_TYPES) ^ (sv in RAW_TYPES):
                raise Exception(f'base_struct != sv\nbase_struct={base_struct}\nsv={sv}')
            elif base_struct in RAW_TYPES and base_struct != sv:
                raise Exception(f'base_struct != sv\nbase_struct={base_struct}\nsv={sv}')
        if isinstance(base_struct, list):
            layers.append('List')
            base_struct = _do_concat_same_struct(base_struct, layers=layers)
        elif isinstance(base_struct, dict):
            base_struct['layers'] = v_dup(layers)
        elif isinstance(base_struct, str):
            base_struct = _pack_field(base_struct, layers=layers)

        if isinstance(base_struct, dict):
            for sv in values:
                if sv == 'Any':
                    continue
                if isinstance(sv, list):
                    sv = _do_concat_same_struct(sv, layers=layers)
                base_struct = _compare_struct_and_concat(base_struct, sv, checkd_name)
    return base_struct


def _pack_field(k: str, layers: List[str], **_):
    if layers and layers[0] == 'List' and k not in RAW_TYPES:
        k += 'Item'
    for layer in reversed(layers):
        k = f'{layer}[{k}]'
    return k

def _parse_tree(value):


    if isinstance(value, list):
        ret = []
        for i in range(len(value)):
            ret.append(_parse_tree(value[i]))
            if isinstance(ret[i], dict):
                ret[i]['layers'].append('List')
        return ret
    elif isinstance(value, dict):
        ret = {
                'struct': {},
                'raw_name': {},
                'children': {},
                'layers': [],
                }

        for k in value:
            ret['raw_name'][pascal2snake(k)] = k
            childrenk = snake2pascal(repair_name(k))
            if childrenk:
                childrenk = childrenk[0].upper() + childrenk[1:]
            if isinstance(value[k], dict):
                parsed_dict = _parse_tree(value[k])

                if len(parsed_dict['struct']) == 0:
                    ret['struct'][pascal2snake(k)] = 'dict'
                #elif len(parsed_dict['struct']) == 1:
                #    ret['struct'][pascal2snake(k)] = f'Dict[str, {list(parsed_dict["struct"].values())[0]}]'
                else:
                    for sk, sv in parsed_dict['struct'].items():
                        if not isinstance(sv, str):
                            continue
                        _l, _r, _n = unpack_raw_field(sv)
                        if _r not in parsed_dict['children']:
                            continue
                        parsed_dict['children'][_r] = _do_concat_same_struct(parsed_dict['children'][_r])
                        if isinstance(parsed_dict['children'][_r], str):
                            parsed_dict['struct'][sk] = replace_raw_field(sv, parsed_dict['children'].pop(_r))
                    ret['struct'][pascal2snake(k)] = childrenk
                    ret['children'][childrenk] = parsed_dict

            elif isinstance(value[k], list):
                parsed_list = _parse_tree(value[k])
                concated_struct = _do_concat_same_struct(parsed_list, ['List'])

                if isinstance(concated_struct, str):
                    ret['struct'][pascal2snake(k)] = concated_struct
                elif isinstance(concated_struct, dict):
                    childrenk = _pack_field(childrenk, **concated_struct)
                    ret['struct'][pascal2snake(k)] = f'{childrenk}'
                    _, childrenk, _ = unpack_raw_field(childrenk)
                    ret['children'][childrenk] = concated_struct

            else:
                ret['struct'][pascal2snake(k)] = _parse_tree(value[k])

        return ret
    else:
        return value.__class__.__name__ if value.__class__.__name__ != 'NoneType' else 'Any'


def parse(name: str, data: dict | list):
    data = v_dup(data)
    if isinstance(data, dict):
        parsed_dict = _parse_tree(data)
    else:
        parsed_dict = _do_concat_same_struct(_parse_tree(data))
        if isinstance(parsed_dict, str):
            return _pack_field(parsed_dict, ['Lism'])
    predefs, body_text = _parse(repair_name(name), parsed_dict)

    predefs.reverse()

    predefs.append(body_text)

    body_text = ''

    i = 0

    while i != len(predefs) - 1:
        j = len(predefs) - 1
        while i < j:
            if predefs[i] == predefs[j]:
                del predefs[j]
            j -= 1
        i += 1

    for i in predefs:
        body_text += i

    header = 'from typing import Dict, List, Any, Optional\n'
    header += 'from dataclasses import dataclass\n\n\n'

    return header + body_text


def replace_raw_field(field: str, new_raw_field: str, deep: int = -1):
    (prefixs, field, _) = unpack_raw_field(field, deep)
    prefixs.reverse()
    for prefix in prefixs:
        new_raw_field = f'{prefix}[{new_raw_field}]'
    return new_raw_field


def unpack_raw_field(field: str, deep: int = -1) -> Tuple[List[str], str, Optional[str]]:
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


def unpack_field_parse(field: str, raw_name: str):
    upper_layers = []

    def V(v: str, N: str, D: int = 0):
        def optional_name_trans(s: str):
            if (i := s.find('.get(')) != -1:
                j = s.rfind(')')
                s = s[:i] + f'[{N[i + 5:j]}]' + s[j + 1:]
            return s

        layers, v, _n = unpack_raw_field(v, 1)
        upper_layers.extend(layers)
        if len(layers) == 0:
            if v:
                return f'{v}({N})'
            else:
                return N
        match layers[-1]:
            case 'Optional':
                return f'({V(v, optional_name_trans(N), D + 1)}) if {N} else None'
            case 'Dict':
                return f'dict([(k{D}, {V(v, "v" + str(D), D + 1)}) for k{D}, v{D} in {N}.items()])'
            case 'List':
                return f'[({V(v, "i" + str(D), D + 1)}) for i{D} in {N}]'

    return V(field, raw_name)


def _parse(name: str, data: dict):
    predefs = []
    body_text = f'@dataclass\nclass {snake2pascal(name)}:\n'

    for k, v in data['children'].items():
        (_predefs, _body_text) = _parse(k, v)
        predefs.extend(_predefs)
        predefs.insert(0, _body_text)

    for k, v in data['struct'].items():
        rk = repair_name(k)
        body_text += f'    {rk}: {v}\n'

    body_text += \
f'''
    def __init__(self, data: dict | None):
        if not data:
            return None
'''

    for k, v in data['struct'].items():
        raw_name = data['raw_name'][pascal2snake(k)]
        rk = repair_name(k)
        _l, _v, _n = unpack_raw_field(v, 1)
        if len(_l) > 0 and _l[0] == 'Optional':
            body_text += '        self.{} = {}\n'.format(rk, unpack_field_parse(v, f'data.get("{raw_name}")'))
        else:
            body_text += '        self.{} = {}\n'.format(rk, unpack_field_parse(v, f'data["{raw_name}"]'))

    body_text += '\n\n'

    return (predefs, body_text)
