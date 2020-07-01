from wyr.generators.trainingdata import TrainingData
from wyr.constants import DEFAULT_MODEL_PATH, DEFAULT_TRAINING_PATH
import spacy
from spacy.util import minibatch, compounding
import random
import warnings
from pathlib import Path
from functools import lru_cache

TEST_TEXT = """Would you rather your child put his or her hands on a hot stove or inside a burning apartment? Do you prefer your sweetheart to bring you a meal, or simply watch over you?

And if that's not a yes or no question, the answers from men and women are flipped on their head. "Would you rather have"""


class TrainedModels(object):
    def __init__(self, training_data: str = DEFAULT_TRAINING_PATH, model_dir: str = DEFAULT_MODEL_PATH):
        self.training_data = TrainingData(training_data)
        self.model_dir = model_dir

    @lru_cache
    def get_or_train(self, level: int):
        try:
            return spacy.load(self.model_path(level))
        except:  # Need to train :/
            return self.train(level)

    def model_path(self, level: int) -> str:
        return f'{self.model_dir}/{self.label(level)}'

    def label(self, level: int) -> str:
        return f'choices{level}'

    def train(self, level: int, n_iter=30):
        label = self.label(level)
        prepared_data = self.training_data.prepare_data(level, label)
        model_path = self.model_path(level)

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
                random.shuffle(prepared_data)
                batches = minibatch(prepared_data, size=sizes)
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
        if model_path is not None:
            model_path = Path(model_path)
            if not model_path.exists():
                model_path.mkdir()
            nlp.meta["name"] = label
            nlp.to_disk(model_path)
            print("Saved model to", model_path)

            # test the saved model
            print("Loading from", model_path)
            nlp2 = spacy.load(model_path)
            # Check the classes have loaded back consistently
            assert nlp2.get_pipe("ner").move_names == move_names
            doc2 = nlp2(test_text)
            for ent in doc2.ents:
                print(ent.label_, ent.text)

        return nlp
