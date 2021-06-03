import carball
import glob

replays = glob.glob('../data/replay/*.replay')
print(replays)

for r in replays:
    print("Processing ", r)
    analysis = carball.analyze_replay_file(r)
    with open(r.replace("replay", "json"), "w") as f:
        analysis.write_json_out_to_file(f)
