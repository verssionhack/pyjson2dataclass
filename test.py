def optional_name_trans(s: str):
    if (i := s.find('.get(')) != -1:
        j = s.rfind(')')
        s = s[:i] + f'[{s[i + 5:j]}]' + s[j + 1:]
    return s

print(optional_name_trans('data.get("tets")'))
