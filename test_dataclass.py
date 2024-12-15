#!/bin/python3


from json2dataclass import snake2pascal
from json2dataclass.__main__ import main
import os
import os.path as op
import json
from importlib import import_module


dataclass_dir = './dataclass'
json_dir = './json'
main(dataclass_dir, [op.join(json_dir, i) for i in os.listdir(json_dir) if not op.exists(op.join(json_dir, i))])

for dataclass in [op.join(dataclass_dir, i) for i in os.listdir(dataclass_dir)]:
    test_dataclass_name = op.basename(dataclass)
    test_dataclass_name_s = test_dataclass_name[:test_dataclass_name.find('.')]
    test_json_filepath = op.join(json_dir, test_dataclass_name_s) + '.json'

    if not op.isfile(test_json_filepath):
        continue

    test_json = json.load(open(test_json_filepath))
    test_dataclass_name_p = snake2pascal(test_dataclass_name_s)
    test_dataclass_name_p = test_dataclass_name_p[0].upper() + test_dataclass_name_p[1:]

    print(f'import {op.basename(dataclass_dir)}.{test_dataclass_name_s}')
    test_dataclass_module = import_module(f'{op.basename(dataclass_dir)}.{test_dataclass_name_s}')

    test_json_dataclass = eval(f'test_dataclass_module.{test_dataclass_name_p}({test_json})')
    print(test_json_dataclass)
    print()
