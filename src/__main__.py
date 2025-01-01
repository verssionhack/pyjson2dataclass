#!/bin/python3


from .__init__ import do_parse
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('-d', '--save-dir',
                    default='.',
                    type=str,
                    dest='save_dir',
                    help='specify the directory parsed dataclass file save to'
                    )

parser.add_argument('-i', '--input',
                    default=[],
                    type=str,
                    dest='input',
                    action='extend',
                    nargs='*',
                    help='specify the input json file path',
                    )

parser.add_argument('-p', '--pascal',
                    default=False,
                    dest='pascal',
                    action='store_true',
                    help='use pascalName for parsed dataclass filename'
                    )

parser.add_argument('-f', '--force',
                    default=False,
                    dest='overwrite',
                    action='store_true',
                    help='enable overwrite exists dataclass'
                    )


def main():
    args = parser.parse_args()

    do_parse(args.save_dir, args.input, args.pascal, args.overwrite)


if __name__ == '__main__':
    main()
