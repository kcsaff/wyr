import random
import html
from functools import cached_property
from wyr.console import Console


class TweetGrabber(object):
    def __init__(self, keys, console=None):
        self.__keys = keys
        if console is None:
            console = Console()
        self.__console = console

    def random_tweet(self, query):
        results = self.client.api.search(query, tweet_mode='extended')
        if results:
            self.__console.okay(f'Found {len(results)} tweets matching {query}')
        rc = random.choice(results)
        if hasattr(rc, 'retweeted_status'):
            return html.unescape(rc.retweeted_status.full_text)
        else:
            return html.unescape(rc.full_text)

    @cached_property
    def client(self):
        from tweebot import TwitterClient
        return TwitterClient(self.__keys)


