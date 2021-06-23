# This class populates hits data and exports final xG model
import pandas as pd
import numpy as np
from math import floor
from concurrent.futures import ProcessPoolExecutor
import pathlib
import glob
import os
import pickle
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier
from sklearn.neural_network import MLPClassifier
from progress.bar import IncrementalBar
from wrapt_timeout_decorator import timeout

class RocketLeagueXG:

    def __init__(self, folder='model', swapping=True, oversample=False):
        self.folder = (pathlib.Path() / f"../../data/{folder}").resolve()
        self.swapping = swapping
        self.oversample = oversample
        self.df = None

    def prepare_data(self, collect=True):
        "Reads and prepares raw data for the model, this step might take a while"

        all_replay_files = glob.glob(f"{self.folder}/*.replay")
        parallel = False

        if parallel:
            with ProcessPoolExecutor(max_workers=16) as executor:
                dfs = list(executor.map(self.read_single_game, all_replay_files))
        else:
            dfs = []
            for f in IncrementalBar('Collecting games').iter(all_replay_files):
            # for f in all_replay_files:
                try:
                    game_data = self.read_single_game(f)
                    if collect:
                        dfs.append(game_data)
                except:
                    print("Game cannot be read properly by carball, deleting the replay")
                    os.unlink(f)

        if collect:
            print("Saving to file")
            all_df = pd.concat(dfs)
            print(all_df.head())
            all_df.reset_index(inplace=True, drop=True)
            all_df.to_csv(self.folder / "combined.csv")
            self.df = all_df

    @timeout(45)
    def read_single_game(self, f):
        import carball
        csv_name = f.replace(".replay", ".csv", 1)
        if os.path.exists(csv_name):
            print(f"CSV exists for {f}")
            df = pd.read_csv(csv_name)
            return df
        print(f"Reading {f}")
        r = carball.analyze_replay_file(f)
        print(f"Carball data is ready, processing {f}")
        tracking_data = r.get_data_frame()
        json_data = r.get_json_data()
        hit_frames = json_data['gameStats']['hits']
        players = {i['id']['id']: i for i in json_data['players']}
        player_names = [i['name'] for i in players.values()]

        # shots = []
        model_shots = []
        for hf in hit_frames:
            print(".", end="")
            if True: #hf.get('shot', False):
                frame_number = hf['frameNumber']
                shot_taker_id = hf['playerId']['id']
                shot_taker_name = players[hf['playerId']['id']]['name']
                is_shot = hf.get('shot', False)
                goal = hf.get('goal', False)
                tracking_frame = tracking_data.loc[frame_number]
                is_overtime = tracking_frame['game'].to_dict().get('is_overtime')
                game_time = 300-tracking_frame['game', 'seconds_remaining'] if not is_overtime else 300+tracking_frame['game', 'seconds_remaining']
                single_shot = {
                    'frame': frame_number,
                    'time': game_time,
                    'players': {
                        p: tracking_frame[p].to_dict() for p in player_names
                    },
                    'ball': tracking_frame['ball'].to_dict(),
                    'shot': is_shot,
                    'goal': goal,
                    'coll_distance': hf.get('distance'),
                    'distanceToGoal': hf.get('distanceToGoal'),
                    'shot_taker_id': shot_taker_id,
                    'shot_taker_name': shot_taker_name,
                }
                # shots.append(single_shot)
                shot_taker = tracking_frame[shot_taker_name]
                shot_taker_team_no = players[shot_taker_id]['isOrange']
                team_mate_name = None
                team_mate_id = None
                for p in json_data['players']:
                    if p['isOrange'] == shot_taker_team_no and p['id']['id'] != shot_taker_id:
                        team_mate_name = p['name']
                        team_mate_id = p['id']['id']
                        break
                # Only valid for 2v2s
                opposition_names = []
                opposition_ids = []
                for p in json_data['players']:
                    if p['isOrange'] != shot_taker_team_no:
                        opposition_names.append(p['name'])
                        opposition_ids.append(p['id']['id'])

                generic_shot = {
                    'frame': frame_number,
                    'time': game_time,
                    'goal': goal,
                    'shot': is_shot,
                    'is_orange': shot_taker_team_no,
                    'distanceToGoal': hf['distanceToGoal'],
                }
                # BALL
                generic_shot.update({
                    'ball_' + key: val for (key,val) in tracking_frame['ball'].to_dict().items()
                })
                # SHOT TAKER
                generic_shot.update({
                    'shot_taker_id': shot_taker_id,
                    'shot_taker_name': shot_taker_name,
                })
                generic_shot.update({
                    'shot_taker_' + key: val for (key,val) in tracking_frame[shot_taker_name].to_dict().items()
                })
                # TEAM MATE
                generic_shot.update({
                    'team_mate_id': team_mate_id,
                    'team_mate_name': team_mate_name
                })
                # OPPOSITION
                generic_shot.update({
                    'team_mate_' + key: val for (key,val) in tracking_frame[team_mate_name].to_dict().items()
                })
                for idx, val in enumerate(opposition_names):
                    generic_shot[f'opp_{idx+1}_name'] = val
                    generic_shot[f'opp_{idx+1}_id'] = opposition_ids[idx]
                    generic_shot.update({
                        f'opp_{idx+1}_{key}': val for (key,val) in tracking_frame[val].to_dict().items()
                    })

                # Orange/Blue fix
                if shot_taker_team_no == 1:
                    for key in generic_shot:
                        if key.endswith("_x") or key.endswith("_y"):
                            generic_shot[key] *= -1
                model_shots.append(generic_shot)

        print(f"Done {f}")

        current_df = pd.DataFrame(model_shots)
        current_df.to_csv(csv_name)
        return current_df

    def build_model(self):
        if self.df is None:
            data = pd.read_csv(self.folder / "combined.csv")
            data = data.rename(columns={'Unnamed: 0': 'idx'})
        else:
            data = self.df.reset_index().rename(columns={'index': 'idx'})

        print("Processing data")

        if self.swapping:
            print("Swapping")
            data_switch = data.copy()
            opp1_cols = [col for col in data_switch.columns if "opp_1_" in col]
            opp2_cols = [col for col in data_switch.columns if "opp_2_" in col]
            temp_cols = ['temp_' + i for i in opp1_cols]
            data_switch[temp_cols] = data_switch[opp1_cols]
            data_switch[opp1_cols] = data_switch[opp2_cols]
            data_switch[opp2_cols] = data_switch[temp_cols]
            data_switch.drop(columns=temp_cols, inplace=True)
            data = pd.concat([data, data_switch])
        print("Filtering data")
        col_list = ['idx'] + [col for col in data.columns if ("_pos_" in col or "_vel_" in col or "_rot_" in col) and "team_mate" not in col and "ball" not in col] + ['goal']  # OR COL=SHOT?
        data_filtered = data[col_list]
        data_filtered = data_filtered.dropna()
        X = data_filtered.iloc[:, :-1].values
        y = data_filtered.iloc[:, -1].astype(int).values
        print("Data is ready, splitting")
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0, test_size=0.2)
        
        if self.oversample:
            print("Oversampling goals")
            not_goal_cnt = len(X_train[y_train==0])
            goal_cnt = len(X_train[y_train==1])
            copy_cnt = floor(not_goal_cnt / goal_cnt) + 1
            copy_cnt = 1
            print("Copy count: ", copy_cnt)
            goals_filtered = X_train[y_train==1].copy()
            X_train = np.concatenate([X_train] + [goals_filtered for _ in range(copy_cnt)])
            y_train = np.concatenate([y_train] + [y_train[y_train==1] for _ in range(copy_cnt)])
        sc = StandardScaler()
        scaled_X_train = sc.fit_transform(X_train[:,1:])
        scaled_X_test = sc.transform(X_test[:,1:])
        print("Split is ready, training")
        reg = XGBClassifier()
        reg.fit(scaled_X_train, y_train)
        y_pred = reg.predict(scaled_X_test)
        print("Model is ready, measuring performance")
        print("Test", accuracy_score(y_pred, y_test), "Train", accuracy_score(reg.predict(scaled_X_train), y_train), "ROC AUC Score", roc_auc_score(y_test, y_pred))
        with open(self.folder / "xg.model", "wb") as f:
            pickle.dump(reg, f)
        with open(self.folder / "xg.scaler", "wb") as f:
            pickle.dump(sc, f)
        print("Ready!")


def generate_xg():
    r = RocketLeagueXG('model')
    # only prep
    # r.prepare_data(collect=False)
    r.prepare_data()
    r.build_model()

def generate_xg_cached():
    r = RocketLeagueXG('model')
    r.build_model()
