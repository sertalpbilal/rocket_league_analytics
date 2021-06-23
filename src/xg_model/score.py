# This class populates hits data and exports final xG model
import pandas as pd
import carball
from concurrent.futures import ProcessPoolExecutor
import pathlib
import glob
import os
import pickle
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import json
from util import download_game, get_shots_from_replay, get_shots_from_aux


class RocketLeagueXGScorer:

    def __init__(self, folder='model'):
        self.folder = (pathlib.Path() / f"../../data/{folder}").resolve()
        self.parent = (pathlib.Path() / "../../data").resolve()
        self.model = None
        self.scaler = None
        self._read_model()
    
    def _read_model(self):
        with open(self.folder / "xg.model", "rb") as f:
            self.model = pickle.load(f)
        with open(self.folder / "xg.scaler", "rb") as f:
            self.scaler = pickle.load(f)

    def score_game(self, game_id):

        print(f"Scoring {game_id}")

        model = self.model
        scaler = self.scaler

        shots_file = self.parent / f"shots/{game_id}.csv"
        if os.path.exists(shots_file):
            shots = pd.read_csv(shots_file)
        else:
            print("Game shots are not available under game_shots folder")
            shots = self.read_game_from_file(game_id)
        
        gdf = shots.copy().reset_index()
        col_list = ['index'] + [col for col in gdf.columns if ("_pos_" in col or "_vel_" in col or "_rot_" in col) and "team_mate" not in col and "ball" not in col]
        gv = gdf[col_list].copy().values[:,1:]

        try:
            xg = model.predict_proba(scaler.transform(gv))[:,1]
        except Exception as e:
            print(e)
            return
        shots['xg'] = xg
        # print(shots)
        print(shots.groupby('shot_taker_name')['xg'].sum())

        e = shots[['shot_taker_name', 'is_orange', 'time', 'xg', 'shot', 'goal']].copy()
        e.to_csv(self.parent / f"xg_out/{game_id}.csv")

        return e

    def read_game_from_file(self, game_id):
        print(f"Populating shots data for {game_id}")
        replay_file = self.parent / f"replay/{game_id}.replay"
        json_file = self.parent / f"json/{game_id}.json"
        csv_file = self.parent / f"dataframe/{game_id}.csv"
        if False and (os.path.exists(replay_file) and os.path.exists(json_file) and os.path.exists(csv_file)):
            print(f"Using existing data for {game_id}")
            with open(json_file) as f:
                json_data = json.loads(f.read())
            csv_data = pd.read_csv(csv_file)
            print(csv_data.columns)
            shots_file = self.parent / f"shots/{game_id}.csv"
            return get_shots_from_aux(csv_data, json_data, shots_file)
        else:
            print(f"Download game {game_id}")
            replay_file = self.parent / f"replay/{game_id}.replay"
            shots_file = self.parent / f"shots/{game_id}.csv"
            download_game(game_id=game_id, output_file=replay_file)
            shots = get_shots_from_replay(replay_file, shots_file)
            return shots


def generate_xg():
    r = RocketLeagueXGScorer('model')

def convert_all():
    import glob
    games = glob.glob("../../data/replay/*.replay")
    game_ids = [i.split('/')[-1].split('.')[0] for i in games]
    s = RocketLeagueXGScorer('model')
    for g in game_ids:
        s.score_game(g)

if __name__ == "__main__":
    s = RocketLeagueXGScorer('model')
    s.score_game("1edab053-ab1a-4729-ac01-a65f34ac8ba0")
    