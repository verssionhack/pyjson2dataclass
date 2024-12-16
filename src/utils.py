import json
from typing import DefaultDict


RAW_TYPES = ['int', 'float', 'bool', 'str', 'list', 'dict']
RESERVED_NAMES = ['async', 'def', 'if', 'raise', 'del', 'import', 'return', 'elif', 'in', 'try', 'and', 'else', 'is', 'while', 'as', 'except', 'lambda', 'with', 'assert', 'finally', 'nonlocal', 'yield', 'break', 'for', 'not', 'class', 'form', 'or', 'continue', 'global', 'pass']
ESCAPE_CHAR = {
        '_': '-/|:;.\\',
        '': '!@#$%^&*()[]\'"<>,~`{}?+=',
        }


def print_json(v):
    print(json.dumps(v, ensure_ascii=False, indent=4))


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
            childrenk = snake2pascal(repair_name(k))
            if childrenk:
                childrenk = childrenk[0].upper() + childrenk[1:]
            if isinstance(value[k], dict):
                parsed_dict = _parse_tree(value[k])

                if len(parsed_dict['struct']) == 0:
                    ret['struct'][pascal2snake(k)] = 'dict'
                elif len(parsed_dict['struct']) == 1:
                    ret['struct'][pascal2snake(k)] = f'Dict[str, {list(parsed_dict["struct"].values())[0]}]'
                else:
                    all_eq = len(parsed_dict['struct']) > 1
                    is_optional = False
                    base_struct = None
                    checkd_name = []
                    for sk, sv in parsed_dict['struct'].items():
                        if sv.startswith('List') or sv.startswith('Dict'):
                            if sv.startswith('List'):
                                all_eq = False
                                break
                            continue
                        if sv == 'Any':
                            is_optional = True
                            continue
                        elif not base_struct:
                            if sv in RAW_TYPES:
                                base_struct = sv
                            else:
                                base_struct = parsed_dict['children'][sv]
                        elif sv in RAW_TYPES or base_struct in RAW_TYPES: #or sv.startswith('List') or sv.startswith('Dict'):
                            if base_struct != sv:
                                all_eq = False
                                break
                        else:
                            more_keys_struct = base_struct
                            less_keys_struct = parsed_dict['children'][sv]
                            if _parsed_struct2str(base_struct) != _parsed_struct2str(parsed_dict['children'][sv]):
                                '''
                                if not (isinstance(more_keys_struct, dict) and isinstance(less_keys_struct, dict)):
                                    all_eq = False
                                    break
                                '''
                                #if len(more_keys_struct['struct']) < len(less_keys_struct['struct']):
                                #    more_keys_struct, less_keys_struct = less_keys_struct, more_keys_struct
                                for lk in less_keys_struct['struct']:
                                    if lk not in more_keys_struct['struct'] and lk not in checkd_name:
                                        more_keys_struct['struct'][lk] = f'Optional[{less_keys_struct["struct"][lk]}]'
                                        more_keys_struct['raw_name'][lk] = less_keys_struct['raw_name'][lk]
                                        checkd_name.append(lk)
                                    #if lk not in more_keys_struct['struct']:
                                    #    all_eq = False
                                    #    break
                                for mk in more_keys_struct['struct']:
                                    if mk not in less_keys_struct['struct'] and mk not in checkd_name:
                                        more_keys_struct['struct'][mk] = f'Optional[{more_keys_struct["struct"][mk]}]'
                                        checkd_name.append(mk)
                                base_struct = more_keys_struct

                    if all_eq and base_struct:
                        if base_struct in RAW_TYPES:
                            if is_optional:
                                ret['struct'][pascal2snake(k)] = f'Dict[str, Optional[{base_struct}]]'
                            else:
                                ret['struct'][pascal2snake(k)] = f'Dict[str, {base_struct}]'
                        else:
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
                all_eq = True
                is_optional = False
                parsed_str_list = [_parsed_struct2str(i) for i in parsed_list]
                checkd_name = []
                i = 0
                if len(parsed_list) == 0:
                    ret['struct'][pascal2snake(k)] = 'list'
                else:
                    base_struct = None
                    for sv in parsed_list:
                        if sv == 'Any':
                            is_optional = True
                        elif not base_struct:
                            base_struct = sv
                        elif sv in RAW_TYPES:
                            if base_struct != sv:
                                all_eq = False
                                break
                        else:
                            more_keys_struct = base_struct
                            less_keys_struct = sv
                            if _parsed_struct2str(base_struct) != _parsed_struct2str(sv):
                                for lk in less_keys_struct['struct']:
                                    if lk not in more_keys_struct['struct'] and lk not in checkd_name:
                                        more_keys_struct['struct'][lk] = f'Optional[{less_keys_struct["struct"][lk]}]'
                                        more_keys_struct['raw_name'][lk] = less_keys_struct['raw_name'][lk]
                                        checkd_name.append(lk)
                                        #all_eq = False
                                        #break
                                for mk in more_keys_struct['struct']:
                                    if mk not in less_keys_struct['struct'] and mk not in checkd_name:
                                        more_keys_struct['struct'][mk] = f'Optional[{more_keys_struct["struct"][mk]}]'
                                        checkd_name.append(mk)
                                base_struct = more_keys_struct
                        i += 1

                    if all_eq and base_struct:
                        if base_struct in RAW_TYPES:
                            if is_optional:
                                ret['struct'][pascal2snake(k)] = f'List[Optional[{base_struct}]]'
                            else:
                                ret['struct'][pascal2snake(k)] = f'List[{base_struct}]'
                        else:
                            ret['children'][childrenk] = base_struct
                            if is_optional:
                                ret['struct'][pascal2snake(k)] = f'List[Optional[{childrenk}]]'
                            else:
                                ret['struct'][pascal2snake(k)] = f'List[{childrenk}]'
                            if 'is_list' in ret['children'][childrenk]:
                                ret['children'][childrenk]['is_list'] = True
                    else:
                        raise Exception(f'parse list item[0] != item[{i}]\nitem[0]={parsed_str_list[0]}\nitem[{i}]={parsed_str_list[i]}')
                    '''
                    for i in range(1, len(parsed_str_list)):
                        if parsed_str_list[0] != parsed_str_list[i]:
                            raise Exception(f'parse list item[0] != item[{i}]\nitem[0]={parsed_str_list[0]}\nitem[{i}]={parsed_str_list[i]}')
                    if parsed_list[0] in RAW_TYPES:
                        ret['struct'][pascal2snake(k)] = f'List[{parsed_list[0]}]'
                    else:
                        ret['children'][childrenk] = parsed_list[0]
                        ret['struct'][pascal2snake(k)] = f'List[{childrenk}]'
                        if 'is_list' in ret['children'][childrenk]:
                            ret['children'][childrenk]['is_list'] = True
                    '''
            else:
                ret['struct'][pascal2snake(k)] = _parse_tree(value[k])

        return ret
    else:
        return value.__class__.__name__ if value.__class__.__name__ != 'NoneType' else 'Any'


