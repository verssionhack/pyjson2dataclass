from typing import Dict, List, Tuple, Optional, Self
from .field import Field, Layers
from .utils import ESCAPE_CHAR
from dataclasses import dataclass


@dataclass
class Tree:
    struct: Dict[str, Field]
    children: Dict[str, Self]
    children_list: List[Self | Field]
    layers: Layers

    def __init__(self,
                 struct: Dict[str, Field] | None = None,
                 children: Dict[str, Self] | None = None,
                 children_list: List[Self | Field] | None = None,
                 layers: Layers | None = None):
        self.struct = struct if struct else {}
        self.children = children if children else {}
        self.children_list = children_list if children_list else []
        for k in self.children:
            self.children[k].layers.concat_with(self.struct[k].layers)
            self.struct[k].layers = self.children[k].layers
        self.layers = layers if layers else Layers([])

        self._do_link_layers()

    def key_exists(self, key: str) -> bool:
        return key in self.struct

    def is_children(self, key: str) -> bool:
        return key in self.children and isinstance(self.children[key], Tree)

    def is_field(self, key: str) -> bool:
        return key in self.struct and not self.is_children(key)

    def field_set(self, key: str, field: Field):
        if (last_field := self.struct.get(key)):
            pass

        self.struct[key] = field.copy

        self._do_link_layers()

    def _do_link_layers(self):
        for k in self.struct:
            if self.is_children(k):
                if self.struct[k].layers.empty:
                    self.struct[k].layers = self.children[k].layers
                self.children[k].layers.concat_with(self.struct[k].layers)
                self.struct[k].layers = self.children[k].layers
                self.children[k]._do_link_layers()

        for children in self.children_list:
            if isinstance(children, Tree):
                children._do_link_layers()

    @property
    def copy(self):
        ret = eval(str(self))
        ret._do_link_layers()
        return ret

    @property
    def is_dict(self) -> bool:
        return len(self.struct) > 0 or self.layers.outer_is('Dict')

    @property
    def is_list(self) -> bool:
        return len(self.children_list) > 0 or self.layers.outer_is('List')

    def field_get(self, key: str) -> Field:
        return self.struct[key]

    def children_get(self, key: str) -> Self:
        return self.children[key]

    def children_list_add(self, children: Self | Field):
        self.children_list.append(children.copy)

    def children_set(self, key: str, field: Field, children: Self):
        self.field_set(key, field.copy)

        if (last_children := self.children.get(key)):
            pass

        self.children[key] = children.copy

        self._do_link_layers()

    def struct_concat_by_key(self, other: Self, key: str):
        if self.key_exists(key) and other.key_exists(key): # both have key
            if self.is_children(key) and other.is_children(key): # both is children
                self.children_get(key).struct_concat_children_list_with(other.children_get(key))
                self.children_get(key).struct_concat_with(other.children_get(key), force=True)

            elif self.is_children(key) and other.is_field(key):
                if key == 'illusts' and other.field_get(key).is_any:
                    breakpoint()
                if other.field_get(key).is_any: # self is children but other is field
                    self.field_get(key).layers.outer_add_layer('Optional')
                    self.children_get(key).layers.outer_add_layer('Optional')
                elif not (other.field_get(key).is_list and self.children_get(key).is_list # both list
                        or other.field_get(key).is_dict and self.children_get(key).is_dict): # both dict
                    raise Exception(f'[{key}] type mismatch\nself={self.children_get(key)}\nother={other.field_get(key)}')

            elif other.is_children(key) and self.is_field(key):# self is field but other is children
                if self.field_get(key).is_any:
                    other.field_get(key).layers.outer_add_layer('Optional')
                    other.children_get(key).layers.outer_add_layer('Optional')
                    self.field_set(key, other.field_get(key))
                elif not (self.field_get(key).is_list and other.children_get(key).is_list # both list
                        or self.field_get(key).is_dict and other.children_get(key).is_dict): # both dict
                    raise Exception(f'[{key}] type mismatch\nself={self.field_get(key)}\nother={other.children_get(key)}')

                self.children_set(key, other.field_get(key), other.children_get(key))
            else:
                if self.field_get(key).field != other.field_get(key).field:
                    if self.field_get(key).is_any:
                        other.field_get(key).layers.outer_add_layer('Optional')
                        self.field_set(key, other.field_get(key))
                    elif other.field_get(key).is_any:
                        self.field_get(key).layers.outer_add_layer('Optional')
                    else:
                        raise Exception(f'[{key}] type mismatch\nself={self.field_get(key)}\nother={other.field_get(key)}')
                self.field_get(key).layers.concat_with(other.field_get(key).layers)

        elif self.key_exists(key): # self have key
            self.field_get(key).layers.outer_add_layer('Optional')

        elif other.key_exists(key): # other have key
            self.field_set(key, other.field_get(key))
            if other.is_children(key):
                self.children_set(key, other.field_get(key), other.children_get(key))
            self.field_get(key).layers.outer_add_layer('Optional')

    def struct_concat_children_list_with(self, other: Self):
        self.layers.concat_with(other.layers)
        if self.is_list and other.is_list:
            self.struct_concat_children_list()
            other.struct_concat_children_list()
            if len(other.children_list) == 0:
                pass
            elif len(self.children_list) == 0 and len(other.children_list) > 0:
                self.children_list = [other.children_list[0]]
            elif len(self.children_list) > 0 and len(other.children_list) > 0:
                if isinstance(self.children_list[0], Tree) and isinstance(other.children_list[0], Tree):
                    self.children_list[0].struct_concat_with(other.children_list[0], force=True)
                if isinstance(self.children_list[0], Field) and isinstance(other.children_list[0], Field):
                    if self.children_list[0].field != other.children_list[0].field:
                        raise Exception(f'type mismatch\nself={self.children_list[0]}\nother={other.children_list[0]}')

    def struct_concat_children_list(self):
        fields = []
        childrens = []
        for children in self.children.values():
            children.struct_concat_children_list()
        for children in self.children_list:
            if isinstance(children, Field):
                fields.append(children)
            else:
                childrens.append(children)
        for field in fields[1:]:
            if fields[0].field != field.field:
                raise Exception(f'field mismatch\nfields[0]={fields[0]}\nfields[{fields.index(field)}]={field}')
            fields[0].layers.concat_with(field.layers)
        for children in childrens:
            children.struct_concat_children_list()
        for children in childrens[1:]:
            childrens[0].struct_concat_with(children, force=True)
            childrens[0].layers.concat_with(children.layers)

        if len(fields) > 0 and len(childrens) > 0:
            if not (fields[0].is_list and childrens[0].is_list # both list
                    or fields[0].is_dict and childrens[0].is_dict): # both dict
                raise Exception(f'type mismatch\nfield={fields[0]}\nchildren={childrens[0]}')
            self.children_list = [childrens[0]]
        elif len(childrens) > 0:
            self.children_list = [childrens[0]]
        elif len(fields) > 0:
            self.children_list = [fields[0]]

    def upstair(self):
        self.children_list_upstair()
        self.children_upstair()

    def children_upstair(self):
        pending_pop_keys = []
        pending_pop_keys_any = []
        for k, children in self.children.items():
            children.children_upstair()
            if len(children.children_list) == 1 and isinstance(children.children_list[0], Field):
                pending_pop_keys.append(k)
            if len(children.struct) == 0 and len(children.children_list) == 0:
                pending_pop_keys_any.append(k)

        for children in self.children_list:
            if isinstance(children, Tree):
                children.children_upstair()

        for k in pending_pop_keys:
            _layers = self.field_get(k).layers
            children = self.children.pop(k)
            _layers.extend(children.children_list[0].layers)
            self.field_set(k, children.children_list[0])
            self.field_get(k).layers = _layers
        for k in pending_pop_keys_any:
            children = self.children.pop(k)
            self.field_set(k, self.field_get(k).replace_field('Any'))
            self.field_get(k).layers._inner.clear()
            self.field_get(k).is_any = True

    def children_list_upstair(self):
        pending_pop_keys = []
        for k, children in self.children.items():
            children.children_list_upstair()
            if len(children.children_list) > 0 and isinstance(children.children_list[0], Field):
                pending_pop_keys.append(k)

        for children in self.children_list:
            if isinstance(children, Tree):
                children.children_list_upstair()

        for k in pending_pop_keys:
            children = self.children.pop(k)
            self.struct[k].layers.extend(children.children_list[0].layers)
            self.struct[k].field = children.children_list[0].field

        if len(self.children_list) == 1:
            if isinstance(self.children_list[0], Tree):
                if len(self.children_list[0].children_list) > 0 and isinstance(self.children_list[0].children_list[0], Field):
                    self.layers.extend(self.children_list[0].layers)
                    self.layers.extend(self.children_list[0].children_list[0].layers)
                    self.children_list = [self.children_list[0].children_list[0]]
                else:
                    self.layers.extend(self.children_list[0].layers)
                    self.struct = self.children_list[0].struct
                    self.children = self.children_list[0].children
                    self.children_list = self.children_list[0].children_list
        self._do_link_layers()

    def struct_concat_with(self, other: Self, force: bool = False):
        self_keys = set(self.struct)
        other_keys = set(other.struct)
        if len(self_keys & other_keys) == 0 and not force:
            return
        if self.layers.empty:
            self.layers = other.layers
        self.layers.concat_with(other.layers)
        both_keys = self_keys | other_keys

        for both_key in both_keys:
            self.struct_concat_by_key(other, both_key)
        self.struct_concat_children_list_with(other)

    def struct_concat(self):
        self.struct_concat_children_list()
        needed_concat = False
        fields = []
        childrens = []
        for k in self.struct:
            if len(k) == 0 or k[0].isdigit() or len(set(k) & set(ESCAPE_CHAR[''])) > 0:
                needed_concat = True
                if self.is_field(k):
                    fields.append(self.field_get(k))

        for children in self.children.values():
            children.struct_concat()
            childrens.append(children)

        for children in self.children_list:
            if isinstance(children, Tree):
                children.struct_concat()

        if needed_concat:
            self.struct.clear()
            self.children.clear()
            self.children_list = childrens
            self.struct_concat_children_list()

            _tree = Tree(children_list=fields)
            _tree.struct_concat_children_list()

            if len(self.children_list) == 0 and len(_tree.children_list) > 0:
                self.children_list = [_tree.children_list[0]]
            if len(_tree.children_list) > 0 and _tree.children_list[0].is_any:
                self.children_list[0].layers.outer_add_layer('Optional')
            self.layers.outer_add_layer('Dict')
        self._do_link_layers()


