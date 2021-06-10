# Reads given game from ballchasing and provides xG values

import pickle
import carball
import requests
import os
import pandas as pd

from analyzer import RocketLeagueAnalyzer

BASE = "https://ballchasing.com/api"

class RocketLeagueGame:

    def __init__(self, token, game_id):
        self.token = token
        self.header = {'Authorization': self.token}
        self.game_id = game_id
        self.replay = ""
        self.get_game()
        self.process_game()
        self.get_xg_values()

    def get_game(self): # maybe not as a file?
        self.file_name = replay_file_name = f"temp/{self.game_id}.replay"
        if os.path.exists(replay_file_name):
            return
        r = requests.get(BASE + f"/replays/{self.game_id}/file", headers=self.header)
        if r.status_code == 200:
            # self.replay = r.content
            with open(replay_file_name, "wb") as f:
                f.write(r.content)

    def process_game(self):
        r = carball.analyze_replay_file(self.file_name)
        tracking_data = r.get_data_frame()
        json_data = r.get_json_data()
        hit_frames = json_data['gameStats']['hits']
        self.players = players = {i['id']['id']: i for i in json_data['players']}
        player_names = [i['name'] for i in players.values()]

        model_shots = []
        for hf in hit_frames:
            if hf.get('shot', False):
                frame_number = hf['frameNumber']
                shot_taker_id = hf['playerId']['id']
                shot_taker_name = players[hf['playerId']['id']]['name']
                goal = hf.get('goal', False)
                tracking_frame = tracking_data.loc[frame_number]
                is_overtime = tracking_frame['game'].to_dict().get('is_overtime')
                game_time = 300-tracking_frame['game', 'seconds_remaining'] if not is_overtime else 300+tracking_frame['game', 'seconds_remaining']

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

        self.game_df = pd.DataFrame(model_shots)

    def get_xg_values(self):
        
        with open("../data/xg/xg.model", "rb") as f:
            reg = pickle.load(f)
        with open("../data/xg/xg.scaler", "rb") as f:
            sc = pickle.load(f)

        gdf = self.game_df.reset_index()
        col_list = ['index'] + [col for col in gdf.columns if ("_pos_" in col or "_vel_" in col or "_rot_" in col) and "team_mate" not in col and "ball" not in col]
        gv = gdf[col_list].copy().values[:,1:]

        xg = reg.predict_proba(sc.transform(gv))[:,1]
        self.game_df['xg'] = xg
        print(self.game_df)
        print(self.game_df.groupby('shot_taker_name')['xg'].sum())

        e = self.game_df[['shot_taker_name', 'is_orange', 'time', 'xg', 'goal']].copy()
        e.to_csv(f"../data/game_shots/{self.game_id}.csv")

if __name__ == "__main__":
    from dotenv import dotenv_values
    config = dotenv_values("../.env")
    token = config.get('TOKEN', os.environ.get('TOKEN', None))
    rg = RocketLeagueGame(token=token, game_id="b25d739e-c706-4a09-bd87-ea0951d4a285")
    # print('x')
