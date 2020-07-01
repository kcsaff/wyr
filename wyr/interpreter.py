from functools import cached_property
from typing import List
from wyr.trainer import TrainedModels
import spacy


class ChoiceInterpreter(object):
    """
    Attempt to interpret choices out of a string starting with "Would you rather".
    """
    def __init__(self, models: TrainedModels):
        self.__models = models

    @cached_property
    def __nlp(self):
        return spacy.load('en_core_web_sm')

    def massage_question(self, question: str) -> str:
        question = self.__remove_trailing_broken_sentence(question)
        choices = self.__find_best_choices(question)
        if len(choices) == 0:
            choices = ['yes', 'no']
        elif len(choices) == 1:
            choices = [choices[0], 'no']
        elif len(choices) > 4:
            choices = choices[:4]
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

    def __remove_trailing_broken_sentence(self, question: str) -> str:
        doc = self.__nlp(question)
        sentences = list(doc.sents)
        if len(sentences) > 1:
            last_sentence = sentences[-1].text
            if last_sentence.rstrip()[-1] not in '!?.':
                question = question[:-len(last_sentence)]
        return question.strip()

