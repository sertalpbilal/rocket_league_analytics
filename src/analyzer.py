# Our own JSON parser
import json
import numpy as np

LIMITS = {
    "X": [-4100, 4100],
    "Y": [-5140, 5140],
    "Z": [0, 2050]
}

class RocketLeagueAnalyzer:

    def __init__(self, file):
        self.status = 'Idle'
        with open(file, 'r') as f:
            self.data = json.loads(f.read())
        self.player_names = dict()
        self.all_frames = []
        self.shots = []
        self.goals = []

        self._read_frames()
        self._find_player_names()
        self._find_ball_ids()
        self._find_ball_coords()
        self._find_shots()

    def _read_frames(self):
        self.all_frames = self.data['content']['body']['frames']

    def get_frames(self):
        return self.all_frames

    def _find_ball_ids(self):
        ball_dict = dict()
        ball_ids = []
        last_ball = None
        for index, frame in enumerate(self.all_frames):
            for entry in frame['replications']:
                c_actor = entry['actor_id']['value']
                if entry['value'].get('spawned', {}).get('class_name', '') == "TAGame.Ball_TA":
                    if last_ball != c_actor:
                        ball_ids.append(c_actor)
                    last_ball = c_actor
            ball_dict[index] = last_ball
        self.ball_dict = ball_dict
        self.ball_ids = ball_ids

    def get_ball_dict(self):
        return self.ball_dict
    
    def get_ball_ids(self):
        return self.ball_ids

    def _find_ball_coords(self):
        all_frames = self.all_frames
        ball_dict = self.ball_dict

        self.ball_positions = ball_positions = []
        cx,cy,cz=np.nan,np.nan,np.nan
        rx,ry,rz=np.nan,np.nan,np.nan
        vx,vy,vz=0,0,0
        ax,ay,az=np.nan,np.nan,np.nan
        for index, frame in enumerate(all_frames):
            for entry in frame['replications']:
                if entry['actor_id']['value'] != ball_dict[index]:
                    continue
                else:
                    # Initialization
                    ball_id = ball_dict[index]
                    if 'spawned' in entry['value']:
                        try:
                            loc = entry['value']['spawned']['initialization']['location']
                            cx,cy,cz = loc['x'],loc['y'],loc['z']
                        except:
                            pass
                    if 'updated' in entry['value']:
                        for val in entry['value']['updated']:
                            if val['name'] == "TAGame.RBActor_TA:ReplicatedRBState":
                                if 'rigid_body_state' in val['value']:
                                    loc = val['value']['rigid_body_state']['location']
                                    cx,cy,cz = (loc['x'])/100,(loc['y'])/100,(loc['z'])/100
            ball_positions.append({'frame': index, 'ball_id': ball_id, 'cx': cx, 'cy': cy, 'cz': cz})

    def _find_player_names(self):
        self.player_names = player_names = {}
        first_frame = self.all_frames[0]
        for entry in first_frame['replications']:
            actor = entry['actor_id']['value']
            if 'updated' in entry['value']:
                vals_updated = entry['value']['updated']
                for v in vals_updated:
                    if v['name'] == 'Engine.PlayerReplicationInfo:PlayerName':
                        name = v['value']['string']
                        player_names[actor] = name

    def get_players(self):
        return self.player_names

    def _find_shots(self):
        "Finds the frame where a shot is rewarded to a player, not necessarily the frame where the shot is actually taken"
        frames = self.all_frames
        name = self.player_names
        self.shots = shots = []
        for frame in frames:
            for entry in frame.get('replications'):
                actor = entry['actor_id']['value']
                for event in entry.get('value', {}).get('updated', []):
                    if event['name'] == "TAGame.PRI_TA:MatchGoals":
                        shots.append({'id': actor, 'player': name[actor], 'time': frame['time']})

    def get_shots(self):
        return self.shots

if __name__ == "__main__":
    r = RocketLeagueAnalyzer("../data/json_detailed/16610695-f169-4ded-be4e-8e8a6ee3daf7.tracking.json")
    print(r.get_players())
    print(r.get_shots())
    print(r.get_ball_dict())
    print(r.get_ball_ids())
    print(r.ball_positions)


# Other notes
# Countdown timer: ReplicatedRoundCountDownNumber
# Ball bouncing: https://samuelpmish.github.io/notes/RocketLeague/ball_bouncing/
# Convert quart rotation to euler: https://github.com/SaltieRL/carball/blob/f9e4854e173bb6db3e53cc93ac1daa4e58952e69/carball/json_parser/actor_parsing.py#L96
