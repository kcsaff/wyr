import requests


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token_filename):
        with open(token_filename) as f:
            self.token = f.read().strip()

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r


class InferKitClient(object):
    URL = 'https://api.inferkit.com/v1/models/standard/generate'

    def __init__(self, token_filename):
        self.auth = BearerAuth(token_filename)

    def generate(self, prompt, length=280, beginning=True):
        response = requests.post(
            self.URL,
            auth=self.auth,
            json={'prompt': {'text': prompt}, 'length': length, 'startFromBeginning': beginning})
        try:
            prompt_continuation = response.json()['data']['text']
        except:
            print(response)
            print(response.text)
        else:
            return prompt + prompt_continuation
