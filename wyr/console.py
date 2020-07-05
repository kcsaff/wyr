from colorama import Fore, Style
from contextlib import contextmanager
import sys
import time


clock = time.perf_counter


class Console(object):
    """
    Wrapper for a print statement to keep track of verbosity.
    """
    def __init__(self, print=print, warn=None):
        self.__print = print
        if warn is None:
            warn = self.__default_warn
        self.__warn = warn

    # Statuses, should write to stderr
    def okay(self, *args, **kwargs):
        self.__color_warn(Fore.GREEN, *args, **kwargs)

    def info(self, *args, **kwargs):
        self.__color_warn(Fore.YELLOW, *args, **kwargs)

    def warn(self, *args, **kwargs):
        self.__color_warn(Fore.RED, *args, **kwargs)

    @contextmanager
    def timed(self, start_text=None, stop_text=None):
        started = clock()
        if start_text:
            self.__color_warn(Fore.CYAN, start_text)

        yield

        elapsed = clock() - started
        if stop_text:
            self.__color_warn(Fore.CYAN, stop_text.format(elapsed))

    # Output, should write to print
    def print(self, *args, **kwargs):
        if self and self.__print:
            self.__print(*args, **kwargs)

    # Internal
    def __color_warn(self, color, *args, **kwargs):
        self.__warn(*self.__add_color(color, *args), **kwargs)

    def __default_warn(self, *args, **kwargs):
        self.__print(*args, file=sys.stderr, **kwargs)

    @staticmethod
    def __add_color(color, *args):
        if len(args) == 1:
            return [f'{color}{args[0]}{Style.RESET_ALL}']
        elif len(args) > 1:
            return [f'{color}{args[0]}', *args[1:-1], f'{args[-1]}{Style.RESET_ALL}']
        else:
            return []
