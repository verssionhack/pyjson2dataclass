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
    def V(v: str, N: str, D: int = 0):

        def optional_name_trans(s: str):
            if (i := s.find('.get(')) != -1:
                j = s.rfind(')')
                s = s[:i] + f'[{N[i + 5:j]}]' + s[j + 1:]
            return s

        layers, v = unpack_raw_field(v, 1)
        if len(layers) == 0:
            return f'{v}({N})'
        match layers[-1]:
            case 'Optional':
                return f'{V(v, optional_name_trans(N), D + 1)} if {N} else None'
            case 'Dict':
                return f'dict([(k{D}, {V(v, "v" + str(D), D + 1)}) for k{D}, v{D} in {N}.items()])'
            case 'List':
                return f'[{V(v, "i" + str(D), D + 1)} for i{D} in {N}]'

    return V(field, raw_name)
