from collections import defaultdict
from functools import cached_property
from typing import List
from wyr.trainer import TrainedModels
import spacy

SENTENCE_ENDERS = '.!?-:'
POSSIBLE_SENTENCE_ENDERS = '\'")]}'


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

    def split_question_choices(self, question):
        question = self.__remove_trailing_broken_sentence(question[:self.__cut_length])
        choices = self.__find_best_choices(question)
        if len(choices) > self.__max_choice_count:
            choices = choices[:self.__max_choice_count]
        if len(choices) == 0:
            choices = ['yes', 'no']
        elif len(choices) == 1:
            choices = [choices[0], 'no']
        return question.strip(), choices

    def massage_question(self, question: str) -> str:
        question, choices = self.split_question_choices(question)
        return question + ''.join(f'\n* {choice}' for choice in choices)

    def __find_best_choices(self, question: str) -> List[str]:
        outer_choices = self.__find_model_choices(question, 1, filtered=True)
        inner_choices = self.__find_model_choices(question, 2, filtered=True)

        # This is just a weird heuristic
        if 2 <= len(outer_choices) != len(inner_choices):
            return outer_choices
        elif len(outer_choices) < 2 <= len(inner_choices):
            return inner_choices

        choices = []
        for inner, outer in zip(inner_choices, outer_choices):
            if inner in outer:
                choices.append(inner)
            else:
                choices.append(outer)
        return choices

    def __find_model_choices(self, question: str, level: int, *, filtered: bool = False) -> List[str]:
        doc = self.__models.get_or_train(level)(question)
        choices = [ent.text for ent in doc.ents]
        if filtered:
            choices = list(self.__filter_choices(question, choices))
        return choices

    def __remove_trailing_broken_sentence(self, question: str, choices: List[str] = ()) -> str:
        question = question.strip()
        if not self.__may_be_sentence_end(question):
            sentences = self.split_sentences(question)
            if len(sentences) > 1:
                last_sentence = sentences[-1]
                possible_question = question.rstrip()[:-len(last_sentence.rstrip())].rstrip()
                if (not choices) or choices[-1] in possible_question:
                    question = possible_question
        return question

    def split_sentences(self, question) -> List[str]:
        # TODO: cache?
        return [sentence.text for sentence in self.__nlp(question).sents]

    def __filter_choices(self, question, choices):
        skipped_sentences = defaultdict(list)
        sentences = self.split_sentences(question)
        for i, choice in enumerate(choices):
            for j, sentence in enumerate(sentences):
                if choice in sentence:
                    if i < 2 or j < 2 or '?' in sentence:
                        yield choice
                    else:
                        skipped_sentences[j].append(choice)
                    break
        for j, choices in skipped_sentences.items():
            if len(choices) >= 2:
                yield from choices

    def __may_be_sentence_end(self, text, pos=None):
        if pos is None:
            pos = len(text) - 1
        return (text[pos] in SENTENCE_ENDERS) or (
                pos and text[pos] in POSSIBLE_SENTENCE_ENDERS and text[pos-1] in SENTENCE_ENDERS)


