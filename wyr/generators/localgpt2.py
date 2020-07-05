from pathlib import Path
from functools import cached_property
from wyr.constants import DEFAULT_GPT2_MODEL, DEFAULT_MODEL_PATH
from wyr.console import Console
from collections import defaultdict


class LocalGpt2(object):
    def __init__(self,
                 model_dir: str = DEFAULT_MODEL_PATH,
                 model_version: str = DEFAULT_GPT2_MODEL,
                 console: Console = None):
        self.__model_dir = model_dir
        self.__model_version = model_version

        if console is None:
            console = Console()
        self.__console = console
        self.__cache = defaultdict(list)

    @cached_property
    def ai(self):
        with self.__console.timed(
                f'Loading model {self.__model_version}',
                'Loaded model in {0:.3f}s'):
            from aitextgen import aitextgen
            return aitextgen(
                model=self.__model_version,
                cache_dir=self.model_path,
            )

    @cached_property
    def model_path(self):
        return Path(self.__model_dir) / self.__model_version

    def generate(self, prompt: str = 'Would you rather', temperature: float = 1.0, count=1):
        ai = self.ai
        cache = self.__cache[prompt, temperature]
        with self.__console.timed(
                f'Generating {count} text(s) based on "{prompt}"\nTemperature: {temperature}',
                'Generated text in {0:.3f}s'):
            cache += ai.generate(
                prompt=prompt,
                temperature=temperature,
                max_length=70,  # Maximum number of words to generate
                n=max(2, 2+3*count-len(cache)),  # Generate at least 2, up to some multiple of count
                return_as_list=True)
            # Find least "bad" questions (need an "or" and few quotes)
            scores = [q.count(' or ') - q.count('"') for q in cache]
            results = []
            for _ in range(count):
                index_max = max(range(len(scores)), key=scores.__getitem__)
                results.append(cache.pop(index_max))
                scores.pop(index_max)
            self.__cache[prompt, temperature] = cache
            return results
