from wyr.constants import DEFAULT_TRAINING_PATH, QUESTION_SEPARATOR
from typing import Dict, Generator, List, Tuple
from functools import cached_property, lru_cache


class TrainingData(object):
    """
    Reads training data that can be read by spacy from the given filename.  The data format should be:

     * Different Would You Rather questions separated by `QUESTION_SEPARATOR`, typically a series of dashes.
     * Two levels of brackets indicating choices. The outer brackets represent the easiest to find choices
       at the basic level, whereas the inner brackets indicate the logical difference between the options,
       such as a human might answer.

    :param filename: Filename to read
    :return: The structured training data readable by spacy NEP models
    """
    def __init__(self, filename: str = DEFAULT_TRAINING_PATH):
        self.__filename = filename

    @lru_cache
    def __new__(cls, filename: str = DEFAULT_TRAINING_PATH):
        result = object.__new__(cls)
        cls.__init__(result, filename)
        return result

    @cached_property
    def raw_data(self) -> List[str]:
        with open(self.__filename, 'r') as f:
            return list(self.__split_questions(f))

    @lru_cache
    def prepare_data(self, level: int, label: str) -> List[Tuple[str, Dict[str, List[Tuple[int, int, str]]]]]:
        return [choices
                for choices in [self.__prepare_markup(question, level, label) for question in self.raw_data]
                if choices]

    @cached_property
    def questions(self) -> List[str]:
        return [question.replace('[', '').replace(']', '').strip() for question in self.raw_data]

    @staticmethod
    def __prepare_markup(question: str, level: int, label: str):
        """
        Find choices in each question, emitting in a format suitable for spacy.
        """

        chars = []
        entities = []
        beginnings = []
        for c in question.strip():
            if c == '[':
                beginnings.append(len(chars))
            elif c == ']':
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
