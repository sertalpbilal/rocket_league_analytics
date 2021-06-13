import requests
import functools
import warnings
import time
import os
import subprocess
import pathlib
import pickle
import platform

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


class ReplayManager:

    def __init__(self, token=None, tracking=True):
        # Ballchasing token
        self.token = token
        self.replay_list = None
        self.header = dict()
        self.tracking = tracking

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
            try:
                replay_file_name = rf"../data/replay/{game['id']}.replay"
                json_tracking_file_name = rf"../data/json_detailed/{game['id']}.tracking.json"
                
                if not os.path.exists(replay_file_name):
                    print(f"Fetching {game['id']}")
                    r = requests.get(BALLCHASING + f"/replays/{game['id']}/file", headers=self.header)
                    if r.status_code == 200:
                        with open(replay_file_name, "wb") as f:
                            f.write(r.content)
                    time.sleep(0.5)
                else:
                    print(f"Replay file {game['id']} exists!")

                # if not os.path.exists(json_tracking_file_name):
                #     parent = pathlib.Path() / ".."

                #     if platform.system() == 'Windows':
                #         subprocess.Popen((f"{parent / 'bin/rattletrap.exe'} -i {replay_file_name} -o {json_tracking_file_name}").split())
                #     elif platform.system() == 'Linux':
                #         subprocess.Popen((f"{parent / 'bin/rattletrap'} -i {replay_file_name} -o {json_tracking_file_name}").split())
                # else:
                #     print(f"JSON file exists {json_tracking_file_name}")


            except Exception as e:
                print(f"Exception occured, skipping {game['id']}", e)

if __name__ == '__main__':
    from dotenv import dotenv_values
    config = dotenv_values("../.env")
    print(config)
    r = ReplayManager(token=config.get('TOKEN', os.environ.get('TOKEN', None)))
    r.get_remote_replay_list("enpitsu", "games5425898691")
    r.fetch_replay_list()
