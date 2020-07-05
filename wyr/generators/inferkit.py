import requests
import time
from wyr.console import Console


class BearerAuth(requests.auth.AuthBase):
    """Implement simple bearer auth for `requests`"""
    def __init__(self, token: str):
        """
        Create the Auth object, with the given token.
        :param token: Bearer token to use
        """
        self.token = token

    @classmethod
    def load(cls, token_filename):
        """
        Create the Auth object, loading the token from the file.
        :param token_filename: Filename containing the token to load.
        """
        with open(token_filename) as f:
            return cls(f.read().strip())

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r


class InferKitClient(object):
    URL = 'https://api.inferkit.com/v1/models/standard/generate'

    def __init__(self, token_filename, console=None):
        self.auth = BearerAuth.load(token_filename)
        if console is None:
            console = Console()
        self.__console = console

    def generate(self, prompt, length=280, beginning=True, max_retries=3):
        for _ in range(max_retries):
            response = requests.post(
                self.URL,
                auth=self.auth,
                json={'prompt': {'text': prompt}, 'length': length, 'startFromBeginning': beginning})

            if response.ok:
                break
            elif response.status_code == 502:
                time.sleep(30)
                continue
            else:
                break

        try:
            prompt_continuation = response.json()['data']['text']
        except:
            self.__console.warn(response)
            self.__console.warn(response.text)
        else:
            return prompt + prompt_continuation
