# %%
import pandas as pd
import carball
import glob
import os

# %%
all_replay_files = glob.glob("/data/replay/*.replay")
dfs = []
for f in all_replay_files:
    csv_name = f.replace("replay", "xg", 1).replace("replay", "csv", 1)
    if os.path.exists(csv_name):
        print(f"CSV exists for {f}")
        df = pd.read_csv(csv_name)
        dfs.append(df)
        continue
    print(f"Reading {f}")
    r = carball.analyze_replay_file(f)
    tracking_data = r.get_data_frame()
    json_data = r.get_json_data()
    hit_frames = json_data['gameStats']['hits']
    players = {i['id']['id']: i for i in json_data['players']}
    player_names = [i['name'] for i in players.values()]

    shots = []
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

    current_df = pd.DataFrame(model_shots)
    current_df.to_csv(csv_name)
    dfs.append(current_df)

# %%
all_df = pd.concat(dfs)
print(all_df.head())
all_df.reset_index(inplace=True, drop=True)
all_df.to_csv("../data/xg/combined.csv")
