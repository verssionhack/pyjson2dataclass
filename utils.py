import json
from typing import Required


RAW_TYPES = ['int', 'float', 'bool', 'str', 'list']


def print_json(v): 
    print(json.dumps(v, ensure_ascii=False, indent=4))


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


def _parse_tree(value):

    def _parsed_struct2str(value: dict):
        return json.dumps(value, ensure_ascii=False)

    if isinstance(value, list):
        ret = []
        for i in range(len(value)):
            ret.append(_parse_tree(value[i]))
        return ret
    elif isinstance(value, dict):
        ret = {
                'struct': {},
                'raw_name': {},
                'children': {},
                'is_list': False,
                }

        for k in value:
            ret['raw_name'][pascal2snake(k)] = k
            childrenk = snake2pascal(k)
            childrenk = childrenk[0].upper() + childrenk[1:]
            if isinstance(value[k], dict):
                parsed_dict = _parse_tree(value[k])

                all_eq = len(parsed_dict['struct']) > 1
                is_optional = False
                base_struct = None
                for sk, sv in parsed_dict['struct'].items():
                    if sv == 'Any':
                        parsed_dict['is_optional'] = True
                        is_optional = True
                        continue
                    elif sv in RAW_TYPES or sv.startswith('List') or sv.startswith('Dict'):
                        all_eq = False
                        break
                    elif not base_struct:
                        base_struct = parsed_dict['children'][sv]
                    else:
                        more_keys_struct = base_struct
                        less_keys_struct = parsed_dict['children'][sv]
                        if _parsed_struct2str(base_struct) != _parsed_struct2str(parsed_dict['children'][sv]):
                            if len(more_keys_struct['struct']) < len(less_keys_struct['struct']):
                                more_keys_struct, less_keys_struct = less_keys_struct, more_keys_struct
                            for lk in less_keys_struct['struct']:
                                if lk not in more_keys_struct['struct']:
                                    all_eq = False
                                    break
                            for mk in more_keys_struct['struct']:
                                if mk not in less_keys_struct['struct']:
                                    more_keys_struct['struct'][mk] = f'Optional[{more_keys_struct["struct"][mk]}]'
                            base_struct = more_keys_struct

                if all_eq and base_struct:
                    ret['children'][childrenk] = base_struct
                    if is_optional:
                        ret['struct'][pascal2snake(k)] = f'Dict[str, Optional[{childrenk}]]'
                    else:
                        ret['struct'][pascal2snake(k)] = f'Dict[str, {childrenk}]'
                else:
                    ret['children'][childrenk] = parsed_dict
                    ret['struct'][pascal2snake(k)] = childrenk


            elif isinstance(value[k], list):
                parsed_list = _parse_tree(value[k])
                parsed_str_list = [_parsed_struct2str(i) for i in parsed_list]
                if len(parsed_list) == 0:
                    ret['struct'][pascal2snake(k)] = 'list'
                else:
                    for i in range(1, len(parsed_str_list)):
                        if parsed_str_list[0] != parsed_str_list[i]:
                            raise Exception(f'parse list item[0]={parsed_str_list[0]} != item[{i}]={parsed_str_list[i]}')
                    if parsed_list[0] in RAW_TYPES:
                        ret['struct'][pascal2snake(k)] = f'List[{parsed_list[0]}]'
                    else:
                        ret['children'][childrenk] = parsed_list[0]
                        ret['struct'][pascal2snake(k)] = f'List[{childrenk}]'
                        if 'is_list' in ret['children'][childrenk]:
                            ret['children'][childrenk]['is_list'] = True
            else:
                ret['struct'][pascal2snake(k)] = _parse_tree(value[k])

        return ret
    else:
        return value.__class__.__name__ if value.__class__.__name__ != 'NoneType' else 'Any'

def parse(name: str, data: dict):
    data = json.loads(json.dumps(data))
    parsed_dict = _parse_tree(data)
    predefs, body_text = _parse(name, parsed_dict)

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


def _parse(name: str, data: dict):
    predefs = []
    if data['is_list']:
        body_text = f'@dataclass\nclass {snake2pascal(name)}Item:\n'
    else:
        body_text = f'@dataclass\nclass {snake2pascal(name)}:\n'

    for k, v in data['children'].items():
        (_predefs, _body_text) = _parse(k, v)
        predefs.extend(_predefs)
        predefs.insert(0, _body_text)

    for k, v in data['struct'].items():
        if v.startswith('List[') or v == 'list':
            if v.startswith('List[') and v[5:-1] not in RAW_TYPES:
                type_name = f'List[{v[5:-1]}Item]'
                body_text += f'    {k}: {type_name}\n'
            else:
                body_text += f'    {k}: {v}\n'
        elif v.startswith('Dict[') or v == 'dict':
            body_text += f'    {k}: {v}\n'
        else:
            body_text += f'    {k}: {v}\n'

    body_text += \
f'''
    def __init__(self, data: dict | None):
        if not data:
            return None
'''

    for k, v in data['struct'].items():
        raw_name = data['raw_name'][pascal2snake(k)]
        if v.startswith('List['):
            type_name = v[5:-1]
            body_text += f'        self.{k} = []\n'
            if type_name in RAW_TYPES:
                body_text += f'        if data.get("{raw_name}"):\n'
                body_text += f'            for i in data["{raw_name}"]:\n'
                body_text += f'                self.{k}.append(i)\n'
            else:
                body_text += f'        if data.get("{raw_name}"):\n'
                body_text += f'            for i in data["{raw_name}"]:\n'
                type_name += 'Item'
                body_text += f'                self.{k}.append({type_name}(i))\n'
        elif v.startswith('Dict['):
            type_name = v[10:-1]
            body_text += f'        self.{k} = {{}}\n'
            body_text += f'        if data.get("{raw_name}"):\n'
            body_text += f'            for k, v in data["{raw_name}"].items():\n'
            if type_name.startswith('Optional['):
                type_name = type_name[9:-1]
                if type_name in RAW_TYPES:
                    body_text += f'                self.{k}[k] = v\n'
                else:
                    body_text += f'                self.{k}[k] = {type_name}(v) if v else None\n'
            else:
                body_text += f'                self.{k}[k] = {type_name}(v)\n'
        else:
            if v == 'Any':
                body_text += f'        self.{k} = data.get("{raw_name}")\n'
            elif v in RAW_TYPES:
                body_text += f'        self.{k} = data["{raw_name}"]\n'
            elif v.startswith('Optional['):
                type_name = v[9:-1]
                if type_name in RAW_TYPES:
                    body_text += f'        self.{k} = data.get("{raw_name}")\n'
                else:
                    body_text += f'        self.{k} = {type_name}(data.get("{raw_name}")) if data.get("{raw_name}") else None\n'
            else:
                body_text += f'        self.{k} = {v}(data["{raw_name}"])\n'

    body_text += '\n\n'

    return (predefs, body_text)
