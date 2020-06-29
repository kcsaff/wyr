import argparse
from wyr.backend import InferKitClient

import pkg_resources
try:
    VERSION = pkg_resources.require("wyr")[0].version
except:
    VERSION = 'DEV'


def build_parser():
    parser = argparse.ArgumentParser(
        description='Wyr: A script that asks Would You Rather questions\n  Version {}'.format(VERSION),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'token', type=str, help='InferKit API Token filename'
    )
    parser.add_argument(
        '--prompt', '-p', type=str, default='Would you rather', help='Prompt to begin text generation'
    )
    parser.add_argument(
        '--version', action='store_true',
        help='Print version ({}) and exit'.format(VERSION)
    )
    return parser

# MAIN


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return

    print(InferKitClient(args.token).generate(args.prompt))


if __name__ == '__main__':
    main()
