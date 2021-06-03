import requests
import functools
import warnings
import time
import os

BALLCHASING = "https://ballchasing.com/api"

def require_token(func):
    """Make sure user is logged in before proceeding"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.token is None:
            warnings.warn("This function needs a ballchasing token", RuntimeWarning)
            return None
        self.header = {'Authorization': self.token}
        return func(self, *args, **kwargs)
    return wrapper


class ReplayManager:

    def __init__(self, token=None):
        # Ballchasing token
        self.token = token
        self.replay_list = None
        self.header = dict()

    @require_token
    def get_remote_replay_list(self, player1=None, player2=None):

        player_text=""
        if player1:
            player_text += f"player-name={player1}&"
        if player2:
            player_text += f"player-name={player2}&"

        r = requests.get(BALLCHASING + "/replays?" + player_text, headers=self.header)
        if r.status_code == 200:
            self.replay_list = r.json()

    def fetch_replay_list(self):
        if self.replay_list is None:
            warnings.warn("Replay list is empty", RuntimeWarning)
            return None

        count = self.replay_list['count']
        print(f"Total number of games: {count}")
        game_list = self.replay_list['list']
        for game in game_list:
            file_name = rf"../data/replay/{game['id']}.replay"
            if os.path.exists(file_name):
                print(f"Game {game['id']} exists, skipping...")
                continue
            r = requests.get(BALLCHASING + f"/replays/{game['id']}/file", headers=self.header)
            if r.status_code == 200:
                with open(file_name, "wb") as f:
                    f.write(r.content)

            time.sleep(0.5)        

if __name__ == '__main__':
    from dotenv import dotenv_values
    config = dotenv_values("../.env")
    print(config)
    r = ReplayManager(token=config['TOKEN'])
    r.get_remote_replay_list("enpitsu", "games5425898691")
    r.fetch_replay_list()

