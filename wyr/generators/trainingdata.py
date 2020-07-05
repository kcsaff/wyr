from wyr.constants import QUESTION_SEPARATOR
import wyr.data
from wyr.console import Console
from typing import Dict, Generator, List, Tuple
from functools import cached_property, lru_cache
from importlib import resources


class TrainingData(object):
    DELIMITERS = '{}'
    BEGIN = 0
    END = 1

    """
    Reads training data that can be read by spacy from the given filename.  The data format should be:

     * Different Would You Rather questions separated by `QUESTION_SEPARATOR`, typically a series of dashes.
     * Two levels of brackets indicating choices. The outer brackets represent the easiest to find choices
       at the basic level, whereas the inner brackets indicate the logical difference between the options,
       such as a human might answer.

    :param filename: Filename to read
    :return: The structured training data readable by spacy NEP models
    """
    def __init__(self, filename: str = None, console=None):
        self.__filename = filename
        if console is None:
            console = Console()
        self.__console = console

    @lru_cache
    def __new__(cls, filename: str = None):
        result = object.__new__(cls)
        cls.__init__(result, filename)
        return result

    @cached_property
    def raw_data(self) -> List[str]:
        """Return list of uninterpreted questions (split but still with bracketed choices)."""
        with self.__open_data() as f:
            questions = list(self.__split_questions(f))
            self.__console.okay(f'Loaded {len(questions)} questions from the training data')
            return questions

    def __open_data(self):
        if self.__filename is None:
            return resources.open_text(wyr.data, 'training')
        else:
            return open(self.__filename, 'r')

    @lru_cache
    def prepare_data(self, level: int, label: str) -> List[Tuple[str, Dict[str, List[Tuple[int, int, str]]]]]:
        return [choices
                for choices in [self.__prepare_markup(question, level, label) for question in self.raw_data]
                if choices]

    @cached_property
    def questions(self) -> List[str]:
        return [self.strip_question(question) for question in self.raw_data]

    @classmethod
    def strip_question(cls, question):
        for delimiter in cls.DELIMITERS:
            question = question.replace(delimiter, '')
        return question.strip()

    @classmethod
    def __prepare_markup(cls, question: str, level: int, label: str):
        """
        Find choices in each question, emitting in a format suitable for spacy.
        """

        chars = []
        entities = []
        beginnings = []
        for c in question.strip():
            action = cls.DELIMITERS.find(c)
            if action == cls.BEGIN:
                beginnings.append(len(chars))
            elif action == cls.END:
                if 0 < len(beginnings):
                    if len(beginnings) == level:
                        entities.append((beginnings[-1], len(chars), label))
                    beginnings.pop()
            else:
                chars.append(c)

        if entities:
            return ''.join(chars), {'entities': entities}
        else:
            return None

    @staticmethod
    def __split_questions(lines) -> Generator[str, None, None]:
        """Split questions"""
        accumulated_lines = []
        for line in lines:
            if line.strip() == QUESTION_SEPARATOR:
                question = '\n'.join(accumulated_lines).strip()
                if question:
                    yield question
                accumulated_lines = []
            else:
                accumulated_lines.append(line.strip())