def struct_tree(value):
    if value is None:
        return None
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
        return value.__class__.__name__


def parse_tree(value):
    tree = Tree()
    if isinstance(value, dict):
        is_optional = False
        for v in value.values():
            if v is None:
                is_optional = True
        for k, v in value.items():
            if v is None:
                _field = Field('Any')
                _field.is_any = True
                tree.field_set(k, _field)
            elif isinstance(v, (dict, list)):
                if len(v) == 0:
                    tree.field_set(k, Field(v.__class__.__name__))
                else:
                    tree.children_set(k, Field(k), parse_tree(v))
            else:
                tree.field_set(k, Field(v))
            # if is_optional:
            #     tree.field_get(k).layers.inner_add_layer('Optional')
            #     if k in tree.children:
            #         tree.children_get(k).layers.inner_add_layer('Optional')
    elif isinstance(value, list):
        tree.layers.outer_add_layer('List')
        is_optional = False
        for v in value:
            if v is None:
                is_optional = True
        if is_optional:
            tree.layers.inner_add_layer('Optional')
        for v in value:
            if v is None:
                continue
            elif isinstance(v, (dict, list)):
                tree.children_list_add(parse_tree(v))
            else:
                tree.children_list_add(Field(v))
    return tree


def json2tree(data: dict | list) -> Tree:
    _parsed_tree = struct_tree(data)
    _parsed_tree = parse_tree(_parsed_tree)
    return _parsed_tree


def tree2dataclass(name: str, tree: Tree, no_data_field: bool = False) -> Tuple[str, List[str]]:
    body = f'@dataclass\nclass {name}:\n'
    predef = []

    for k, children in tree.children.items():
        field = tree.field_get(k)
        k = Field(k)

        cbody, cpredef = tree2dataclass(field.dataclass_name, children)
        predef.extend(cpredef)
        predef.append(cbody)

    for k, v in tree.struct.items():
        k = Field(k)
        if not tree.is_field(k.field):
            v = v.replace_field(v.dataclass_name)
        body += f'    {k.snake.repair.field}: {v.pack}\n'

    body += '\n'
    body += '    def __init__(self, data):\n'

    for k, v in tree.struct.items():
        k = Field(k)
        if not tree.is_field(k.field):
            v = v.replace_field(v.dataclass_name)
        data_field = f'data.get("{k.field}")'
        if no_data_field:
            data_field = 'data'
        body += f'        self.{k.snake.repair.field} = {v.parse}\n'.format(data=data_field)
    return (body[:-1], predef)
