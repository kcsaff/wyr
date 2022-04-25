from uuid import uuid4

import requests


class MastodonPoster:
    MAX_CHOICE_LENGTH = 50
    def __init__(self, token_file, api='https://botsin.space'):
        self.__api = api.strip().rstrip('/')
        with open(token_file, 'r') as f:
            self.__token = f.read().strip()

    def post(self, toot, choices=None, parse_choices=True):
        if parse_choices and not choices:
            toot, choices = self.__parse_choices(toot)
        j = {
            'status': str(toot),
            'visibility': 'public',
        }
        if choices:
            j['poll'] = {
                'options': [str(choice)[:self.MAX_CHOICE_LENGTH] for choice in choices],
                'expires_in': 24 * 60 * 60,
            }
        resp = requests.post(
            f'{self.__api}/api/v1/statuses',
            json=j,
            headers={
                'Authorization': f'Bearer {self.__token}',
                'Idempotency-Key': str(uuid4()),
            },
        )

        print(resp.json())

    def __parse_choices(self, status: str):
        lines = status.strip().splitlines(keepends=True)
        choices = list()
        for line in reversed(lines):
            if line.lstrip().startswith('* '):
                choices.append(line.split(maxsplit=1)[-1].strip())
            else:
                break
        if choices:
            status = ''.join(lines[:(len(lines)-len(choices))])
            return status, reversed(choices)
        else:
            return status, []
