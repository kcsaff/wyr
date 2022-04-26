from uuid import uuid4

import requests

WOULD_YOU_RATHER_TEXT = 'Would you rather '
WOULD_YOU_RATHER_TAG = '#WouldYouRather '


class MastodonPoster:
    MAX_CHOICE_LENGTH = 50
    def __init__(self, token_file, interpreter, api='https://botsin.space'):
        self.__api = api.strip().rstrip('/')
        self.__interpreter = interpreter
        with open(token_file, 'r') as f:
            self.__token = f.read().strip()

    def post(self, toot):
        toot, choices = self.__interpreter.split_question_choices(toot)
        ret_values = []
        j = {
            'status': self.__add_tag(toot),
            'visibility': 'public',
        }
        sentences = self.__interpreter.split_sentences(toot)
        if len(sentences) >= 2:
            j['spoiler_text'] = sentences[0].strip()
            ret_values.append(j['spoiler_text'])
            ret_values.append('-----')
            j['status'] = toot.lstrip()[len(sentences[0].strip()):].strip() + '\n\n#WouldYouRather'
        ret_values.append(j['status'])

        if choices:
            j['poll'] = {
                'options': [str(choice)[:self.MAX_CHOICE_LENGTH] for choice in choices],
                'expires_in': 24 * 60 * 60,
            }
            ret_values.extend(f'* {choice}' for choice in j['poll']['options'])
        resp = requests.post(
            f'{self.__api}/api/v1/statuses',
            json=j,
            headers={
                'Authorization': f'Bearer {self.__token}',
                'Idempotency-Key': str(uuid4()),
            },
        )

        print(resp.json())
        return '\n'.join(ret_values)

    def __add_tag(self, toot: str):
        if toot.startswith(WOULD_YOU_RATHER_TEXT):
            return WOULD_YOU_RATHER_TAG + toot[len(WOULD_YOU_RATHER_TEXT):]
        else:
            return toot
