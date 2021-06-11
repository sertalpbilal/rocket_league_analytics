# This class collects random games from ballchasing in order to prepare input for xG model
import requests
import functools
import warnings
import time
import os
import pathlib

BALLCHASING = "https://ballchasing.com/api"

def require_token(func):
    """Make sure user has a token"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.token is None:
            warnings.warn("This function needs a ballchasing token", RuntimeWarning)
            return None
        self.header = {'Authorization': self.token}
        return func(self, *args, **kwargs)
    return wrapper


class GameCollector:

    def __init__(self, token=None, tracking=True, folder='replay'):
        # Ballchasing token
        self.token = token
        self.replay_list = []
        self.header = dict()
        self.tracking = tracking
        self.folder = folder
        self.pwd = pathlib.Path()

    @require_token
    def get_remote_replay_list(self, player1=None, player2=None, min_rank=None, count=1, pages=1):

        params = f"count={count}&playlist=ranked-doubles&"
        if player1:
            params += f"player-name={player1}&"
        if player2:
            params += f"player-name={player2}&"
        if min_rank:
            params += f"min-rank={min_rank}&"

        url = BALLCHASING + "/replays?" + params
        for page in range(pages):
            print(f"Getting page {page+1} of {pages}")
            r = requests.get(url, headers=self.header)
            response = r.json()
            if r.status_code == 200:
                self.replay_list += response['list']
            if 'next' in response:
                url = response['next']
            else:
                break

    def fetch_replay_list(self):
        if len(self.replay_list) == 0:
            warnings.warn("Replay list is empty", RuntimeWarning)
            return None

        print(f"Total number of games to fetch: {len(self.replay_list)}")
        folder = self.folder
        game_list = self.replay_list
        stop = False
        for game in game_list:
            try:
                if stop:
                    continue
                replay_file_name = (self.pwd / rf"../../data/{folder}/{game['id']}.replay").resolve()
                
                if not os.path.exists(replay_file_name):
                    print(f"Fetching {game['id']}")
                    r = requests.get(BALLCHASING + f"/replays/{game['id']}/file", headers=self.header)
                    if r.status_code == 200:
                        with open(replay_file_name, "wb") as f:
                            f.write(r.content)
                    else:
                        print(f'Error with HTTP code: {r.status_code}')
                        if r.status_code == 429:
                            stop = True
                            print("Terminating downloads, hit the API limit")
                            break
                    time.sleep(5)
                else:
                    print(f"Replay file {game['id']} exists!")

            except Exception as e:
                print(f"Exception occured, skipping {game['id']}", e)


def read_env_file():
    from dotenv import dotenv_values
    config = dotenv_values("../../.env")
    return config


def get_model_replays(count=1, pages=1):
    config = read_env_file()
    r = GameCollector(token=config.get('TOKEN', os.environ.get('TOKEN', None)), folder='model')
    r.get_remote_replay_list(min_rank='platinum-3', count=count, pages=pages)
    r.fetch_replay_list()


def get_my_replays():
    config = read_env_file()
    r = GameCollector(token=config.get('TOKEN', os.environ.get('TOKEN', None)))
    r.get_remote_replay_list("enpitsu", "games5425898691")
    r.fetch_replay_list()
