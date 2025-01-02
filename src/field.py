from typing import List, Tuple, Optional, Self
from dataclasses import dataclass
from case_convert import camel_case, pascal_case, snake_case
from .utils import RAW_TYPES, repair_name


@dataclass
class Layers:
    _inner: List[str]

    @property
    def len(self):
        return len(self._inner)

    def __getitem__(self, i) -> str:
        return self._inner[i]

    def outer_is(self, layer: str) -> bool:
        return not self.empty and self._inner[0] == layer

    def inner_is(self, layer: str) -> bool:
        return not self.empty and self._inner[-1] == layer

    def __add__(self, o: Self):
        return Layers(self._inner + o._inner)

    def extend(self, other: Self):
        self._inner.extend(other._inner)

    @property
    def _full_layers(self):
        ret = []
        i = 0
        while i < self.len:
            is_optional = False
            if self._inner[i] == 'Optional':
                is_optional = True
                i += 1
            if i == self.len:
                break
            ret.append((self._inner[i], is_optional))
            i += 1
        if not self.empty:
            ret.append(self._inner[-1] == 'Optional')
        else:
            ret.append(False)
        return ret

    @property
    def inner_optional(self) -> bool:
        return self.inner_is('Optional')

    @property
    def outer_optional(self) -> bool:
        return self.outer_is('Optional')

    def outer_add_layer(self, layer: str):
        if self.outer_optional and layer == 'Optional':
            return
        self._inner.insert(0, layer)

    def inner_add_layer(self, layer: str):
        if self.inner_optional and layer == 'Optional':
            return
        self._inner.append(layer)

    @property
    def empty(self) -> bool:
        return len(self._inner) == 0

    @property
    def parse(self) -> str:
        def V(v: str, N: str, D: int = 0):
            if self.empty or D == len(self._inner):
                return f'{v}({N})'
            match self._inner[D]:
                case 'Optional':
                    return f'({V(v, N, D + 1)}) if {N} is not None else None'
                case 'List':
                    return f'[({V(v, "i" + str(D), D + 1)}) for i{D} in {N}]'
                case 'Dict':
                    return f'dict([(k{D}, {V(v, "v" + str(D), D + 1)}) for k{D}, v{D} in {N}.items()])'
            raise Exception(f'Unknown layer "{self._inner[D]}"')

        return V('{field}', '{{data}}')

    def concat_with(self, other: Self):
        new_layers = Layers([])
        _non_opt_self_layers = Layers([layer for layer in self._inner if layer != 'Optional'])
        _non_opt_other_layers = Layers([layer for layer in other._inner if layer != 'Optional'])
        if _non_opt_self_layers.len != _non_opt_other_layers.len:
            raise Exception(f'NonOptionalLayers self.len != other.len\nself={_non_opt_self_layers._inner}\nother={_non_opt_other_layers._inner}')

        for i in range(_non_opt_self_layers.len):
            if _non_opt_self_layers._inner[i] != _non_opt_other_layers._inner[i]:
                raise Exception(f'NonOptionalLayers self[{i}] != other[{i}]\nself={_non_opt_self_layers._inner}\nother={_non_opt_other_layers._inner}')

        _self_layers = self._full_layers
        _other_layers = other._full_layers
        for i in range(len(_self_layers) - 1):
            layer, optional = _self_layers[i][0], _self_layers[i][1] | _other_layers[i][1]
            # print(f'[{i}] {layer} {optional}')
            if optional:
                new_layers.inner_add_layer('Optional')
            new_layers.inner_add_layer(layer)

        if _self_layers[-1] | _other_layers[-1]:
            new_layers.inner_add_layer('Optional')
        self._inner = new_layers._inner


@dataclass
class Field:
    field: str
    layers: Layers
    is_any: bool

    def __init__(self, field: str, layers: List[str] | Layers = [], is_any: bool = False):
        _layers, self.field, _ = _unpack_field(field=field)
        if isinstance(layers, list):
            self.layers = Layers(layers + _layers)
        else:
            self.layers = Layers(layers._inner + _layers)
        self.is_any = is_any

    def replace_field(self, new_field: str):
        return Field(new_field, self.layers)

    @property
    def copy(self):
        return eval(str(self))

    @property
    def is_raw_type(self):
        return self.field in RAW_TYPES

    @property
    def is_list(self):
        return self.field == 'list' or self.layers.outer_is('List')

    @property
    def is_dict(self):
        return self.field == 'dict' or self.layers.outer_is('Dict')

    @property
    def pack(self):
        return _pack_field(field=self.field, layers=self.layers._inner)

    @property
    def camel(self):
        return Field(field=camel_case(self.field), layers=self.layers._inner)

    @property
    def pascal(self):
        return Field(field=pascal_case(self.field), layers=self.layers._inner)

    @property
    def snake(self):
        return Field(field=snake_case(self.field), layers=self.layers._inner)

    @property
    def repair(self):
        return Field(field=repair_name(self.field), layers=self.layers._inner)

    @property
    def parse(self):
        if self.is_any:
            return '{data}'
        return self.layers.parse.format(field=self.field)

    @property
    def dataclass_name(self):
        ret = self.repair.pascal.field
        full_layers = self.layers._full_layers
        if len(full_layers) > 1:
            if full_layers[0][0].lower() in ['list']:
                ret += 'I'
            else:
                ret += 'V'
        return ret


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


def _unpack_field(field: str,
                  deep: int = -1) -> Tuple[List[str], str, Optional[str]]:
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
