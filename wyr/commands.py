import argparse
import random
from wyr.generators.backend import InferKitClient
from wyr.generators.reader import TrainingDataReader
from wyr.interpreter import ChoiceInterpreter
from wyr.constants import QUESTION_SEPARATOR

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
    subparsers = parser.add_subparsers()

    fetch_parser = subparsers.add_parser('fetch', help='Fetch a question from InferKit')
    fetch_parser.add_argument(
        'token', type=str, help='InferKit API Token filename'
    )
    fetch_parser.add_argument(
        '--prompt', '-p', type=str, default='Would you rather', help='Prompt to begin text generation'
    )
    fetch_parser.set_defaults(generator=build_fetcher)

    read_parser = subparsers.add_parser('read', help='Read a previously fetched question from training data (for testing)')
    read_parser.add_argument(
        'filename', type=str, help='Training data filename'
    )
    read_parser.set_defaults(generator=build_reader)

    parser.add_argument(
        '--count', '-c', type=int, default=1,
        help='Number of requests to fetch (helpful for model training)'
    )
    parser.add_argument(
        '--massage', '-M', action='store_true',
        help='Massage the question for human readability'
    )
    parser.add_argument(
        '--version', action='store_true',
        help='Print version ({}) and exit'.format(VERSION)
    )
    return parser


def build_fetcher(args):
    client = InferKitClient(args.token)

    def generate():
        return client.generate(args.prompt)
    return generate


def build_reader(args):
    client = TrainingDataReader(args.filename)

    def generate():
        return random.choice(client.questions)

    return generate


# MAIN


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return

    generate = args.generator(args)
    interpreter = ChoiceInterpreter()

    for i in range(args.count):
        question = generate()
        if args.massage:
            question = interpreter.massage_question(question)

        print(question)
        if args.count > 1:
            print(QUESTION_SEPARATOR, flush=True)


if __name__ == '__main__':
    main()
