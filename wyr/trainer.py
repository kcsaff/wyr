from wyr.constants import QUESTION_SEPARATOR, OUTER_CHOICE, INNER_CHOICE
from wyr.generators.reader import TrainingDataReader
import argparse
import spacy
from spacy.util import minibatch, compounding
import random
import warnings
from pathlib import Path

TEST_TEXT = """Would you rather your child put his or her hands on a hot stove or inside a burning apartment? Do you prefer your sweetheart to bring you a meal, or simply watch over you?

And if that's not a yes or no question, the answers from men and women are flipped on their head. "Would you rather have"""


def build_parser():
    parser = argparse.ArgumentParser(
        description='Wyr trainer: loads training data and trains on finding choices',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'training_data', type=str, help='Filename of data to load'
    )
    parser.add_argument(
        'model_dir', type=str, default='models/choices', help='Where to write the model'
    )
    return parser


def train(training_data, output_dir, label, n_iter=30):
    output_dir = f'{output_dir}/{label}'
    random.seed(0)
    nlp = spacy.blank('en')
    print('Created blank model')

    # Add entity recognizer to model if it's not in the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner)
    # otherwise, get it, so we can add labels to it
    else:
        ner = nlp.get_pipe('ner')

    ner.add_label(label)

    optimizer = nlp.begin_training()

    move_names = list(ner.move_names)
    # get names of other pipes to disable them during training
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    # only train NER
    with nlp.disable_pipes(*other_pipes) and warnings.catch_warnings():
        # show warnings for misaligned entity spans once
        warnings.filterwarnings("once", category=UserWarning, module='spacy')

        sizes = compounding(1.0, 4.0, 1.001)
        # batch up the examples using spaCy's minibatch
        for itn in range(n_iter):
            random.shuffle(training_data)
            batches = minibatch(training_data, size=sizes)
            losses = {}
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)
            print("Losses", losses)

    # test the trained model
    test_text = TEST_TEXT
    doc = nlp(test_text)
    print("Entities in '%s'" % test_text)
    for ent in doc.ents:
        print(ent.label_, ent.text)

    # save model to output directory
    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.meta["name"] = label
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)

        # test the saved model
        print("Loading from", output_dir)
        nlp2 = spacy.load(output_dir)
        # Check the classes have loaded back consistently
        assert nlp2.get_pipe("ner").move_names == move_names
        doc2 = nlp2(test_text)
        for ent in doc2.ents:
            print(ent.label_, ent.text)

# MAIN


def main():
    parser = build_parser()
    args = parser.parse_args()

    reader = TrainingDataReader(args.training_data)

    for level, label in enumerate((OUTER_CHOICE, INNER_CHOICE), 1):
        training_data = reader.prepare_data(level, label)
        print(training_data)
        train(training_data, args.model_dir, label)


if __name__ == '__main__':
    main()

