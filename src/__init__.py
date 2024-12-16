from typing import dataclass_transform
from .utils import pascal2snake, snake2pascal, key2snake, key2pascal, parse, json, print_json, repair_name
import os.path as op
import os
from importlib import import_module


def do_parse(save_dir: str, inputs: list[str], pascal: bool = False, overwrite: bool = False):
    for i in inputs:

        data = json.load(open(i))

        if not isinstance(data, dict):
            continue

        file_name = op.basename(i)

        if '.' in file_name:
            file_name = file_name[:file_name.rfind('.')]

        pascal_name = snake2pascal(file_name)
        file_name = snake2pascal(file_name) if pascal else pascal2snake(file_name)
        file_name = repair_name(file_name)
        if not op.exists(save_dir):
            os.makedirs(save_dir)
        if not op.exists(op.join(save_dir, f'{file_name}.py')) or overwrite:
            open(op.join(save_dir, f'{file_name}.py'), 'w').write(parse(pascal_name[0].upper() + pascal_name[1:], data))


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

    for jsonfile in [op.join(json_dir, i) for i in os.listdir(json_dir)]:
        test_dataclass_name = op.basename(jsonfile)
        if '.' in test_dataclass_name:
            test_dataclass_name = repair_name(test_dataclass_name[:test_dataclass_name.rfind('.')])
        test_dataclass_name_s = pascal2snake(test_dataclass_name)
        test_dataclass_name_p = snake2pascal(test_dataclass_name)
        test_dataclass_name_p = test_dataclass_name_p[0].upper() + test_dataclass_name_p[1:]

        test_dataclass_filepath_s = op.join(dataclass_dir, test_dataclass_name_s) + '.py'
        test_dataclass_filepath_p = op.join(dataclass_dir, test_dataclass_name_p) + '.py'

        print(f'test {test_dataclass_filepath_s}')
        print(f'test {test_dataclass_filepath_p}')
        if op.isfile(test_dataclass_filepath_s):
            test_dataclass_filepath = test_dataclass_filepath_s
            test_dataclass_name = test_dataclass_name_s
        elif op.isfile(test_dataclass_filepath_p):
            test_dataclass_filepath = test_dataclass_filepath_p
            test_dataclass_name = test_dataclass_name_p
        else:
            print(f'dataclass file for "{jsonfile}" not found')
            continue

        test_json = json.load(open(jsonfile))

        if dataclass_dir == '.':
            print(f'import {test_dataclass_name}')
            test_dataclass_module = import_module(f'{test_dataclass_name}')
        else:
            print(f'import {path2modulepath(dataclass_dir)}.{test_dataclass_name}')
            test_dataclass_module = import_module(f'{path2modulepath(dataclass_dir)}.{test_dataclass_name}')

        test_json_dataclass = eval(f'test_dataclass_module.{test_dataclass_name_p}({test_json})')
        print(test_json_dataclass)
        print()