def parse(name: str, data: dict):
    data = json.loads(json.dumps(data))
    parsed_dict = _parse_tree(data)
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


def unpack_raw_field(field: str, deep: int = -1):
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
    return unpack_layers, field


def unpack_field_parse(field: str, raw_name: str):
    def V(v: str, N: str, D: int = 0, Vpad: str = ''):

        def optional_name_trans(s: str):
            if (i := s.find('.get(')) != -1:
                j = s.rfind(')')
                s = s[:i] + f'[{N[i + 5:j]}]' + s[j + 1:]
            return s

        layers, v = unpack_raw_field(v, 1)
        if len(layers) == 0:
            return f'{v}{Vpad}({N})'
        match layers[-1]:
            case 'Optional':
                return f'{V(v, optional_name_trans(N), D + 1)} if {N} else None'
            case 'Dict':
                return f'dict([(k{D}, {V(v, "v" + str(D), D + 1)}) for k{D}, v{D} in {N}.items()])'
            case 'List':
                return f'[{V(v, "i" + str(D), D + 1, "Item" if v not in RAW_TYPES else '')} for i{D} in {N}]'

    return V(field, raw_name)



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
        rk = repair_name(k)
        if v.startswith('List[') or v == 'list':
            if v.startswith('List[') and v[5:-1] not in RAW_TYPES:
                type_name = f'List[{v[5:-1]}Item]'
                body_text += f'    {rk}: {type_name}\n'
            else:
                body_text += f'    {rk}: {v}\n'
        elif v.startswith('Dict[') or v == 'dict':
            body_text += f'    {rk}: {v}\n'
        else:
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
        _l, _v = unpack_raw_field(v, 1)
        if len(_l) > 0 and _l[0] == 'Optional':
            body_text += f'        self.{rk} = {unpack_field_parse(v, "data.get(\"" + raw_name + "\")")}\n'
        else:
            body_text += f'        self.{rk} = {unpack_field_parse(v, "data[\"" + raw_name + "\"]")}\n'
        '''
        if v.startswith('List['):
            type_name = v[5:-1]
            body_text += f'        self.{rk} = []\n'
            if type_name in RAW_TYPES:
                body_text += f'        if data.get("{raw_name}"):\n'
                body_text += f'            for i in data["{raw_name}"]:\n'
                body_text += f'                self.{rk}.append(i)\n'
            else:
                body_text += f'        if data.get("{raw_name}"):\n'
                body_text += f'            for i in data["{raw_name}"]:\n'
                type_name += 'Item'
                body_text += f'                self.{rk}.append({type_name}(i))\n'
        elif v.startswith('Dict['):
            type_name = v[10:-1]
            body_text += f'        self.{rk} = {{}}\n'
            body_text += f'        if data.get("{raw_name}"):\n'
            body_text += f'            for k, v in data["{raw_name}"].items():\n'
            if type_name.startswith('Optional['):
                type_name = type_name[9:-1]
                if type_name in RAW_TYPES:
                    body_text += f'                self.{rk}[k] = v\n'
                else:
                    body_text += f'                self.{rk}[k] = {type_name}(v) if v else None\n'
            else:
                body_text += f'                self.{rk}[k] = {type_name}(v)\n'
        else:
            if v == 'Any':
                body_text += f'        self.{rk} = data.get("{raw_name}")\n'
            elif v in RAW_TYPES:
                body_text += f'        self.{rk} = data["{raw_name}"]\n'
            elif v.startswith('Optional['):
                type_name = v[9:-1]
                if type_name in RAW_TYPES:
                    body_text += f'        self.{rk} = data.get("{raw_name}")\n'
                else:
                    body_text += f'        self.{rk} = {type_name}(data.get("{raw_name}")) if data.get("{raw_name}") else None\n'
            else:
                body_text += f'        self.{rk} = {v}(data["{raw_name}"])\n'
        '''

    body_text += '\n\n'

    return (predefs, body_text)
