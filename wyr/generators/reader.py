from wyr.constants import QUESTION_SEPARATOR


class TrainingDataReader(object):
    """
    Reads training data that can be read by spacy from the given filename.  The data format should be:

     * Different Would You Rather questions separated by `QUESTION_SEPARATOR`, typically a series of dashes.
     * Two levels of brackets indicating choices. The outer brackets represent the easiest to find choices
       at the basic level, whereas the inner brackets indicate the logical difference between the options,
       such as a human might answer.

    :param filename: Filename to read
    :param level: level of bracketing to record
    :param label: label to apply to selection
    :return: The structured training data readable by spacy NEP models
    """
    def __init__(self, filename: str):
        self.__filename = filename
        self.__raw_data = None
        self.__questions = None

    @property
    def raw_data(self):
        if self.__raw_data is None:
            with open(self.__filename, 'r') as f:
                self.__raw_data = list(self.__split_questions(f))
        return self.__raw_data

    def prepare_data(self, level, label):
        return [choices
                for choices in [self.__prepare_markup(question, level, label) for question in self.raw_data]
                if choices]

    @property
    def questions(self):
        if self.__questions is None:
            self.__questions = [question.replace('[', '').replace(']', '').strip()
                                for question in self.raw_data]
        return self.__questions

    @staticmethod
    def __prepare_markup(question, level, label):
        """Find choices in each question"""
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
    def __split_questions(lines):
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
