from typing import Dict, List, Tuple, Optional, Self
from .field import Field, Layers
from dataclasses import dataclass


@dataclass
class Tree:
    field: Optional[Field]
    struct: Dict[str, Field]
    children: Dict[str, Self]
    children_list: List[Self | Field]
    layers: Layers

    def __init__(self,
                 struct: Dict[str, Field] = {},
                 children: Dict[str, Self] = {},
                 children_list: List[Self | Field] = [],
                 layers: Layers = Layers([])):
        self.struct = struct
        self.children = children
        self.children_list = children_list
        _layers = None
        for _children in self.children_list:
            if _layers is None:
                _layers = _children.layers
            else:
                _children.layers = _layers
        for k in self.children:
            self.children[k].layers = self.struct[k].layers
        self.layers = layers

    def children_add(self, field: Field, children: )
