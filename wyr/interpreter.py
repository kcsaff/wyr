from wyr.constants import OUTER_CHOICE, INNER_CHOICE, DEFAULT_MODEL_PATH
import spacy


class ChoiceInterpreter(object):
    """
    Attempt to interpret choices out of a string starting with "Would you rather".
    """
    def __init__(self, model_path=DEFAULT_MODEL_PATH):
        self.__model_path = model_path
        self.__models = {}
        self.__loaded_nlp = None

    def massage_question(self, question):
        question = self.__remove_trailing_broken_sentence(question)
        choices = self.__find_best_choices(question)
        if len(choices) == 0:
            choices = ['yes', 'no']
        elif len(choices) == 1:
            choices = [choices[0], 'no']
        elif len(choices) > 4:
            choices = choices[:4]
        return question.strip() + ''.join(f'\n* {choice}' for choice in choices)

    def __find_best_choices(self, question):
        outer_choices = self.__find_model_choices(question, OUTER_CHOICE)
        inner_choices = self.__find_model_choices(question, INNER_CHOICE)
        if len(outer_choices) != len(inner_choices):
            return outer_choices
        for inner, outer in zip(inner_choices, outer_choices):
            if inner not in outer:
                return outer_choices
        return inner_choices

    def __find_model_choices(self, question, label):
        doc = self.__get_model(label)(question)
        return [ent.text for ent in doc.ents]

    def __remove_trailing_broken_sentence(self, question):
        doc = self.__nlp(question)
        sentences = list(doc.sents)
        if len(sentences) > 1:
            last_sentence = sentences[-1].text
            if last_sentence.rstrip()[-1] not in '!?.':
                question = question[:-len(last_sentence)]
        return question.strip()

    def __get_model(self, label):
        if label not in self.__models:
            self.__models[label] = spacy.load(f'{self.__model_path}/{label}')
        return self.__models[label]

    @property
    def __nlp(self):
        if self.__loaded_nlp is None:
            self.__loaded_nlp = spacy.load('en_core_web_sm')
        return self.__loaded_nlp

