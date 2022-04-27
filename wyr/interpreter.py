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

        if len(outer_choices) < 2:
            simple_choices = self.__find_simple_choices(question)
            if len(simple_choices) >= 2:
                outer_choices = simple_choices

        # This is just a weird heuristic
        if 2 <= len(outer_choices) != len(inner_choices):
            return outer_choices

        choices = []
        for inner, outer in zip(inner_choices, outer_choices):
            if inner in outer:
                choices.append(inner)
            else:
                choices.append(outer)
        choices.extend(outer_choices[len(choices):])
        return choices

    def __find_model_choices(self, question: str, level: int, *, filtered: bool = False) -> List[str]:
        doc = self.__models.get_or_train(level)(question)
        choices = [ent.text for ent in doc.ents]
        if filtered:
            choices = list(self.__filter_choices(question, choices))
        return choices

    def __find_simple_choices(self, question):
        first_sentence = self.split_sentences(question)[0]
        if not first_sentence.startswith('Would you rather'):
            return []
        if ' or ' in first_sentence:
            choices = list()
            start = len('Would you rather ')
            while True:
                i = first_sentence.find(' or ', start)
                if i < 0:
                    choices.append(first_sentence[start:].strip().strip('.,?"\':!()[]{};').strip())
                    break
                choices.append(first_sentence[start:i].strip().strip(',:"\''))
                start = i + 4
            return choices
        return []

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
        choices = list(choices)
        # Combine choices if adjacent ones are in question
        last_choice = ''
        combined_choices = list()
        for i, choice in enumerate(choices):
            if last_choice:
                if last_choice + choice in question:
                    last_choice = last_choice + choice
                else:
                    combined_choices.append(last_choice)
                    last_choice = choice
        if last_choice:
            combined_choices.append(last_choice)

        for i, choice in enumerate(combined_choices):
            for j, sentence in enumerate(sentences):
                if choice in sentence:
                    if i < 2 or j < 2 or '?' in sentence:
                        yield choice
                    else:
                        skipped_sentences[j].append(choice)
                    break
        for j, skipped_choices in skipped_sentences.items():
            if len(skipped_choices) >= 2:
                yield from skipped_choices

    def __may_be_sentence_end(self, text, pos=None):
        if pos is None:
            pos = len(text) - 1
        return (text[pos] in SENTENCE_ENDERS) or (
                pos and text[pos] in POSSIBLE_SENTENCE_ENDERS and text[pos-1] in SENTENCE_ENDERS)


