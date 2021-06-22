"Utility functions"

from dotenv import dotenv_values
import os
import requests
import carball
import pandas as pd

def download_game(game_id, output_file):
    config = dotenv_values("../../.env")
    token = config.get('TOKEN', os.environ.get('TOKEN', None))
    header = {'Authorization': token}
    base = "https://ballchasing.com/api"
    r = requests.get(base + f"/replays/{game_id}/file", headers=header)
    if r.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(r.content)


def generate_aux_files(replay_file, json_file, csv_file):
    analysis = carball.analyze_replay_file(replay_file)
    with open(json_file, "w") as f:
        analysis.write_json_out_to_file(f)
    df = analysis.get_data_frame()
    with open(csv_file, "w") as f:
        df.to_csv(f)

def get_shots_from_aux(tracking_data, json_data, shots_file):
    hit_frames = json_data['gameStats']['hits']
    players = {i['id']['id']: i for i in json_data['players']}
    player_names = [i['name'] for i in players.values()]

    shots = []
    model_shots = []
    for hf in hit_frames:
        if True: # hf.get('shot', False):
            frame_number = hf['frameNumber']
            shot_taker_id = hf['playerId']['id']
            shot_taker_name = players[hf['playerId']['id']]['name']
            is_shot = hf.get('shot', False)
            goal = hf.get('goal', False)
            tracking_frame = tracking_data.loc[frame_number]
            print(tracking_frame)
            is_overtime = tracking_frame['game'].to_dict().get('is_overtime')
            game_time = 300-tracking_frame['game', 'seconds_remaining'] if not is_overtime else 300+tracking_frame['game', 'seconds_remaining']
            single_shot = {
                'frame': frame_number,
                'time': game_time,
                'players': {
                    p: tracking_frame[p].to_dict() for p in player_names
                },
                'ball': tracking_frame['ball'].to_dict(),
                'goal': goal,
                'coll_distance': hf.get('distance'),
                'distanceToGoal': hf.get('distanceToGoal'),
                'shot_taker_id': shot_taker_id,
                'shot_taker_name': shot_taker_name,
            }
            shots.append(single_shot)
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
    
    shots_df = pd.DataFrame(model_shots)
    shots_df.to_csv(shots_file)
    return shots_df

def get_shots_from_replay(replay_file, shots_file):
    analysis = carball.analyze_replay_file(replay_file)
    tracking_data = analysis.get_data_frame()
    json_data = analysis.get_json_data()
    model_shots = get_shots_from_aux(tracking_data, json_data, shots_file)
    return model_shots
