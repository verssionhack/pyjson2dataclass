#!/bin/python3


from pyjson2dataclass import do_test
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-d', '--dataclass-dir',
                    default='dataclass',
                    dest='dataclass_dir',
                    type=str,
                    help='specify parsed dataclass directory to be test',
                    )

parser.add_argument('-j', '--json-dir',
                    default='json',
                    dest='json_dir',
                    type=str,
                    help='specify json directory to be test',
                    )


def main():
    args = parser.parse_args()

    do_test(args.dataclass_dir, args.json_dir)


if __name__ == '__main__':
    main()
