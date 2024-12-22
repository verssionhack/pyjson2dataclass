from typing import List, Tuple, Optional, Self
from dataclasses import dataclass
from case_convert import camel_case, pascal_case, snake_case
from .utils import RAW_TYPES, repair_name


@dataclass
class Layers:
    inner: List[str]

    def __add__(self, o: Self):
        return Layers(self.inner + o.inner)

    @property
    def inner_optional(self):
        return self.inner and self.inner[-1] == 'Optional'

    @property
    def outer_optional(self):
        return self.inner and self.inner[0] == 'Optional'

    def add(self, layer: str):
        self.inner.insert(0, layer)

    @property
    def empty(self):
        return len(self.inner) == 0

    @property
    def parse(self):
        def V(v: str, N: str, D: int = 0):
            if self.empty or D == len(self.inner):
                return f'{v}({N})'
            match self.inner[D]:
                case 'Optional':
                    return f'({V(v, N, D + 1)}) if {N} is not None else None'
                case 'List':
                    return f'[({V(v, "i" + str(D), D + 1)}) for i{D} in {N}]'
                case 'Dict':
                    return f'dict([(k{D}, {V(v, "v" + str(D), D + 1)}) for k{D}, v{D} in {N}.items()])'
            raise Exception(f'Unknown layer "{self.inner[D]}"')

        return V('{field}', '{{data}}.get("{{data_field}}")')


@dataclass
class Field:
    field: str
    layers: Layers

    def __init__(self, field: str, layers: List[str] = []):
        _layers, self.field, _ = _unpack_field(field=field)
        self.layers = Layers(layers + _layers)

    @property
    def is_raw_type(self):
        return self.field in RAW_TYPES

    @property
    def is_list(self):
        return self.field == 'list' or not self.layers.empty and self.layers[0] == 'List'

    @property
    def is_dict(self):
        return self.field == 'Dict' or not self.layers.empty and self.layers[0] == 'Dict'

    @property
    def pack(self):
        return _pack_field(field=self.field, layers=self.layers.inner)

    @property
    def camel(self):
        return Field(field=camel_case(self.field), layers=self.layers.inner)

    @property
    def pascal(self):
        return Field(field=pascal_case(self.field), layers=self.layers.inner)

    @property
    def snake(self):
        return Field(field=snake_case(self.field), layers=self.layers.inner)

    @property
    def repair(self):
        return Field(field=repair_name(self.field), layers=self.layers.inner)

    @property
    def parse(self):
        return self.layers.parse.format(field=self.field)


def _pack_field(field: str, layers: List[str]):
    '''
        layers order: outer -> inner
        e: to pack int as Optional[List[Dict[str, int]]]
        input1: field = int, layers = Optional -> List -> Dict
        input2: field = List[Dict[str, int]], layers = Optional
        output: Optional[List[Dict[str, int]]]
    '''
    _layers, field, _ = _unpack_field(field)
    layers.extend(_layers)
    for layer in layers[::-1]:
        if layer == 'Dict':
            field = f'{layer}[str, {field}]'
        else:
            field = f'{layer}[{field}]'
    return field


def _unpack_field(field: str, deep: int = -1) -> Tuple[List[str], str, Optional[str]]:
    '''
        e.1
        input: Optional[List[Dict[str, int]]], deep = -1
        output: (Optional -> List -> Dict, int, None)
        e.2
        input: Optional[List[Dict[str, int]]], deep = 1
        output: (Optional, List[Dict[str, int]], List)
    '''
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
