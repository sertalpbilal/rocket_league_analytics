import carball
import glob
import os

replays = glob.glob('../data/replay/*.replay')
print(replays)

for r in replays:
    print("Processing ", r)
    json_name = r.replace("replay", "json")
    if os.path.exists(json_name):
        print(f"{json_name} exists, skipping...")
        continue
    analysis = carball.analyze_replay_file(r)
    with open(json_name, "w") as f:
        analysis.write_json_out_to_file(f)
