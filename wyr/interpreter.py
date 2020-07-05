from functools import cached_property
from typing import List
from wyr.trainer import TrainedModels
import spacy


class ChoiceInterpreter(object):
    BASE_MODEL = 'en_core_web_sm'

    """
    Attempt to interpret choices out of a string starting with "Would you rather".
    """
    def __init__(self, models: TrainedModels, cut_length: int = 280, max_choice_count: int = 4):
        self.__models = models
        self.__cut_length = cut_length
        self.__max_choice_count = max_choice_count

    @cached_property
    def __nlp(self):
        try:
            return spacy.load(self.BASE_MODEL)
        except IOError as _:
            from spacy.cli import download
            download(self.BASE_MODEL)
            return spacy.load(self.BASE_MODEL)
            # TODO: auto-load on failure with `python -m spacy download en_core_web_sm` ?

    def massage_question(self, question: str) -> str:
        choices = self.__find_best_choices(question)
        if len(choices) > self.__max_choice_count:
            choices = choices[:self.__max_choice_count]
        question = self.__remove_trailing_broken_sentence(question[:self.__cut_length], choices)
        if len(choices) == 0:
            choices = ['yes', 'no']
        elif len(choices) == 1:
            choices = [choices[0], 'no']
        return question.strip() + ''.join(f'\n* {choice}' for choice in choices)

    def __find_best_choices(self, question: str) -> List[str]:
        outer_choices = self.__find_model_choices(question, 1)
        inner_choices = self.__find_model_choices(question, 2)
        if len(outer_choices) != len(inner_choices):
            return outer_choices
        for inner, outer in zip(inner_choices, outer_choices):
            if inner not in outer:
                return outer_choices
        return inner_choices

    def __find_model_choices(self, question: str, level: int) -> List[str]:
        doc = self.__models.get_or_train(level)(question)
        return [ent.text for ent in doc.ents]

    def __remove_trailing_broken_sentence(self, question: str, choices: List[str]) -> str:
        doc = self.__nlp(question)
        sentences = list(doc.sents)
        if len(sentences) > 1:
            last_sentence = sentences[-1].text
            possible_question = question[:-len(last_sentence)]
            if choices[-1] in possible_question:
                question = possible_question
        return question.strip()

