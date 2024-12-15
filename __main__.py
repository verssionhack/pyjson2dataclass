#!/bin/python3


from .utils import key2pascal, key2snake, parse, pascal2snake, snake2pascal, struct_tree, _parse_tree, print_json
import json as j
import sys
import os.path as op


def main(outdir='.', paths=sys.argv[1:]):
    for i in paths:

        data = j.load(open(i))

        if not isinstance(data, dict):
            continue


        file_name = op.basename(i)

        if '.' in file_name:
            file_name = file_name[:file_name.find('.')]

        '''
        print_json(data)
        print('struct_tree')
        print_json(struct_tree(data))
        print('key2snake')
        key2snake(data)
        print_json(data)
        print('key2pascal')
        key2pascal(data)
        print_json(data)
        '''
        pascal_name = snake2pascal(file_name)
        pascal_name = pascal_name[0].upper() + pascal_name[1:]
        open(op.join(outdir, f'{pascal2snake(file_name)}.py'), 'w').write(parse(pascal_name, data))


if __name__ == '__main__':
    main()
