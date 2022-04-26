import argparse
import random
import sys
from wyr.generators.inferkit import InferKitClient
from wyr.generators.trainingdata import TrainingData
from wyr.interpreter import ChoiceInterpreter
from wyr.constants import QUESTION_SEPARATOR, DEFAULT_MODEL_PATH, DEFAULT_GPT2_MODEL, GPT2_MODELS
from wyr.senders.mastodon import MastodonPoster
from wyr.trainer import TrainedModels
from wyr.generators.twitter import TweetGrabber
from wyr.generators.localgpt2 import LocalGpt2

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

    inferkit_parser = subparsers.add_parser('inferkit', help='Fetch a question from InferKit')
    inferkit_parser.add_argument(
        'token', type=str, help='InferKit API Token filename'
    )
    inferkit_parser.add_argument(
        '--prompt', '-p', type=str, default='Would you rather', help='Prompt to begin text generation'
    )
    inferkit_parser.set_defaults(generator=build_inferkit)

    read_parser = subparsers.add_parser('read', help='Read a previously fetched question from training data (for testing)')
    read_parser.set_defaults(generator=build_reader)

    search_parser = subparsers.add_parser('tweets', help='Search twitter for results')
    search_parser.add_argument(
        'keys', type=str, help='Auth keys filename'
    )
    search_parser.add_argument(
        '--prompt', '-p', type=str, default='"Would you rather"',
        help='Query to search for'
    )
    search_parser.set_defaults(generator=build_searcher)

    gpt2_parser = subparsers.add_parser('gpt2', help='Generate using local GPT2')
    gpt2_parser.add_argument(
        '--gpt2-model', '-g', choices=GPT2_MODELS, default=DEFAULT_GPT2_MODEL,
        help='GPT2 model to use for text generation'
    )
    gpt2_parser.add_argument(
        '--prompt', '-p', type=str, default='Would you rather',
        help='Prompt to begin text generation'
    )
    gpt2_parser.add_argument(
        '--temperature', '-T', type=float, default=1.0,
        help='Generation temperature (1.0 = average, higher is more "creative")'
    )
    gpt2_parser.set_defaults(generator=build_gpt2)

    parser.add_argument(
        '--count', '-c', type=int, default=1,
        help='Number of requests to fetch (helpful for model training)'
    )
    parser.add_argument(
        '--massage', '-M', action='store_true',
        help='Massage the question for human readability & guess choices'
    )
    parser.add_argument(
        '--retrain', '-R', action='store_true',
        help='Retrain the choice interpreter'
    )
    parser.add_argument(
        '--mastodon-token', type=str,
        default='',
        help='Filename of mastodon token'
    )
    parser.add_argument(
        '--model-dir', '-m', type=str,
        default=DEFAULT_MODEL_PATH,
        help='Trained model directory'
    )
    parser.add_argument(
        '--training-data', '-T', type=str,
        default=None,
        help='Training data filename -- by default loads package data'
    )
    parser.add_argument(
        '--version', action='store_true',
        help='Print version ({}) and exit'.format(VERSION)
    )
    return parser


def build_inferkit(args):
    client = InferKitClient(args.token)

    def generate(count):
        return [client.generate(args.prompt) for _ in range(count)]
    return generate


def build_reader(args):
    client = TrainingData(args.training_data)

    def generate(count):
        return random.sample(client.questions, count)

    return generate


def build_searcher(args):
    grabber = TweetGrabber(args.keys)

    def generate(count):
        return [grabber.random_tweet(args.prompt) for _ in range(count)]

    return generate


def build_gpt2(args):
    client = LocalGpt2(args.model_dir, args.gpt2_model)

    def generate(count):
        return client.generate(prompt=args.prompt, temperature=args.temperature, count=count)

    return generate


# MAIN


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return
    elif not hasattr(args, 'generator'):
        parser.print_help(sys.stderr)
        exit(1)

    should_massage = bool(args.massage or args.mastodon_token)
    should_load_models = bool(should_massage or args.retrain)

    generate = args.generator(args)
    models = TrainedModels(args.model_dir, args.training_data) if should_load_models else None
    masseuse = ChoiceInterpreter(models) if should_massage else None
    if args.retrain:
        models.retrain()

    for question in generate(args.count):
        if args.mastodon_token:
            question = MastodonPoster(args.mastodon_token, masseuse).post(question)
        elif masseuse:
            question = masseuse.massage_question(question)
        print(question)
        if args.count > 1:
            print(QUESTION_SEPARATOR, flush=True)


if __name__ == '__main__':
    main()
