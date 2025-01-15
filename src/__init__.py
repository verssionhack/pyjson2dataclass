import json
import os.path as op
import os
from case_convert import pascal_case, snake_case
from importlib import import_module
from .field import Field
from .tree import Tree, json2tree, struct_tree, tree2dataclass
from .utils import repair_name, DATACLASS_FILE_HEADER
import sys
sys.path.append('.')


def json2dataclass(main_name: str, data) -> str:
    if isinstance(data, (dict, list)):
        tree = json2tree(data)
        tree.struct_concat()
        tree.upstair()
        _main_name = Field(main_name, tree.layers)
        no_data_field = False
        if not tree.layers.empty:
            tree = Tree(
                    struct={_main_name.repair.field: _main_name},
                    children={_main_name.repair.field: tree}
                    )
            tree.children_upstair()
            no_data_field = True
        body, _predefs = tree2dataclass(_main_name.repair.pascal.field, tree, no_data_field)
    else:
        _main_name = Field(main_name)
        data_struct = struct_tree(data)
        data_field = Field('Any' if data_struct is None else data_struct, is_any=data_struct is None)
        tree = Tree(
                struct={_main_name.repair.field: data_field}
                )
        body, _predefs = tree2dataclass(_main_name.repair.pascal.field, tree, True)

    predefs = []

    for predef in _predefs:
        if predef.strip() not in predefs:
            predefs.append(predef.strip())

    context = DATACLASS_FILE_HEADER
    for predef in predefs:
        context += predef + '\n\n\n'

    return context + body


def do_parse(save_dir: str, inputs: list[str], pascal: bool = False, overwrite: bool = False):
    for i in inputs:

        if not op.isfile(i):
            continue

        data = json.load(open(i))

        file_name = op.basename(i)

        if '.' in file_name:
            file_name = file_name[:file_name.rfind('.')]

        pascal_name = pascal_case(file_name)
        file_name = pascal_case(file_name) if pascal else snake_case(file_name)
        file_name = repair_name(file_name)
        if not op.exists(save_dir):
            os.makedirs(save_dir)
        if not op.exists(op.join(save_dir, f'{file_name}.py')) or overwrite:
            open(op.join(save_dir, f'{file_name}.py'), 'w').write(json2dataclass(file_name, data))


def do_test(dataclass_dir: str, json_dir: str):

    def path2modulepath(path: str):
        if path.startswith('/'):
            raise Exception('do not start with /')
        mpath = []
        r = ''
        path, r = op.split(path)
        while path:
            mpath.insert(0, r)
            (path, r) = op.split(path)
        mpath.insert(0, r)
        return '.'.join(mpath)

    passed = []
    failed = []
    ignored = []

    for jsonfile in [op.join(json_dir, i) for i in os.listdir(json_dir) if op.isfile(op.join(json_dir, i))]:
        test_dataclass_name = op.basename(jsonfile)
        if '.' in test_dataclass_name:
            test_dataclass_name = repair_name(test_dataclass_name[:test_dataclass_name.rfind('.')])
        test_dataclass_name_s = snake_case(test_dataclass_name)
        test_dataclass_name_p = pascal_case(test_dataclass_name)
        test_dataclass_name_p = test_dataclass_name_p[0].upper() + test_dataclass_name_p[1:]

        test_dataclass_filepath_s = op.join(dataclass_dir, test_dataclass_name_s) + '.py'
        test_dataclass_filepath_p = op.join(dataclass_dir, test_dataclass_name_p) + '.py'

        if op.isfile(test_dataclass_filepath_s):
            test_dataclass_filepath = test_dataclass_filepath_s
            test_dataclass_name = test_dataclass_name_s
        elif op.isfile(test_dataclass_filepath_p):
            test_dataclass_filepath = test_dataclass_filepath_p
            test_dataclass_name = test_dataclass_name_p
        else:
            print(f'dataclass file for "{jsonfile}" not found')
            ignored.append(jsonfile)
            continue

        test_json = json.load(open(jsonfile))

        if dataclass_dir == '.':
            print(f'import {test_dataclass_name}')
            test_dataclass_module = import_module(f'{test_dataclass_name}')
        else:
            print(f'import {path2modulepath(dataclass_dir)}.{test_dataclass_name}')
            test_dataclass_module = import_module(f'{path2modulepath(dataclass_dir)}.{test_dataclass_name}')

        try:
            test_json_dataclass = eval(f'test_dataclass_module.{test_dataclass_name_p}({test_json})')
            print(test_json_dataclass)
            print()
            passed.append(jsonfile)
        except Exception as e:
            print(f'{e}')
            failed.append(jsonfile)

    print(f'Amounts: {len(passed) + len(failed) + len(ignored)}')
    print(f'Passed: {len(passed)}')
    print(f'Failed: {len(failed)}')
    print(f'Ignored: {len(ignored)}')
    if len(passed) > 0:
        print()
        print('Passed:')
        for i in passed:
            print(i)
    if len(failed) > 0:
        print()
        print('Failed:')
        for i in failed:
            print(i)
    if len(ignored) > 0:
        print()
        print('Ignored:')
        for i in ignored:
            print(i)
