import carball
import glob
import os

replays = glob.glob('../data/replay/*.replay')
print(replays)

for r in replays:
    print("Processing ", r)
    
    json_name = r.replace("replay", "json")
    df_name = r.replace("replay", "dataframe", 1).replace("replay", "csv")

    if os.path.exists(json_name) and os.path.exists(df_name):
        print(f"{r} files exist, skipping...")
        continue

    analysis = carball.analyze_replay_file(r)
    with open(json_name, "w") as f:
        analysis.write_json_out_to_file(f)
    df = analysis.get_data_frame()
    with open(df_name, "w") as f:
        df.to_csv(f)

