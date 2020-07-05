from wyr.generators.trainingdata import TrainingData
from wyr.constants import DEFAULT_MODEL_PATH
import os.path
import spacy
from spacy.util import minibatch, compounding
import random
import warnings
from pathlib import Path
from functools import lru_cache
from wyr.console import Console


class TrainedModels(object):
    def __init__(self, model_dir: str = DEFAULT_MODEL_PATH,
                 training_data: str = None, console: Console = None):
        self.training_data = TrainingData(training_data)
        self.model_dir = model_dir
        if console is None:
            console = Console()
        self.__console = console

    @lru_cache
    def get_or_train(self, level: int):
        if self.__needs_training(level):
            self.__console.info(f'Need to train {self.label(level)}...')
            return self.__train(level)

        try:
            return spacy.load(self.model_path(level))
        except:  # Need to train :/
            self.__console.warn(f'Model {self.label(level)} not found.  Building it...')
            return self.__train(level)

    def __needs_training(self, level: int):
        # Needs training if does not exist
        if not self.model_qsize_path(level).exists():
            return True

        # Needs training if more questions exist now
        try:
            qsize = int(self.model_qsize_path(level).read_text().strip())
        except:
            return True
        else:
            if qsize < len(self.training_data.questions):
                return True

        # Does not need retrained
        return False

    def model_path(self, level: int) -> Path:
        return Path(f'{self.model_dir}/{self.label(level)}')

    def model_qsize_path(self, level: int) -> Path:
        return self.model_path(level) / 'qsize'

    def label(self, level: int) -> str:
        return f'choices{level}'

    def retrain(self):
        self.get_or_train.cache_clear()
        for level in [1, 2]:
            self.__console.info(f'Retraining {self.label(level)}...')
            self.__train(level)

    def __train(self, level: int, n_iter=40):
        label = self.label(level)
        prepared_data = self.training_data.prepare_data(level, label)
        model_path = self.model_path(level)

        # Setup model path, verify access
        model_path.mkdir(parents=True, exist_ok=True)

        random.seed(0)
        nlp = spacy.blank('en')
        self.__console.info('Created blank model')

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
            with self.__console.timed(f'Training model {label}', 'Trained model in {0:.3f}s'):
                for itn in range(n_iter):
                    random.shuffle(prepared_data)
                    batches = minibatch(prepared_data, size=sizes)
                    losses = {}
                    for batch in batches:
                        texts, annotations = zip(*batch)
                        nlp.update(texts, annotations, sgd=optimizer, drop=0.35, losses=losses)
                    self.__console.info("Losses", losses)

        # test the trained model
        test_text = random.choice(self.training_data.questions)
        doc = nlp(test_text)
        self.__console.info("Entities in '%s'" % test_text)
        for ent in doc.ents:
            self.__console.info(ent.label_, ent.text)

        # save model to output directory
        nlp.meta["name"] = label
        nlp.to_disk(model_path)
        self.__console.okay("Saved model to", model_path)

        # test the saved model
        self.__console.info("Loading from", model_path)
        nlp2 = spacy.load(model_path)
        # Check the classes have loaded back consistently
        assert nlp2.get_pipe("ner").move_names == move_names
        doc2 = nlp2(test_text)
        for ent in doc2.ents:
            self.__console.info(ent.label_, ent.text)

        self.model_qsize_path(level).write_text(str(len(self.training_data.questions)))
        return nlp
