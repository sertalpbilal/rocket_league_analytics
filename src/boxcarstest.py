# TODO: split ground and aerial heatmap based on z values
# TODO: calculate how long the ball is in our half vs. the opponent's half
# TODO: show touches in each half or third of the pitch
# TODO: detect forfeits
# TODO: add colormap to heatmaps like in this example: https://www.dreamteamfc.com/c/wp-content/uploads/sites/4/2018/05/mesut-ozil-final.jpg?strip=all&w=742&quality=100
# TODO: fix issues with GD chart when there is only 1 game and it's an overtime game
# TODO: fix axes on charts which show game numbers to only show ints and not floats
# TODO: handle own-goals (add stats for own goals scored)
# TODO: decide whether to plot "non-shot" goals in the 4 goal heatmaps
# TODO: plot assists (maybe highlight assisted goals in a different color in the 4 goal heatmaps)

import csv
import json
import os
import time
from collections import Counter
from statistics import mean

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
from tabulate import tabulate

startTime = time.time()

check_new = False  # Only processes new files (in separate directory)
side_view_3d_scatter = False  # Show 3D scatterplot from the side by rotating it 180 degrees

# Names in Rocket League
my_name = "games5425898691"
your_name = "enpitsu"

# Names for program output
my_alias = "Allan"
your_alias = "Sertalp"

# Colors for output on graphs
my_color = "royalblue"
your_color = "mediumblue"
our_color = "green"
their_color = "darkred"

bg_img = plt.imread("simple-pitch.png")

if check_new:
    path_to_json = 'data/json-new/'
else:
    path_to_json = 'data/json/'

path_to_untrimmed_csv = 'data/dataframe/'
path_to_csv = 'data/dataframe-trimmed/'

# Trim CSVs if there are CSVs to trim
if len(os.listdir(path_to_untrimmed_csv)) > 0:
    csv_files = [pos_csv for pos_csv in os.listdir(path_to_untrimmed_csv) if pos_csv.endswith('.csv')]

    print("Trimming", len(csv_files), "CSV files...")
    frames_to_skip = 20

    for file in csv_files:
        with open(path_to_untrimmed_csv + file) as f:
            reader = csv.reader(f)
            my_list = list(reader)

        nrows = len(my_list)
        ncols = len(my_list[0])

        my_x_arr = []
        my_y_arr = []
        my_z_arr = []
        your_x_arr = []
        your_y_arr = []
        your_z_arr = []
        ball_x_arr = []
        ball_y_arr = []
        ball_z_arr = []
        time_status = "NT"

        for col in range(ncols):
            for row in range(3, nrows, frames_to_skip):
                if my_list[row][col] != "":
                    if my_list[0][col] == my_name:
                        if my_list[1][col] == "pos_x":
                            my_x_arr.append(round(float(my_list[row][col])))
                        elif my_list[1][col] == "pos_y":
                            my_y_arr.append(round(float(my_list[row][col])))
                        elif my_list[1][col] == "pos_z":
                            my_z_arr.append(round(float(my_list[row][col])))

                    elif my_list[0][col] == your_name:
                        if my_list[1][col] == "pos_x":
                            your_x_arr.append(round(float(my_list[row][col])))
                        elif my_list[1][col] == "pos_y":
                            your_y_arr.append(round(float(my_list[row][col])))
                        elif my_list[1][col] == "pos_z":
                            your_z_arr.append(round(float(my_list[row][col])))

                    elif my_list[0][col] == "ball":
                        if my_list[1][col] == "pos_x":
                            ball_x_arr.append(round(float(my_list[row][col])))
                        elif my_list[1][col] == "pos_y":
                            ball_y_arr.append(round(float(my_list[row][col])))
                        elif my_list[1][col] == "pos_z":
                            ball_z_arr.append(round(float(my_list[row][col])))

                    elif my_list[0][col] == "game":
                        if my_list[1][col] == "is_overtime":
                            time_status = "OT"

        dfObj = pd.DataFrame(
            [my_x_arr, my_y_arr, my_z_arr, your_x_arr, your_y_arr, your_z_arr, ball_x_arr, ball_y_arr, ball_z_arr]).T
        if time_status == "OT":
            dfObj.columns = [my_name + "_pos_x", my_name + "_pos_y", my_name + "_pos_z",
                             your_name + "_pos_x", your_name + "_pos_y", your_name + "_pos_z",
                             "ball_pos_x", "ball_pos_y", "ball_pos_z-GAME-WENT-OT"]
        else:
            dfObj.columns = [my_name + "_pos_x", my_name + "_pos_y", my_name + "_pos_z",
                             your_name + "_pos_x", your_name + "_pos_y", your_name + "_pos_z",
                             "ball_pos_x", "ball_pos_y", "ball_pos_z"]

        # dfObj.dropna(axis=0, how='any', thresh=None, subset=None, inplace=True)

        dfObj.to_csv(index=False, path_or_buf=path_to_csv + file, float_format='{:.0f}'.format)
        os.remove(path_to_untrimmed_csv + file)

    trimexecutionTime = (time.time() - startTime)
    print('Trimming completed in ', "%.2f" % trimexecutionTime, 'seconds\n\n')

json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]

json_files_2v2 = []
file_counter = 0
file_time = []

# Only keep RANKED_DOUBLES games
for file in json_files:
    f = open(path_to_json + file, )
    data = json.load(f)

    local_playlist = ""

    for i in data["gameMetadata"]["playlist"]:
        local_playlist += i

    if local_playlist == "RANKED_DOUBLES":
        json_files_2v2.append(file)

# Sort files by time created - loop through jsons, get start time of match, then sort by time
for file in json_files_2v2:
    f = open(path_to_json + file, )
    data = json.load(f)
    file_counter += 1

    local_time = ""

    for i in data["gameMetadata"]["time"]:
        local_time += i

    file_time.append(local_time)


file_counter = 0
new_json_files = [x for _, x in sorted(zip(file_time, json_files_2v2))]
new_csv_files = []

local_time_array = []
streak_start_games = []
file_pos = 0

for file in new_json_files:
    f = open(path_to_json + file, )
    data = json.load(f)
    local_time = ""

    for i in data["gameMetadata"]["time"]:
        local_time += i

    local_time_array.append(int(local_time))

    # find the time difference between current game and previous game to see if they are part of a streak
    # if at least 30 minutes passed between the two games, they are not part of the same streak
    streak_min_threshold = 30
    if file_pos > 0:
        if local_time_array[file_pos] - local_time_array[file_pos - 1] >= (streak_min_threshold * 60):
            streak_start_games.append(file_pos)

    new_csv_files.append(file.replace(".json", ".csv"))
    file_pos += 1

my_misses_distancetogoal = []
your_misses_distancetogoal = []
their_misses_distancetogoal = []

my_goals_distancetogoal = []
your_goals_distancetogoal = []
their_goals_distancetogoal = []

my_shots_distancetogoal = []
my_shots_goal_or_miss = []  # goal = 1, miss = 0

your_shots_distancetogoal = []
your_shots_goal_or_miss = []  # goal = 1, miss = 0

our_shots_distancetogoal = []
our_shots_goal_or_miss = []  # my goal = 1, my miss = 0, your goal = 2, your miss = 3

my_id = ""
your_id = ""

our_col = []
their_col = []

my_shots_x = []
my_shots_y = []
my_shots_z = []

your_shots_x = []
your_shots_y = []
your_shots_z = []

our_shots_x = []
our_shots_y = []
our_shots_z = []

their_shots_x = []
their_shots_y = []
their_shots_z = []

all_shots_x = []
all_shots_y = []
all_shots_z = []

my_goals_x = []
my_goals_y = []
my_goals_z = []

your_goals_x = []
your_goals_y = []
your_goals_z = []

their_goals_x = []
their_goals_y = []
their_goals_z = []

my_touches_x = []
my_touches_y = []
my_touches_z = []

your_touches_x = []
your_touches_y = []
your_touches_z = []

their_touches_x = []
their_touches_y = []
their_touches_z = []

my_misses_x = []
my_misses_y = []
my_misses_z = []

your_misses_x = []
your_misses_y = []
your_misses_z = []

their_misses_x = []
their_misses_y = []
their_misses_z = []

my_touches_count = 0
your_touches_count = 0
their_touches_count = 0

win_count = 0
loss_count = 0
result_array = []
result_array_num = []
gd_array = []
normaltime_gd_array = []
result_color = []
gs_array = []
gc_array = []
shots_alphas = []

shot_diff_array = []

our_team_color = []

my_assists_count = 0
your_assists_count = 0
their_assists_count = 0

my_saves_count = 0
your_saves_count = 0
their_saves_count = 0

my_goals_over_time = []
your_goals_over_time = []
their_goals_over_time = []

my_shots_over_time = []
your_shots_over_time = []
their_shots_over_time = []

my_saves_over_time = []
your_saves_over_time = []
their_saves_over_time = []

my_assists_over_time = []
your_assists_over_time = []
their_assists_over_time = []

my_demos_count = 0
your_demos_count = 0
their_demos_count = 0

my_demos_conceded_count = 0
your_demos_conceded_count = 0
their_demos_conceded_count = 0

my_passes_count = 0
your_passes_count = 0
their_passes_count = 0

my_score_count = 0
your_score_count = 0
their_score_count = 0

my_clears_count = 0
your_clears_count = 0
their_clears_count = 0

my_turnovers_count = 0
your_turnovers_count = 0
their_turnovers_count = 0

my_turnovers_won_count = 0
your_turnovers_won_count = 0
their_turnovers_won_count = 0

# TODO: take FF into account
overtime_wins_count = 0
overtime_losses_count = 0

my_goal_count = 0
your_goal_count = 0
their_goal_count = 0

for file in new_json_files:
    file_counter += 1
    if file_counter < len(new_json_files) + 1:

        f = open(path_to_json + file, )
        data = json.load(f)

        local_color = "blue"
        local_GS = 0
        local_GC = 0

        local_my_goals = 0
        local_your_goals = 0
        local_their_goals = 0

        local_my_shots = 0
        local_your_shots = 0
        local_our_shots = 0
        local_their_shots = 0
        local_my_saves = 0
        local_your_saves = 0
        local_their_saves = 0
        local_my_assists = 0
        local_your_assists = 0
        local_their_assists = 0

        # Link our names to IDs
        for i in data['players']:
            if i["name"] == my_name:
                if i["isOrange"]:
                    local_color = "orange"
                my_id = i["id"]["id"]
            elif i["name"] == your_name:
                your_id = i["id"]["id"]

        for i in data['players']:
            if i["id"]["id"] == my_id:
                if "assists" in i:
                    local_my_assists += i["assists"]
                    my_assists_count += i["assists"]
            elif i["id"]["id"] == your_id:
                if "assists" in i:
                    local_your_assists += i["assists"]
                    your_assists_count += i["assists"]
            else:
                if "assists" in i:
                    local_their_assists += i["assists"]
                    their_assists_count += i["assists"]

        for i in data["gameMetadata"]["goals"]:
            if i["playerId"]["id"] == my_id:
                local_my_goals += 1
                my_goal_count += 1
            elif i["playerId"]["id"] == your_id:
                local_your_goals += 1
                your_goal_count += 1
            else:
                local_their_goals += 1
                their_goal_count += 1

        # TODO: totalAerials, totalDribbles
        for i in data["players"]:
            if i["id"]["id"] == my_id:
                if "score" in i:
                    my_score_count += i["score"]
                if "totalPasses" in i["stats"]["hitCounts"]:
                    my_passes_count += i["stats"]["hitCounts"]["totalPasses"]
                if "totalClears" in i["stats"]["hitCounts"]:
                    my_clears_count += i["stats"]["hitCounts"]["totalClears"]
                if "turnovers" in i["stats"]["possession"]:
                    my_turnovers_count += i["stats"]["possession"]["turnovers"]
                if "wonTurnovers" in i["stats"]["possession"]:
                    my_turnovers_won_count += i["stats"]["possession"]["wonTurnovers"]

            elif i["id"]["id"] == your_id:
                if "score" in i:
                    your_score_count += i["score"]
                if "totalPasses" in i["stats"]["hitCounts"]:
                    your_passes_count += i["stats"]["hitCounts"]["totalPasses"]
                if "totalClears" in i["stats"]["hitCounts"]:
                    your_clears_count += i["stats"]["hitCounts"]["totalClears"]
                if "turnovers" in i["stats"]["possession"]:
                    your_turnovers_count += i["stats"]["possession"]["turnovers"]
                if "wonTurnovers" in i["stats"]["possession"]:
                    your_turnovers_won_count += i["stats"]["possession"]["wonTurnovers"]

            else:
                if "score" in i:
                    their_score_count += i["score"]
                if "totalPasses" in i["stats"]["hitCounts"]:
                    their_passes_count += i["stats"]["hitCounts"]["totalPasses"]
                if "totalClears" in i["stats"]["hitCounts"]:
                    their_clears_count += i["stats"]["hitCounts"]["totalClears"]
                if "turnovers" in i["stats"]["possession"]:
                    their_turnovers_count += i["stats"]["possession"]["turnovers"]
                if "wonTurnovers" in i["stats"]["possession"]:
                    their_turnovers_won_count += i["stats"]["possession"]["wonTurnovers"]

        if "demos" in data["gameMetadata"]:
            for i in data["gameMetadata"]["demos"]:
                if i["attackerId"]["id"] == my_id:
                    my_demos_count += 1
                    their_demos_conceded_count += 1
                if i["attackerId"]["id"] == your_id:
                    your_demos_count += 1
                    their_demos_conceded_count += 1
                if i["victimId"]["id"] == my_id:
                    their_demos_count += 1
                    my_demos_conceded_count += 1
                if i["victimId"]["id"] == your_id:
                    their_demos_count += 1
                    your_demos_conceded_count += 1

        if local_color == "orange":
            our_team_color.append("O")
            if data["teams"][0]["isOrange"]:
                local_GS = data["teams"][0]["score"]
                local_GC = data["teams"][1]["score"]
            elif data["teams"][1]["isOrange"]:
                local_GS = data["teams"][1]["score"]
                local_GC = data["teams"][0]["score"]
        elif local_color == "blue":
            our_team_color.append("B")
            if data["teams"][0]["isOrange"]:
                local_GS = data["teams"][1]["score"]
                local_GC = data["teams"][0]["score"]
            elif data["teams"][1]["isOrange"]:
                local_GS = data["teams"][0]["score"]
                local_GC = data["teams"][1]["score"]


        for i in data['gameStats']['hits']:
            if i["playerId"]["id"] == my_id:
                my_touches_count += 1
                if local_color == "orange":
                    my_touches_x.append(i["ballData"]["posX"] * -1)
                    my_touches_y.append(i["ballData"]["posY"] * -1)
                else:
                    my_touches_x.append(i["ballData"]["posX"])
                    my_touches_y.append(i["ballData"]["posY"])
                my_touches_z.append(i["ballData"]["posZ"] * -1)
            elif i["playerId"]["id"] == your_id:
                your_touches_count += 1
                if local_color == "orange":
                    your_touches_x.append(i["ballData"]["posX"] * -1)
                    your_touches_y.append(i["ballData"]["posY"] * -1)
                else:
                    your_touches_x.append(i["ballData"]["posX"])
                    your_touches_y.append(i["ballData"]["posY"])
                your_touches_z.append(i["ballData"]["posZ"] * -1)
            else:
                their_touches_count += 1
                if local_color == "orange":
                    their_touches_x.append(i["ballData"]["posX"] * -1)
                    their_touches_y.append(i["ballData"]["posY"] * -1)
                else:
                    their_touches_x.append(i["ballData"]["posX"])
                    their_touches_y.append(i["ballData"]["posY"])
                their_touches_z.append(i["ballData"]["posZ"] * -1)

            if "save" in i:
                if i["playerId"]["id"] == my_id:
                    my_saves_count += 1
                    local_my_saves += 1

                elif i["playerId"]["id"] == your_id:
                    your_saves_count += 1
                    local_your_saves += 1

                else:
                    their_saves_count += 1
                    local_their_saves += 1

            if "shot" in i:
                if i["playerId"]["id"] == my_id or i["playerId"]["id"] == your_id:
                    local_our_shots += 1
                    if local_color == "orange":
                        all_shots_x.append(i["ballData"]["posX"] * -1)
                        all_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        all_shots_x.append(i["ballData"]["posX"])
                        all_shots_y.append(i["ballData"]["posY"])
                    all_shots_z.append(i["ballData"]["posZ"])

                    if "goal" in i:
                        if i["playerId"]["id"] == my_id:
                            if local_color == "orange":
                                my_goals_x.append(i["ballData"]["posX"] * -1)
                                my_goals_y.append(i["ballData"]["posY"] * -1)
                            else:
                                my_goals_x.append(i["ballData"]["posX"])
                                my_goals_y.append(i["ballData"]["posY"])
                            my_goals_z.append(i["ballData"]["posZ"])
                            local_my_shots += 1
                        else:
                            if local_color == "orange":
                                your_goals_x.append(i["ballData"]["posX"] * -1)
                                your_goals_y.append(i["ballData"]["posY"] * -1)
                            else:
                                your_goals_x.append(i["ballData"]["posX"])
                                your_goals_y.append(i["ballData"]["posY"])
                            your_goals_z.append(i["ballData"]["posZ"])
                            local_your_shots += 1

                    else:
                        if i["playerId"]["id"] == my_id:
                            if local_color == "orange":
                                my_misses_x.append(i["ballData"]["posX"] * -1)
                                my_misses_y.append(i["ballData"]["posY"] * -1)
                            else:
                                my_misses_x.append(i["ballData"]["posX"])
                                my_misses_y.append(i["ballData"]["posY"])
                            my_misses_z.append(i["ballData"]["posZ"])
                            local_my_shots += 1
                        else:
                            if local_color == "orange":
                                your_misses_x.append(i["ballData"]["posX"] * -1)
                                your_misses_y.append(i["ballData"]["posY"] * -1)
                            else:
                                your_misses_x.append(i["ballData"]["posX"])
                                your_misses_y.append(i["ballData"]["posY"])
                            your_misses_z.append(i["ballData"]["posZ"])
                            local_your_shots += 1

                else:
                    local_their_shots += 1
                    if local_color == "orange":
                        all_shots_x.append(i["ballData"]["posX"] * -1)
                        all_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        all_shots_x.append(i["ballData"]["posX"])
                        all_shots_y.append(i["ballData"]["posY"])
                    all_shots_z.append(i["ballData"]["posZ"])

                    if "goal" in i:
                        if local_color == "orange":
                            their_goals_x.append(i["ballData"]["posX"] * -1)
                            their_goals_y.append(i["ballData"]["posY"] * -1)
                        else:
                            their_goals_x.append(i["ballData"]["posX"])
                            their_goals_y.append(i["ballData"]["posY"])
                        their_goals_z.append(i["ballData"]["posZ"])
                        their_goals_distancetogoal.append(i["distanceToGoal"])

                    else:
                        if local_color == "orange":
                            their_misses_x.append(i["ballData"]["posX"] * -1)
                            their_misses_y.append(i["ballData"]["posY"] * -1)
                        else:
                            their_misses_x.append(i["ballData"]["posX"])
                            their_misses_y.append(i["ballData"]["posY"])
                        their_misses_z.append(i["ballData"]["posZ"])
                        their_misses_distancetogoal.append(i["distanceToGoal"])

            if (i["playerId"]["id"] == my_id or i["playerId"]["id"] == your_id) and "shot" in i:
                if i["playerId"]["id"] == my_id and "goal" in i:
                    our_shots_distancetogoal.append(i["distanceToGoal"])
                    #local_my_goals += 1

                    if local_color == "orange":
                        our_shots_x.append(i["ballData"]["posX"] * -1)
                        our_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        our_shots_x.append(i["ballData"]["posX"])
                        our_shots_y.append(i["ballData"]["posY"])
                    our_shots_z.append(i["ballData"]["posZ"])

                    our_col.append("lime")
                if i["playerId"]["id"] == my_id and "goal" not in i:
                    our_shots_distancetogoal.append(i["distanceToGoal"])

                    if local_color == "orange":
                        our_shots_x.append(i["ballData"]["posX"] * -1)
                        our_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        our_shots_x.append(i["ballData"]["posX"])
                        our_shots_y.append(i["ballData"]["posY"])
                    our_shots_z.append(i["ballData"]["posZ"])

                    our_col.append("red")
                if i["playerId"]["id"] == your_id and "goal" in i:
                    #local_your_goals += 1
                    our_shots_distancetogoal.append(i["distanceToGoal"])

                    if local_color == "orange":
                        our_shots_x.append(i["ballData"]["posX"] * -1)
                        our_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        our_shots_x.append(i["ballData"]["posX"])
                        our_shots_y.append(i["ballData"]["posY"])
                    our_shots_z.append(i["ballData"]["posZ"])

                    our_col.append("darkgreen")
                if i["playerId"]["id"] == your_id and "goal" not in i:
                    our_shots_distancetogoal.append(i["distanceToGoal"])

                    if local_color == "orange":
                        our_shots_x.append(i["ballData"]["posX"] * -1)
                        our_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        our_shots_x.append(i["ballData"]["posX"])
                        our_shots_y.append(i["ballData"]["posY"])
                    our_shots_z.append(i["ballData"]["posZ"])

                    our_col.append("darkred")

            if i["playerId"]["id"] == my_id and "shot" in i:
                my_shots_distancetogoal.append(i["distanceToGoal"])

                if local_color == "orange":
                    my_shots_x.append(i["ballData"]["posX"] * -1)
                    my_shots_y.append(i["ballData"]["posY"] * -1)
                else:
                    my_shots_x.append(i["ballData"]["posX"])
                    my_shots_y.append(i["ballData"]["posY"])
                my_shots_z.append(i["ballData"]["posZ"])

                if "goal" in i:
                    my_shots_goal_or_miss.append(1)
                    my_goals_distancetogoal.append(i["distanceToGoal"])
                else:
                    my_shots_goal_or_miss.append(0)
                    my_misses_distancetogoal.append(i["distanceToGoal"])

            if i["playerId"]["id"] == your_id and "shot" in i:
                your_shots_distancetogoal.append(i["distanceToGoal"])
                if local_color == "orange":
                    your_shots_x.append(i["ballData"]["posX"] * -1)
                    your_shots_y.append(i["ballData"]["posY"] * -1)
                else:
                    your_shots_x.append(i["ballData"]["posX"])
                    your_shots_y.append(i["ballData"]["posY"])
                your_shots_z.append(i["ballData"]["posZ"])
                if "goal" in i:
                    your_shots_goal_or_miss.append(1)
                    your_goals_distancetogoal.append(i["distanceToGoal"])
                else:
                    your_shots_goal_or_miss.append(0)
                    your_misses_distancetogoal.append(i["distanceToGoal"])

            if (i["playerId"]["id"] != my_id and i["playerId"]["id"] != your_id) and "shot" in i:
                if "goal" in i:
                    if local_color == "orange":
                        their_shots_x.append(i["ballData"]["posX"] * -1)
                        their_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        their_shots_x.append(i["ballData"]["posX"])
                        their_shots_y.append(i["ballData"]["posY"])
                    their_shots_z.append(i["ballData"]["posZ"])

                    their_col.append("green")
                else:
                    if local_color == "orange":
                        their_shots_x.append(i["ballData"]["posX"] * -1)
                        their_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        their_shots_x.append(i["ballData"]["posX"])
                        their_shots_y.append(i["ballData"]["posY"])
                    their_shots_z.append(i["ballData"]["posZ"])

                    their_col.append("red")

        # print(file, local_GS, local_GC, local_our_shots, local_their_shots)

        gd_array.append(local_GS - local_GC)
        gs_array.append(local_GS)
        gc_array.append(local_GC)
        shot_diff_array.append(local_our_shots - local_their_shots)

        my_goals_over_time.append(local_my_goals)
        your_goals_over_time.append(local_your_goals)
        their_goals_over_time.append(local_their_goals)

        my_shots_over_time.append(local_my_shots)
        your_shots_over_time.append(local_your_shots)
        their_shots_over_time.append(local_their_shots)

        my_saves_over_time.append(local_my_saves)
        your_saves_over_time.append(local_your_saves)
        their_saves_over_time.append(local_their_saves)

        my_assists_over_time.append(local_my_assists)
        your_assists_over_time.append(local_your_assists)
        their_assists_over_time.append(local_their_assists)

        local_wentOvertime = False

        # check if game went overtime -- only if there is 1 GD between the teams, or 0 GD (FF in OT)
        if (local_GS - local_GC) == 1 or (local_GC - local_GS) == 1 or (local_GC == local_GS):
            csv_file = file.replace(".json", ".csv")
            with open(path_to_csv + csv_file, newline='') as f:
                reader = csv.reader(f)
                row1 = next(reader)
            if "ball_pos_z-GAME-WENT-OT" in row1:
                local_wentOvertime = True
                if local_GS > local_GC:
                    overtime_wins_count += 1
                elif local_GC > local_GS:
                    overtime_losses_count += 1

        if local_GS > local_GC and local_wentOvertime:
            win_count += 1
            result_array.append("W")
            result_array_num.append(1)
            result_color.append("darkblue")

        elif local_GS > local_GC and not local_wentOvertime:
            win_count += 1
            result_array.append("W")
            result_array_num.append(1)
            result_color.append(our_color)
            normaltime_gd_array.append(local_GS - local_GC)

        elif local_GC > local_GS and local_wentOvertime:
            loss_count += 1
            result_array.append("L")
            result_array_num.append(-1)
            result_color.append("darkorange")

        elif local_GC > local_GS and not local_wentOvertime:
            loss_count += 1
            result_array.append("L")
            result_array_num.append(-1)
            result_color.append(their_color)
            normaltime_gd_array.append(local_GS - local_GC)

        # TODO: Handle FFs

my_col = []
your_col = []

for val in my_shots_goal_or_miss:
    if val == 1:
        my_col.append('green')
    else:
        my_col.append('red')

for val in your_shots_goal_or_miss:
    if val == 1:
        your_col.append('green')
    else:
        your_col.append('red')

fig = plt.figure(figsize=(40, 20))

your_miss_count = 0
for shot in range(0, len(your_shots_goal_or_miss)):
    if your_shots_goal_or_miss[shot] == 0:
        your_miss_count += 1

my_miss_count = 0
for shot in range(0, len(my_shots_goal_or_miss)):
    if my_shots_goal_or_miss[shot] == 0:
        my_miss_count += 1

their_miss_count = len(their_misses_distancetogoal)

if (their_goal_count + their_miss_count) > 0:
    their_gs_ratio = their_goal_count / (their_goal_count + their_miss_count)
else:
    their_gs_ratio = 0

if (my_goal_count + my_miss_count) > 0:
    my_gs_ratio = my_goal_count / (my_goal_count + my_miss_count)
else:
    my_gs_ratio = 0

if (your_goal_count + your_miss_count) > 0:
    your_gs_ratio = your_goal_count / (your_goal_count + your_miss_count)
else:
    your_gs_ratio = 0

our_goal_count = my_goal_count + your_goal_count
our_miss_count = my_miss_count + your_miss_count

if (our_goal_count + our_miss_count) > 0:
    our_gs_ratio = our_goal_count / (our_goal_count + our_miss_count)
else:
    our_gs_ratio = 0

our_assists_count = my_assists_count + your_assists_count
our_saves_count = my_saves_count + your_saves_count
our_demos_count = my_demos_count + your_demos_count
our_demos_conceded_count = my_demos_conceded_count + your_demos_conceded_count
our_score_count = my_score_count + your_score_count
our_passes_count = my_passes_count + your_passes_count
our_clears_count = my_clears_count + your_clears_count
our_touches_count = my_touches_count + your_touches_count
our_turnovers_count = my_turnovers_count + your_turnovers_count
our_turnovers_won_count = my_turnovers_won_count + your_turnovers_won_count

if my_goal_count > 0:
    my_avg_goal_distance = "%.0f" % mean(my_goals_distancetogoal)
else:
    my_avg_goal_distance = 0

if your_goal_count > 0:
    your_avg_goal_distance = "%.0f" % mean(your_goals_distancetogoal)
else:
    your_avg_goal_distance = 0

if my_miss_count > 0:
    my_avg_miss_distance = "%.0f" % mean(my_misses_distancetogoal)
else:
    my_avg_miss_distance = 0

if your_miss_count > 0:
    your_avg_miss_distance = "%.0f" % mean(your_misses_distancetogoal)
else:
    your_avg_miss_distance = 0

if (my_goal_count + my_miss_count) > 0:
    my_avg_shot_distance = "%.0f" % mean(my_shots_distancetogoal)
else:
    my_avg_shot_distance = 0

if (your_goal_count + your_miss_count) > 0:
    your_avg_shot_distance = "%.0f" % mean(your_shots_distancetogoal)
else:
    your_avg_shot_distance = 0

if my_goal_count > 0 and your_goal_count == 0:
    our_avg_goal_distance = my_avg_goal_distance
if my_goal_count == 0 and your_goal_count > 0:
    our_avg_goal_distance = your_avg_goal_distance
if my_goal_count == 0 and your_goal_count == 0:
    our_avg_goal_distance = 0
if my_goal_count > 0 and your_goal_count > 0:
    our_avg_goal_distance = "%.0f" % mean(my_goals_distancetogoal + your_goals_distancetogoal)

if my_miss_count > 0 and your_miss_count == 0:
    our_avg_miss_distance = my_avg_miss_distance
if my_miss_count == 0 and your_miss_count > 0:
    our_avg_miss_distance = your_avg_miss_distance
if my_miss_count == 0 and your_miss_count == 0:
    our_avg_miss_distance = 0
if my_miss_count > 0 and your_miss_count > 0:
    our_avg_miss_distance = "%.0f" % mean(my_misses_distancetogoal + your_misses_distancetogoal)

if (my_miss_count + my_goal_count) > 0 and (your_miss_count + your_goal_count) == 0:
    our_avg_shot_distance = my_avg_shot_distance
if (my_miss_count + my_goal_count) == 0 and (your_miss_count + your_goal_count) > 0:
    our_avg_shot_distance = your_avg_shot_distance
if (my_miss_count + my_goal_count) == 0 and (your_miss_count + your_goal_count) == 0:
    our_avg_shot_distance = 0
if (my_miss_count + my_goal_count) > 0 and (your_miss_count + your_goal_count) > 0:
    our_avg_shot_distance = "%.0f" % mean(my_shots_distancetogoal + your_shots_distancetogoal)

if their_goal_count > 0:
    their_avg_goal_distance = "%.0f" % mean(their_goals_distancetogoal)
else:
    their_avg_goal_distance = 0

if their_miss_count > 0:
    their_avg_miss_distance = "%.0f" % mean(their_misses_distancetogoal)
else:
    their_avg_miss_distance = 0

if (their_goal_count + their_miss_count) > 0:
    their_avg_shot_distance = "%.0f" % mean(their_goals_distancetogoal + their_misses_distancetogoal)
else:
    their_avg_shot_distance = 0

individual_data = [["Goals", my_goal_count, your_goal_count],
                   ["Misses", my_miss_count, your_miss_count],
                   ["G/Shot", "%.2f" % my_gs_ratio, "%.2f" % your_gs_ratio],
                   ["Assists", my_assists_count, your_assists_count],
                   ["Saves", my_saves_count, your_saves_count],
                   ["Demos", my_demos_count, your_demos_count],
                   ["Demoed", my_demos_conceded_count, your_demos_conceded_count],
                   ["Score", my_score_count, your_score_count],
                   ["Passes", my_passes_count, your_passes_count],
                   ["Clears", my_clears_count, your_clears_count],
                   ["Touches", my_touches_count, your_touches_count],
                   ["Goal Distance", my_avg_goal_distance, your_avg_goal_distance],
                   ["Miss Distance", my_avg_miss_distance, your_avg_miss_distance],
                   ["Shot Distance", my_avg_shot_distance, your_avg_shot_distance],
                   ["Won Ball", my_turnovers_won_count, your_turnovers_won_count],
                   ["Lost Ball", my_turnovers_count, your_turnovers_count]
                   ]

team_data = [["Goals", our_goal_count, their_goal_count],
             ["Misses", our_miss_count, their_miss_count],
             ["G/Shot", "%.2f" % our_gs_ratio, "%.2f" % their_gs_ratio],
             ["Assists", our_assists_count, their_assists_count],
             ["Saves", our_saves_count, their_saves_count],
             ["Demos", our_demos_count, their_demos_count],
             ["Score", our_score_count, their_score_count],
             ["Passes", our_passes_count, their_passes_count],
             ["Clears", our_clears_count, their_clears_count],
             ["Touches", our_touches_count, their_touches_count],
             ["Goal Distance", our_avg_goal_distance, their_avg_goal_distance],
             ["Miss Distance", our_avg_miss_distance, their_avg_miss_distance],
             ["Shot Distance", our_avg_shot_distance, their_avg_shot_distance],
             ["Won Ball", our_turnovers_won_count, their_turnovers_won_count],
             ]

print(tabulate(individual_data, headers=["STATS", my_alias, your_alias], numalign="right"))
print("\n")
print(tabulate(team_data, headers=["STATS", "Us", "Them"], numalign="right"))

res_num = 0
local_wins_in_streak = 0
local_losses_in_streak = 0

streak_end_games = []
for streak in streak_start_games:
    streak_end_games.append(streak - 1)

streak_end_games.append(len(json_files_2v2) - 1)

streak_wins = []
streak_losses = []

streak_results = []
local_streak_results = ""

streak_num_games = []

streak_goals = []
streak_my_goals = []
streak_your_goals = []
streak_their_goals = []
local_my_goals_in_streak = 0
local_your_goals_in_streak = 0
local_our_goals_in_streak = 0
local_their_goals_in_streak = 0

for result in range(0, len(result_array)):
    if result_array[result] == "W":
        local_wins_in_streak += 1
    elif result_array[result] == "L":
        local_losses_in_streak += 1

    local_my_goals_in_streak += my_goals_over_time[result]
    local_your_goals_in_streak += your_goals_over_time[result]

    local_our_goals_in_streak += (my_goals_over_time[result] + your_goals_over_time[result])
    local_their_goals_in_streak += their_goals_over_time[result]

    local_streak_results += str(result_array[result] + " ")

    if res_num in streak_end_games:
        streak_wins.append(local_wins_in_streak)
        streak_losses.append(local_losses_in_streak)
        streak_results.append(local_streak_results)
        streak_num_games.append(local_wins_in_streak + local_losses_in_streak)
        streak_goals.append(local_our_goals_in_streak)
        streak_my_goals.append(local_my_goals_in_streak)
        streak_your_goals.append(local_your_goals_in_streak)
        streak_their_goals.append(local_their_goals_in_streak)
        local_wins_in_streak = 0
        local_losses_in_streak = 0
        local_streak_results = ""
        local_our_goals_in_streak = 0
        local_my_goals_in_streak = 0
        local_your_goals_in_streak = 0
        local_their_goals_in_streak = 0

    res_num += 1

streak_data = []

# print as table (tabulate)
for streak in range(0, len(streak_num_games)):
    num_games_in_streak = streak_wins[streak] + streak_losses[streak]
    win_rate = streak_wins[streak] / num_games_in_streak
    win_pct = "%.0f" % (win_rate * 100) + "%"
    our_goals_per_game_streak = "%.1f" % (streak_goals[streak] / num_games_in_streak)
    my_goals_per_game_streak = "%.1f" % (streak_my_goals[streak] / num_games_in_streak)
    your_goals_per_game_streak = "%.1f" % (streak_your_goals[streak] / num_games_in_streak)
    their_goals_per_game_streak = "%.1f" % (streak_their_goals[streak] / num_games_in_streak)
    gd_per_game_streak = "%.1f" % ((streak_goals[streak] - streak_their_goals[streak]) / num_games_in_streak)

    streak_data.append(
        [win_pct, streak_results[streak], streak_wins[streak] + streak_losses[streak], streak_wins[streak],
         streak_losses[streak],
         my_goals_per_game_streak, your_goals_per_game_streak, our_goals_per_game_streak, their_goals_per_game_streak,
         gd_per_game_streak])

print("\n")
print(tabulate(streak_data,
               headers=["Win %", "Results", "Games", "Wins", "Losses", my_alias + " Goals/G", your_alias + " Goals/G",
                        "Our Goals/G", "Their Goals/G", "Goal Diff./G"], numalign="right"))
print("\n")

games_nr = len(new_json_files)

"""
scorelines_array = []
for g in range(0,len(gs_array)):
    scoreline_str = str(gs_array[g]) + "-" + str(gc_array[g])
    scorelines_array.append(scoreline_str)

scoreline_counter = Counter(scorelines_array)
scoreline_counter_keys = list(scoreline_counter.keys())
scoreline_counter_values = list(scoreline_counter.values())

scoreline_and_pct = []

for score in range(0,len(scoreline_counter_keys)):
    gs_and_gc = scoreline_counter_keys[score].split('-')
    result_type = "W"
    if gs_and_gc[0] < gs_and_gc[1]:
        result_type = "L"
    goal_diff_for_score = int(gs_and_gc[0]) - int(gs_and_gc[1])
    score_pct = round(((scoreline_counter_values[score] / games_nr) * 100),1)
    scoreline_and_pct.append([result_type,scoreline_counter_keys[score],score_pct,scoreline_counter_values[score],goal_diff_for_score])

scoreline_and_pct = sorted(scoreline_and_pct, key=lambda x: -x[2])

print(tabulate(scoreline_and_pct,
               headers=["Result", "Scoreline", "Occurrence %", "Occurrence", "Goal Diff."], numalign="right"))
print("\n")
"""

############

our_win_ratio = win_count / games_nr
our_loss_ratio = 1 - our_win_ratio
overtime_games_count = overtime_wins_count + overtime_losses_count
normaltime_wins_count = win_count - overtime_wins_count
normaltime_losses_count = loss_count - overtime_losses_count
normaltime_games_count = normaltime_wins_count + normaltime_losses_count

if normaltime_games_count > 0:
    normaltime_win_rate = normaltime_wins_count / normaltime_games_count
    normaltime_loss_rate = normaltime_losses_count / normaltime_games_count
    our_NT_win_ratio = normaltime_wins_count / normaltime_games_count
    our_NT_loss_ratio = normaltime_losses_count / normaltime_games_count
else:
    normaltime_win_rate = 0
    normaltime_loss_rate = 0
    our_NT_win_ratio = 0
    our_NT_loss_ratio = 0

if overtime_games_count > 0:
    overtime_win_rate = overtime_wins_count / overtime_games_count
    overtime_loss_rate = overtime_losses_count / overtime_games_count
    our_OT_win_ratio = overtime_wins_count / overtime_games_count
    our_OT_loss_ratio = overtime_losses_count / overtime_games_count
else:
    overtime_win_rate = 0
    overtime_loss_rate = 0
    our_OT_win_ratio = 0
    our_OT_loss_ratio = 0

result_data = [["Games", games_nr, normaltime_games_count, overtime_games_count],
               ["Win %", "%.2f" % (our_win_ratio * 100), "%.2f" % (normaltime_win_rate * 100),
                "%.2f" % (overtime_win_rate * 100)],
               ["Loss %", "%.2f" % (our_loss_ratio * 100), "%.2f" % (normaltime_loss_rate * 100),
                "%.2f" % (overtime_loss_rate * 100)],
               ["Wins", win_count, normaltime_wins_count, overtime_wins_count],
               ["Losses", loss_count, normaltime_losses_count, overtime_losses_count]
               ]

print(tabulate(result_data, headers=["STATS", "Overall", "Normaltime", "Overtime"], numalign="right"))

###########

my_x_coords = []
my_y_coords = []
my_z_coords = []

your_x_coords = []
your_y_coords = []
your_z_coords = []

ball_x_coords = []
ball_y_coords = []
ball_z_coords = []

file_counter = 0

# Only consider at most the last 10 games for positional heatmaps
game_print_list = []
for game in range(0, games_nr):
    if games_nr > 9:
        if game > (games_nr - 11):
            game_print_list.append(game)
    else:
        game_print_list.append(game)

for file in new_csv_files:
    if file_counter in game_print_list:
        with open(path_to_csv + file) as f:
            reader = csv.reader(f)
            my_list = list(reader)

        nrows = len(my_list)
        ncols = len(my_list[0])

        multiplier = 1
        if our_team_color[file_counter] == "O":
            multiplier = -1

        for col in range(ncols):
            for row in range(3, nrows):

                if my_list[row][col] != "":
                    if my_list[0][col] == my_name+"_pos_x":
                        my_x_c = int(my_list[row][col]) * multiplier
                        my_x_coords.append(my_x_c)
                    elif my_list[0][col] == my_name+"_pos_y":
                        my_y_c = int(my_list[row][col]) * multiplier
                        my_y_coords.append(my_y_c)
                    elif my_list[0][col] == my_name + "_pos_z":
                        my_z_c = int(my_list[row][col])
                        my_z_coords.append(my_z_c)

                if my_list[row][col] != "":
                    if my_list[0][col] == your_name + "_pos_x":
                        your_x_c = int(my_list[row][col]) * multiplier
                        your_x_coords.append(your_x_c)
                    elif my_list[0][col] == your_name + "_pos_y":
                        your_y_c = int(my_list[row][col]) * multiplier
                        your_y_coords.append(your_y_c)
                    elif my_list[0][col] == your_name + "_pos_z":
                        your_z_c = int(my_list[row][col])
                        your_z_coords.append(your_z_c)

                if my_list[row][col] != "":
                    if my_list[0][col] == "ball_pos_x":
                        ball_x_c = int(my_list[row][col]) * multiplier
                        ball_x_coords.append(ball_x_c)
                    elif my_list[0][col] == "ball_pos_y":
                        ball_y_c = int(my_list[row][col]) * multiplier
                        ball_y_coords.append(ball_y_c)
                    elif (my_list[0][col] == "ball_pos_z") or (my_list[0][col] == "ball_pos_z-GAME-WENT-OT"):
                        ball_z_c = int(my_list[row][col])
                        ball_z_coords.append(ball_z_c)
    file_counter += 1


n_plots = 21
widths = [1]
heights = [1] * n_plots
spec = fig.add_gridspec(ncols=1, nrows=n_plots, width_ratios=widths, height_ratios=heights)

pitch_min_x = 4500
pitch_min_y = -6300

pitch_max_x = pitch_min_x * -1
pitch_max_y = pitch_min_y * -1

ax1 = fig.add_subplot(spec[0, 0])  # results
ax1.bar(range(len(gd_array)), gd_array, color=result_color)
min_gd = min(gd_array)
max_gd = max(gd_array)
gd_lim = max(abs(min_gd), max_gd)
ax1.set_ylim(-gd_lim, gd_lim)
ax1.set_xlim(-1, len(gd_array))
ax1.axis("off")
plt.axhline(y=0, color='grey', linestyle=':')

for streak_game_num in streak_start_games:
    plt.axvline(x=streak_game_num - 0.5, color='grey', linestyle='-')

ax2 = fig.add_subplot(spec[1, 0], projection='3d')  # shot positions
ax2.set_xlabel("X Axis")
ax2.set_ylabel("Y Axis")
ax2.set_zlabel("Z Axis")
ax2.set_xlim(pitch_min_x, pitch_max_x)
ax2.set_ylim(pitch_min_y, pitch_max_y)
ax2.set_zlim(0, 2050)
ax2.scatter(my_goals_x, my_goals_y, my_goals_z, color=my_color, alpha=0.25, s=75)
ax2.scatter(your_goals_x, your_goals_y, your_goals_z, color=your_color, alpha=0.25, s=75)
ax2.scatter(their_goals_x, their_goals_y, their_goals_z, color=their_color, alpha=0.25, s=75)

ax2.scatter(my_misses_x, my_misses_y, my_misses_z, color=my_color, alpha=0.25, s=30, marker="x")
ax2.scatter(your_misses_x, your_misses_y, your_misses_z, color=your_color, alpha=0.25, s=30, marker="x")
ax2.scatter(their_misses_x, their_misses_y, their_misses_z, color=their_color, alpha=0.25, s=30, marker="x")


if side_view_3d_scatter:
    ax2.view_init(0, 180)

my_goal_count_per_game = my_goal_count / games_nr
your_goal_count_per_game = your_goal_count / games_nr
our_goal_count_per_game = our_goal_count / games_nr
their_goal_count_per_game = their_goal_count / games_nr

my_shot_count = (my_goal_count + my_miss_count)
your_shot_count = (your_goal_count + your_miss_count)
our_shot_count = (our_goal_count + our_miss_count)
their_shot_count = (their_goal_count + their_miss_count)

my_shot_count_per_game = (my_goal_count + my_miss_count) / games_nr
your_shot_count_per_game = (your_goal_count + your_miss_count) / games_nr
our_shot_count_per_game = (our_goal_count + our_miss_count) / games_nr
their_shot_count_per_game = (their_goal_count + their_miss_count) / games_nr

my_assist_count_per_game = my_assists_count / games_nr
your_assist_count_per_game = your_assists_count / games_nr
our_assist_count_per_game = our_assists_count / games_nr
their_assist_count_per_game = their_assists_count / games_nr

my_save_count_per_game = my_saves_count / games_nr
your_save_count_per_game = your_saves_count / games_nr
our_save_count_per_game = our_saves_count / games_nr
their_save_count_per_game = their_saves_count / games_nr

my_miss_count_per_game = my_miss_count / games_nr
your_miss_count_per_game = your_miss_count / games_nr
our_miss_count_per_game = our_miss_count / games_nr
their_miss_count_per_game = their_miss_count / games_nr

my_touches_per_game = my_touches_count / games_nr
your_touches_per_game = your_touches_count / games_nr
their_touches_per_game = their_touches_count / games_nr
our_touches_per_game = our_touches_count / games_nr

my_demos_per_game = my_demos_count / games_nr
your_demos_per_game = your_demos_count / games_nr
their_demos_per_game = their_demos_count / games_nr
our_demos_per_game = our_demos_count / games_nr

my_demos_conceded_per_game = my_demos_conceded_count / games_nr
your_demos_conceded_per_game = your_demos_conceded_count / games_nr
their_demos_conceded_per_game = their_demos_conceded_count / games_nr
our_demos_conceded_per_game = our_demos_conceded_count / games_nr

my_passes_per_game = my_passes_count / games_nr
your_passes_per_game = your_passes_count / games_nr
their_passes_per_game = their_passes_count / games_nr
our_passes_per_game = our_passes_count / games_nr

my_clears_per_game = my_clears_count / games_nr
your_clears_per_game = your_clears_count / games_nr
their_clears_per_game = their_clears_count / games_nr
our_clears_per_game = our_clears_count / games_nr

my_score_per_game = my_score_count / games_nr
your_score_per_game = your_score_count / games_nr
their_score_per_game = their_score_count / games_nr
our_score_per_game = our_score_count / games_nr

my_turnovers_per_game = my_turnovers_count / games_nr
your_turnovers_per_game = your_turnovers_count / games_nr
their_turnovers_per_game = their_turnovers_count / games_nr
our_turnovers_per_game = our_turnovers_count / games_nr

my_turnovers_won_per_game = my_turnovers_won_count / games_nr
your_turnovers_won_per_game = your_turnovers_won_count / games_nr
their_turnovers_won_per_game = their_turnovers_won_count / games_nr
our_turnovers_won_per_game = our_turnovers_won_count / games_nr

ax3 = fig.add_subplot(spec[2, 0])  # Results

sizes = [our_win_ratio, our_loss_ratio]
labels = "Win %", "Loss %"
ax3.pie(sizes, colors=[our_color, their_color], startangle=90, autopct='%1.1f%%', explode=(0.1, 0), shadow=True,
        textprops={'color': "black", 'bbox': dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
                   })
ax3.set_title(str(games_nr) + " Games:")

ax4 = fig.add_subplot(spec[3, 0])  # My heatmap
ax4.set_title(my_alias + "'s Positional Heatmap\n(Last " + str(len(game_print_list)) + " games)")
ax4.set_xlim(pitch_min_x, pitch_max_x)
ax4.set_ylim(pitch_min_y, pitch_max_y)
ax4.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax4.axis("off")
ax4.scatter(my_x_coords, my_y_coords, alpha=0.1, color=my_color, s=10)

ax5 = fig.add_subplot(spec[4, 0])  # Your heatmap
ax5.set_title(your_alias + "'s Positional Heatmap\n(Last " + str(len(game_print_list)) + " games)")
ax5.set_xlim(pitch_min_x, pitch_max_x)
ax5.set_ylim(pitch_min_y, pitch_max_y)
ax5.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax5.axis("off")
ax5.scatter(your_x_coords, your_y_coords, alpha=0.1, color=your_color, s=10)

ax12 = fig.add_subplot(spec[4, 0])  # Heatmap of the ball
ax12.set_title("Ball heatmap\n(Last " + str(len(game_print_list)) + " games)")
ax12.set_xlim(pitch_min_x, pitch_max_x)
ax12.set_ylim(pitch_min_y, pitch_max_y)
ax12.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax12.axis("off")
ax12.scatter(ball_x_coords, ball_y_coords, alpha=0.1, color="grey", s=10)

ax6 = fig.add_subplot(spec[5, 0])  # Team balance horizontal stacked bar chart

dic = {1.0: "Assists", 2.0: "Saves", 3.0: "Goals", 4.0: "Misses", 5.0: "Shots", 6.0: "Goals/Shot", 7.0: "Touches",
       8.0: "Demos", 9.0: "Demoed", 10.0: "Passes", 11.0: "Clears", 12.0: "Scores", 13.0: "Lost Ball", 14.0: "Won Ball"}

ticks = []

for num in dic:
    ticks.append(num)

ax6.set_yticks(ticks)

labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]

ax6.set_yticklabels(labels)
ax6.set_xticklabels("")
ax6.tick_params(bottom=False)  # remove the ticks

ax6.set_xlim(0, 1)

# ASSISTS
if our_assists_count > 0:
    my_assist_share = my_assists_count / our_assists_count
    your_assist_share = your_assists_count / our_assists_count
else:
    my_assist_share = 0
    your_assist_share = 0

ax6.barh(1, my_assist_share, color=my_color)
ax6.barh(1, your_assist_share, left=my_assist_share, color=your_color)

# SAVES
if our_saves_count > 0:
    my_save_share = my_saves_count / our_saves_count
    your_save_share = your_saves_count / our_saves_count
else:
    my_save_share = 0
    your_save_share = 0
ax6.barh(2, my_save_share, color=my_color)
ax6.barh(2, your_save_share, left=my_save_share, color=your_color)

# GOALS
if our_goal_count > 0:
    my_goal_share = my_goal_count / our_goal_count
    your_goal_share = your_goal_count / our_goal_count
else:
    my_goal_share = 0
    your_goal_share = 0
ax6.barh(3, my_goal_share, color=my_color)
ax6.barh(3, your_goal_share, left=my_goal_share, color=your_color)

# MISSES
if our_miss_count > 0:
    my_miss_share = my_miss_count / our_miss_count
    your_miss_share = your_miss_count / our_miss_count
else:
    my_miss_share = 0
    your_miss_share = 0
ax6.barh(4, my_miss_share, color=my_color)
ax6.barh(4, your_miss_share, left=my_miss_share, color=your_color)

# SHOTS
if (our_shot_count) > 0:
    my_shot_share = my_shot_count / our_shot_count
    your_shot_share = your_shot_count / our_shot_count
else:
    my_miss_share = 0
    your_miss_share = 0
ax6.barh(5, my_shot_share, color=my_color)
ax6.barh(5, your_shot_share, left=my_shot_share, color=your_color)

# GOAL/SHOT RATIO
if our_gs_ratio > 0:
    my_gs_ratio_share = my_gs_ratio / (my_gs_ratio+your_gs_ratio)
    your_gs_ratio_share = your_gs_ratio / (my_gs_ratio+your_gs_ratio)
else:
    my_gs_ratio_share = 0
    your_gs_ratio_share = 0
ax6.barh(6, my_gs_ratio_share, color=my_color)
ax6.barh(6, your_gs_ratio_share, left=my_gs_ratio_share, color=your_color)

# TOUCHES
if our_touches_count > 0:
    my_touch_share = my_touches_count / our_touches_count
    your_touch_share = your_touches_count / our_touches_count
else:
    my_touch_share = 0
    your_touch_share = 0
ax6.barh(7, my_touch_share, color=my_color)
ax6.barh(7, your_touch_share, left=my_touch_share, color=your_color)

# DEMOS
if our_demos_count > 0:
    my_demo_share = my_demos_count / our_demos_count
    your_demo_share = your_demos_count / our_demos_count
else:
    my_demo_share = 0
    your_demo_share = 0
ax6.barh(8, my_demo_share, color=my_color)
ax6.barh(8, your_demo_share, left=my_demo_share, color=your_color)

# GOT DEMOED
if our_demos_conceded_count > 0:
    my_demoed_share = my_demos_conceded_count / our_demos_conceded_count
    your_demoed_share = your_demos_conceded_count / our_demos_conceded_count
else:
    my_demoed_share = 0
    your_demoed_share = 0
ax6.barh(9, my_demoed_share, color=my_color)
ax6.barh(9, your_demoed_share, left=my_demoed_share, color=your_color)

# PASSES
if our_passes_count > 0:
    my_passes_share = my_passes_count / our_passes_count
    your_passes_share = your_passes_count / our_passes_count
else:
    my_passes_share = 0
    your_passes_share = 0
ax6.barh(10, my_passes_share, color=my_color)
ax6.barh(10, your_passes_share, left=my_passes_share, color=your_color)

# CLEARS
if our_clears_count > 0:
    my_clears_share = my_clears_count / our_clears_count
    your_clears_share = your_clears_count / our_clears_count
else:
    my_clears_share = 0
    your_clears_share = 0
ax6.barh(11, my_clears_share, color=my_color)
ax6.barh(11, your_clears_share, left=my_clears_share, color=your_color)

# SCORES
if our_score_count > 0:
    my_score_share = my_score_count / our_score_count
    your_score_share = your_score_count / our_score_count
else:
    my_score_share = 0
    your_score_share = 0
ax6.barh(12, my_score_share, color=my_color)
ax6.barh(12, your_score_share, left=my_score_share, color=your_color)

# TURNOVERS (LOST BALL)
if our_turnovers_count > 0:
    my_turnover_share = my_turnovers_count / our_turnovers_count
    your_turnover_share = your_turnovers_count / our_turnovers_count
else:
    my_turnover_share = 0
    your_turnover_share = 0
ax6.barh(13, my_turnover_share, color=my_color)
ax6.barh(13, your_turnover_share, left=my_turnover_share, color=your_color)

# TURNOVERS WON (WON BALL)
if our_turnovers_won_count > 0:
    my_turnovers_won_share = my_turnovers_won_count / our_turnovers_won_count
    your_turnovers_won_share = your_turnovers_won_count / our_turnovers_won_count
else:
    my_turnovers_won_share = 0
    your_turnovers_won_share = 0
ax6.barh(14, my_turnovers_won_share, color=my_color)
ax6.barh(14, your_turnovers_won_share, left=my_turnovers_won_share, color=your_color)

label_count = 0
for c in ax6.containers:
    # customize the label to account for cases when there might not be a bar section
    labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

    labels[0] = ""

    # assists
    if label_count == 0 and my_assist_count_per_game > 0:
        labels[0] = "%.2f" % my_assist_count_per_game
    if label_count == 1 and your_assist_count_per_game > 0:
        labels[0] = "%.2f" % your_assist_count_per_game

    # saves
    if label_count == 2 and my_save_count_per_game > 0:
        labels[0] = "%.2f" % my_save_count_per_game
    if label_count == 3 and your_save_count_per_game > 0:
        labels[0] = "%.2f" % your_save_count_per_game

    # goals
    if label_count == 4 and my_goal_count_per_game > 0:
        labels[0] = "%.2f" % my_goal_count_per_game
    if label_count == 5 and your_goal_count_per_game > 0:
        labels[0] = "%.2f" % your_goal_count_per_game

    # misses
    if label_count == 6 and my_miss_count_per_game > 0:
        labels[0] = "%.2f" % my_miss_count_per_game
    if label_count == 7 and your_miss_count_per_game > 0:
        labels[0] = "%.2f" % your_miss_count_per_game

    # shots
    if label_count == 8 and my_shot_count_per_game > 0:
        labels[0] = "%.2f" % my_shot_count_per_game
    if label_count == 9 and your_shot_count_per_game > 0:
        labels[0] = "%.2f" % your_shot_count_per_game

    # goal / shot ratio
    if label_count == 10 and my_gs_ratio > 0:
        labels[0] = "%.2f" % my_gs_ratio
    if label_count == 11 and your_gs_ratio > 0:
        labels[0] = "%.2f" % your_gs_ratio

    # touches
    if label_count == 12 and my_touches_per_game > 0:
        labels[0] = "%.2f" % my_touches_per_game
    if label_count == 13 and your_touches_per_game > 0:
        labels[0] = "%.2f" % your_touches_per_game

    # demos
    if label_count == 14 and my_demos_per_game > 0:
        labels[0] = "%.2f" % my_demos_per_game
    if label_count == 15 and your_demos_per_game > 0:
        labels[0] = "%.2f" % your_demos_per_game

    # demos conceded
    if label_count == 16 and my_demos_conceded_per_game > 0:
        labels[0] = "%.2f" % my_demos_conceded_per_game
    if label_count == 17 and your_demos_conceded_per_game > 0:
        labels[0] = "%.2f" % your_demos_conceded_per_game

    # passes
    if label_count == 18 and my_passes_per_game > 0:
        labels[0] = "%.2f" % my_passes_per_game
    if label_count == 19 and your_passes_per_game > 0:
        labels[0] = "%.2f" % your_passes_per_game

    # clears
    if label_count == 20 and my_clears_per_game > 0:
        labels[0] = "%.2f" % my_clears_per_game
    if label_count == 21 and your_clears_per_game > 0:
        labels[0] = "%.2f" % your_clears_per_game

    # scores
    if label_count == 22 and my_score_per_game > 0:
        labels[0] = "%.0f" % my_score_per_game
    if label_count == 23 and your_score_per_game > 0:
        labels[0] = "%.0f" % your_score_per_game

    # lost ball
    if label_count == 24 and my_turnovers_per_game > 0:
        labels[0] = "%.2f" % my_turnovers_per_game
    if label_count == 25 and your_turnovers_per_game > 0:
        labels[0] = "%.2f" % your_turnovers_per_game

    # won ball
    if label_count == 26 and my_turnovers_won_per_game > 0:
        labels[0] = "%.2f" % my_turnovers_won_per_game
    if label_count == 27 and your_turnovers_won_per_game > 0:
        labels[0] = "%.2f" % your_turnovers_won_per_game

    # set the bar label
    ax6.bar_label(c, labels=labels, label_type='center', color="white")
    label_count += 1
plt.axvline(x=0.5, color='white', linestyle='-', alpha=0.5, linewidth=1)
ax6.set_title(my_alias + " - " + your_alias + " (per Game)")

ax7 = fig.add_subplot(spec[6, 0])  # Horizontal stacked bar chart (us vs opponent)

dic = {1.0: "Assists", 2.0: "Saves", 3.0: "Goals", 4.0: "Misses", 5.0: "Shots", 6.0: "Goals/Shot", 7.0: "Touches",
       8.0: "Demos", 9.0: "Passes", 10.0: "Clears", 11.0: "Scores", 12.0: "Won Ball"}

ticks = []

for num in dic:
    ticks.append(num)

ax7.set_yticks(ticks)

labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]
ax7.set_yticklabels(labels)
ax7.set_xticklabels("")
ax7.tick_params(bottom=False)  # remove the ticks

ax7.set_xlim(0, 1)

# cumulative stats
total_assists_count = our_assists_count + their_assists_count
total_saves_count = our_saves_count + their_saves_count
total_goals_count = our_goal_count + their_goal_count
total_misses_count = our_miss_count + their_miss_count
total_shots_count = our_shot_count + their_shot_count
total_gs_ratio = our_gs_ratio + their_gs_ratio
total_touches_count = our_touches_count + their_touches_count
total_demos_count = our_demos_count + their_demos_count
total_passes_count = our_passes_count + their_passes_count
total_clears_count = our_clears_count + their_clears_count
total_score_count = our_score_count + their_score_count
total_turnovers_won_count = our_turnovers_won_count + their_turnovers_won_count

# ASSISTS
if total_assists_count > 0:
    our_assist_share = our_assists_count / total_assists_count
    their_assist_share = their_assists_count / total_assists_count
else:
    our_assist_share = 0
    their_assist_share = 0
ax7.barh(1, our_assist_share, color=our_color)
ax7.barh(1, their_assist_share, left=our_assist_share, color=their_color)

# SAVES
if total_saves_count > 0:
    our_save_share = our_saves_count / total_saves_count
    their_save_share = their_saves_count / total_saves_count
else:
    our_save_share = 0
    their_save_share = 0
ax7.barh(2, our_save_share, color=our_color)
ax7.barh(2, their_save_share, left=our_save_share, color=their_color)

# GOALS
if total_goals_count > 0:
    our_goal_share = our_goal_count / total_goals_count
    their_goal_share = their_goal_count / total_goals_count
else:
    our_goal_share = 0
    their_goal_share = 0
ax7.barh(3, our_goal_share, color=our_color)
ax7.barh(3, their_goal_share, left=our_goal_share, color=their_color)

# MISSES
if total_misses_count > 0:
    our_miss_share = our_miss_count / total_misses_count
    their_miss_share = their_miss_count / total_misses_count
else:
    our_miss_share = 0
    their_miss_share = 0
ax7.barh(4, our_miss_share, color=our_color)
ax7.barh(4, their_miss_share, left=our_miss_share, color=their_color)

# SHOTS
if total_shots_count > 0:
    our_shot_share = our_shot_count / total_shots_count
    their_shot_share = their_shot_count / total_shots_count
else:
    our_shot_share = 0
    their_shot_share = 0
ax7.barh(5, our_shot_share, color=our_color)
ax7.barh(5, their_shot_share, left=our_shot_share, color=their_color)

# GOAL/SHOT RATIO
if total_gs_ratio > 0:
    our_gs_ratio_share = our_gs_ratio / total_gs_ratio
    their_gs_ratio_share = their_gs_ratio / total_gs_ratio
else:
    our_gs_ratio_share = 0
    their_gs_ratio_share = 0
ax7.barh(6, our_gs_ratio_share, color=our_color)
ax7.barh(6, their_gs_ratio_share, left=our_gs_ratio_share, color=their_color)

# TOUCHES
if total_touches_count > 0:
    our_touch_share = our_touches_count / total_touches_count
    their_touch_share = their_touches_count / total_touches_count
else:
    our_touch_share = 0
    their_touch_share = 0
ax7.barh(7, our_touch_share, color=our_color)
ax7.barh(7, their_touch_share, left=our_touch_share, color=their_color)

# DEMOS
if total_demos_count > 0:
    our_demo_share = our_demos_count / total_demos_count
    their_demo_share = their_demos_count / total_demos_count
else:
    our_demo_share = 0
    their_demo_share = 0
ax7.barh(8, our_demo_share, color=our_color)
ax7.barh(8, their_demo_share, left=our_demo_share, color=their_color)

# PASSES
if total_passes_count > 0:
    our_pass_share = our_passes_count / total_passes_count
    their_pass_share = their_passes_count / total_passes_count
else:
    our_pass_share = 0
    their_pass_share = 0
ax7.barh(9, our_pass_share, color=our_color)
ax7.barh(9, their_pass_share, left=our_pass_share, color=their_color)

# CLEARS
if total_clears_count > 0:
    our_clear_share = our_clears_count / total_clears_count
    their_clear_share = their_clears_count / total_clears_count
else:
    our_clear_share = 0
    their_clear_share = 0
ax7.barh(10, our_clear_share, color=our_color)
ax7.barh(10, their_clear_share, left=our_clear_share, color=their_color)

# SCORES
if total_score_count > 0:
    our_score_share = our_score_count / total_score_count
    their_score_share = their_score_count / total_score_count
else:
    our_score_share = 0
    their_score_share = 0
ax7.barh(11, our_score_share, color=our_color)
ax7.barh(11, their_score_share, left=our_score_share, color=their_color)

# TURNOVERS WON (WON BALL)
if total_turnovers_won_count > 0:
    our_turnovers_won_share = our_turnovers_won_count / total_turnovers_won_count
    their_turnovers_won_share = their_turnovers_won_count / total_turnovers_won_count
else:
    our_turnovers_won_share = 0
    their_turnovers_won_share = 0
ax7.barh(12, our_turnovers_won_share, color=our_color)
ax7.barh(12, their_turnovers_won_share, left=our_turnovers_won_share, color=their_color)

label_count = 0
for c in ax7.containers:
    # customize the label to account for cases when there might not be a bar section
    labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

    # assists
    if label_count == 0 and our_assist_count_per_game > 0:
        labels[0] = "%.2f" % our_assist_count_per_game
    if label_count == 1 and their_assist_count_per_game > 0:
        labels[0] = "%.2f" % their_assist_count_per_game

    # saves
    if label_count == 2 and our_save_count_per_game > 0:
        labels[0] = "%.2f" % our_save_count_per_game
    if label_count == 3 and their_save_count_per_game > 0:
        labels[0] = "%.2f" % their_save_count_per_game

    # goals
    if label_count == 4 and our_goal_count_per_game > 0:
        labels[0] = "%.2f" % our_goal_count_per_game
    if label_count == 5 and their_goal_count_per_game > 0:
        labels[0] = "%.2f" % their_goal_count_per_game

    # misses
    if label_count == 6 and our_miss_count_per_game > 0:
        labels[0] = "%.2f" % our_miss_count_per_game
    if label_count == 7 and their_miss_count_per_game > 0:
        labels[0] = "%.2f" % their_miss_count_per_game

    # shots
    if label_count == 8 and our_shot_count_per_game > 0:
        labels[0] = "%.2f" % our_shot_count_per_game
    if label_count == 9 and their_shot_count_per_game > 0:
        labels[0] = "%.2f" % their_shot_count_per_game

    # goal / shot ratio
    if label_count == 10 and our_gs_ratio > 0:
        labels[0] = "%.2f" % our_gs_ratio
    if label_count == 11 and their_gs_ratio > 0:
        labels[0] = "%.2f" % their_gs_ratio

    # touches
    if label_count == 12 and our_touches_per_game > 0:
        labels[0] = "%.2f" % our_touches_per_game
    if label_count == 13 and their_touches_per_game > 0:
        labels[0] = "%.2f" % their_touches_per_game

    # demos
    if label_count == 14 and our_demos_per_game > 0:
        labels[0] = "%.2f" % our_demos_per_game
    if label_count == 15 and their_demos_per_game > 0:
        labels[0] = "%.2f" % their_demos_per_game

    # passes
    if label_count == 16 and our_passes_per_game > 0:
        labels[0] = "%.2f" % our_passes_per_game
    if label_count == 17 and their_passes_per_game > 0:
        labels[0] = "%.2f" % their_passes_per_game

    # clears
    if label_count == 18 and our_clears_per_game > 0:
        labels[0] = "%.2f" % our_clears_per_game
    if label_count == 19 and their_clears_per_game > 0:
        labels[0] = "%.2f" % their_clears_per_game

    # scores
    if label_count == 20 and our_score_per_game > 0:
        labels[0] = "%.0f" % our_score_per_game
    if label_count == 21 and their_score_per_game > 0:
        labels[0] = "%.0f" % their_score_per_game

    # won ball
    if label_count == 22 and our_turnovers_won_per_game > 0:
        labels[0] = "%.2f" % our_turnovers_won_per_game
    if label_count == 23 and their_turnovers_won_per_game > 0:
        labels[0] = "%.2f" % their_turnovers_won_per_game

    # set the bar label
    ax7.bar_label(c, labels=labels, label_type='center', color="white")
    label_count += 1

plt.axvline(x=0.5, color='white', linestyle='-', alpha=0.5, linewidth=1)
ax7.set_title("Us - Opponents (per Game)")

new_result_array_num_up = []
new_result_array_num_down = []

for entry in range(0, len(their_goals_over_time)):
    their_goals_over_time[entry] *= -1

ax8 = fig.add_subplot(spec[0, 0])  # our goals over time
ax8.set_xlim(0.5, games_nr + 0.5)

# TODO: Move x tick labels so they only show integers

limit1 = min(their_goals_over_time)
our_goals_over_time = [your_goals_over_time[x] + my_goals_over_time[x] for x in range(games_nr)]
limit2 = max(our_goals_over_time)

if abs(limit1) > limit2:
    limit = abs(limit1)

limit = max(abs(limit1), limit2)
ax8.set_ylim(-limit, limit)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax8.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25, ec="grey")
ax8.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25, ec="grey")

ax8.bar(range(1, games_nr + 1), my_goals_over_time, color=my_color, width=1, ec="black")
ax8.bar(range(1, games_nr + 1), your_goals_over_time, color=your_color, bottom=my_goals_over_time, width=1, ec="black")
ax8.bar(range(1, games_nr + 1), their_goals_over_time, color=their_color, width=1, ec="black")
for streak_game_num in streak_start_games:
    plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
ax8.set_ylabel("GOALS", rotation="horizontal", ha="center", va="center", labelpad=35)

for entry in range(0, len(their_shots_over_time)):
    their_shots_over_time[entry] *= -1

ax9 = fig.add_subplot(spec[0, 0])  # our goals over time
ax9.set_xlim(0.5, games_nr + 0.5)
limit1 = min(their_shots_over_time)
our_shots_over_time = [your_shots_over_time[x] + my_shots_over_time[x] for x in range(games_nr)]
limit2 = max(our_shots_over_time)
limit = max(abs(limit1), limit2)
ax9.set_ylim(-limit, limit)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax9.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25, ec="grey")
ax9.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25, ec="grey")

ax9.bar(range(1, games_nr + 1), my_shots_over_time, color=my_color, width=1, ec="black")
ax9.bar(range(1, games_nr + 1), your_shots_over_time, color=your_color, bottom=my_shots_over_time, width=1, ec="black")
ax9.bar(range(1, games_nr + 1), their_shots_over_time, color=their_color, width=1, ec="black")
ax9.set_xticklabels("")
for streak_game_num in streak_start_games:
    plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
ax9.set_ylabel("SHOTS", rotation="horizontal", ha="center", va="center", labelpad=35)

for entry in range(0, len(their_saves_over_time)):
    their_saves_over_time[entry] *= -1

ax10 = fig.add_subplot(spec[0, 0])  # our saves over time
ax10.set_xlim(0.5, games_nr + 0.5)
limit1 = min(their_saves_over_time)
our_saves_over_time = [your_saves_over_time[x] + my_saves_over_time[x] for x in range(games_nr)]
limit2 = max(our_saves_over_time)
limit = max(abs(limit1), limit2)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax10.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25, ec="grey")
ax10.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25, ec="grey")

ax10.set_ylim(-limit, limit)
ax10.bar(range(1, games_nr + 1), my_saves_over_time, color=my_color, width=1, ec="black")
ax10.bar(range(1, games_nr + 1), your_saves_over_time, color=your_color, bottom=my_saves_over_time, width=1, ec="black")
ax10.bar(range(1, games_nr + 1), their_saves_over_time, color=their_color, width=1, ec="black")
ax10.set_xticklabels("")
for streak_game_num in streak_start_games:
    plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
ax10.set_ylabel("SAVES", rotation="horizontal", ha="center", va="center", labelpad=35)

for entry in range(0, len(their_assists_over_time)):
    their_assists_over_time[entry] *= -1

ax11 = fig.add_subplot(spec[0, 0])  # our assists over time
ax11.set_xlim(0.5, games_nr + 0.5)
limit1 = min(their_assists_over_time)
our_assists_over_time = [your_assists_over_time[x] + my_assists_over_time[x] for x in range(games_nr)]
limit2 = max(our_assists_over_time)
limit = max(abs(limit1), limit2)
ax11.set_ylim(-limit, limit)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax11.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25, ec="grey")
ax11.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25, ec="grey")

ax11.bar(range(1, games_nr + 1), my_assists_over_time, color=my_color, width=1, ec="black")
ax11.bar(range(1, games_nr + 1), your_assists_over_time, color=your_color, bottom=my_assists_over_time, width=1,
         ec="black")
ax11.bar(range(1, games_nr + 1), their_assists_over_time, color=their_color, width=1, ec="black")
ax11.set_xticklabels("")
for streak_game_num in streak_start_games:
    plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
ax11.set_ylabel("ASSISTS", rotation="horizontal", ha="center", va="center", labelpad=35)

ax13 = fig.add_subplot(spec[4, 0])  # Heatmap of Allan's goals
ax13.hist2d(my_shots_x + [pitch_min_x] + [pitch_max_x], my_shots_y + [pitch_min_y] + [pitch_max_y], bins=8,
            cmap="Greys", alpha=0.25)
ax13.scatter(my_goals_x, my_goals_y, alpha=0.7, color=my_color, s=10)
ax13.set_xlim(pitch_min_x, pitch_max_x)
ax13.set_ylim(pitch_min_y, pitch_max_y)
ax13.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax13.axis("off")
ax13.set_title(my_alias + "'s Shot & Goal Heatmap")

ax14 = fig.add_subplot(spec[4, 0])  # Heatmap of Sertalp's goals
ax14.hist2d(your_shots_x + [pitch_min_x] + [pitch_max_x], your_shots_y + [pitch_min_y] + [pitch_max_y], bins=8,
            cmap="Greys", alpha=0.25)
ax14.scatter(your_goals_x, your_goals_y, alpha=0.7, color=your_color, s=10)
ax14.set_xlim(pitch_min_x, pitch_max_x)
ax14.set_ylim(pitch_min_y, pitch_max_y)
ax14.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax14.axis("off")
ax14.set_title(your_alias + "'s Shot & Goal Heatmap")

ax15 = fig.add_subplot(spec[4, 0])  # Heatmap of our team's goals
ax15.hist2d(your_shots_x + [pitch_min_x] + [pitch_max_x] + my_shots_x,
            your_shots_y + [pitch_min_y] + [pitch_max_y] + my_shots_y, bins=8, cmap="Greys", alpha=0.25)
ax15.scatter(your_goals_x + my_goals_x, your_goals_y + my_goals_y, alpha=0.7, color=our_color, s=10)
ax15.set_xlim(pitch_min_x, pitch_max_x)
ax15.set_ylim(pitch_min_y, pitch_max_y)
ax15.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax15.axis("off")
ax15.set_title("Our Shot & Goal Heatmap")

ax16 = fig.add_subplot(spec[4, 0])  # Heatmap of opponent's goals
ax16.hist2d(their_shots_x + [pitch_min_x] + [pitch_max_x], their_shots_y + [pitch_min_y] + [pitch_max_y], bins=8,
            cmap="Greys", alpha=0.25)
ax16.scatter(their_goals_x, their_goals_y, alpha=0.7, color=their_color, s=10)
ax16.set_xlim(pitch_min_x, pitch_max_x)
ax16.set_ylim(pitch_min_y, pitch_max_y)
ax16.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=0.5)
ax16.axis("off")
ax16.set_title("Opponent's Shot & Goal Heatmap")

ax17 = fig.add_subplot(spec[2, 0])  # Overtime Results
sizes = [our_OT_win_ratio, our_OT_loss_ratio]
labels = "Win %", "Loss %"
ax17.pie(sizes, colors=[our_color, their_color], startangle=90, autopct='%1.1f%%', explode=(0.1, 0), shadow=True,
         normalize=False,
         textprops={'color': "black", 'bbox': dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
                    })
ax17.set_title(str(overtime_losses_count + overtime_wins_count) + " Overtime")
# TODO: handle FFs

ax18 = fig.add_subplot(spec[2, 0])  # Overtime Results

sizes = [our_NT_win_ratio, our_NT_loss_ratio]
labels = "Win %", "Loss %"
ax18.pie(sizes, colors=[our_color, their_color], startangle=90, autopct='%1.1f%%', explode=(0.1, 0), shadow=True,
         normalize=False,
         textprops={'color': "black", 'bbox': dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
                    })
ax18.set_title(str(normaltime_games_count) + " Normaltime")
# TODO: handle FFs


ax19 = fig.add_subplot(spec[2, 0])  # Goal Difference Distribution
gd_counter = Counter(normaltime_gd_array)
gd_counter_keys = list(gd_counter.keys())
gd_counter_values = list(gd_counter.values())

neg_gd = []
pos_gd = []
neg_val = []
pos_val = []

sorted_gd_counter_values = [x for _, x in sorted(zip(gd_counter_keys, gd_counter_values))]
counter_col = []

if len(gd_counter_keys) > 0:
    min_gd = min(gd_counter_keys)
    max_gd = max(gd_counter_keys)

else:
    min_gd = 0
    max_gd = 0

new_min_gd = min_gd
new_max_gd = max_gd

if abs(min_gd) != abs(max_gd):
    if abs(min_gd) > abs(max_gd):
        new_min_gd = min_gd
        new_max_gd = min_gd * -1

    elif abs(max_gd) > abs(min_gd):
        new_min_gd = max_gd * -1
        new_max_gd = max_gd

new_gd_counter_keys = []
new_gd_counter_values = []
for gd in range(new_min_gd, new_max_gd + 1):
    new_gd_counter_keys.append(gd)
    new_gd_counter_values.append(0)

for gd in range(0, len(gd_counter_keys)):
    if gd_counter_keys[gd] in new_gd_counter_keys:
        for new_gd in range(0, len(new_gd_counter_keys)):
            if new_gd_counter_keys[new_gd] == gd_counter_keys[gd]:
                new_gd_counter_values[new_gd] = gd_counter_values[gd]

sorted_gd_counter_values = [x for _, x in sorted(zip(new_gd_counter_keys, new_gd_counter_values))]

for gd in new_gd_counter_keys:
    if gd < 0:
        counter_col.append(their_color)
    if gd == 0:
        counter_col.append("black")
    if gd > 0:
        counter_col.append(our_color)

sorted_gd_counter_pct = []
for gd in sorted_gd_counter_values:
    sorted_gd_counter_pct.append(gd / games_nr)

overtime_pcts = []
for gd in new_gd_counter_keys:
    if gd != -1 and gd != 1:
        overtime_pcts.append(0)
    else:
        if gd == 1:
            overtime_pcts.append(overtime_wins_count / games_nr)

        if gd == -1:
            overtime_pcts.append(overtime_losses_count / games_nr)

overall_pcts = []
for pct in range(0, len(overtime_pcts)):
    overall_pcts.append(overtime_pcts[pct] + sorted_gd_counter_pct[pct])


# Round the max y limit of the bar chart to the next multiple of 0.05 (5%)
max_y_lim = max(overall_pcts) + (0.05 - max(overall_pcts)) % 0.05
if max_y_lim > 1:
    max_y_lim = 1

for gd in new_gd_counter_keys:
    if len(new_gd_counter_keys) > 1:
        if gd < 0:
            neg_gd.append(gd)
            neg_val.append(new_gd_counter_values[gd])
        if gd > 0:
            pos_gd.append(gd)
            pos_val.append(new_gd_counter_values[gd])
    else:
        if gd < 0:
            neg_gd.append(gd)
            neg_val.append(new_gd_counter_values[0])
        if gd > 0:
            pos_gd.append(gd)
            pos_val.append(new_gd_counter_values[0])

ax19.set_xlim(min(new_gd_counter_keys) - 0.5, max(new_gd_counter_keys) + 0.5)
ax19.set_xticks(ticks=new_gd_counter_keys)
ax19.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0, symbol='%', is_latex=False))
ax19.set_ylim(0, max_y_lim)

ax19.bar(neg_gd, max_y_lim, color=their_color, width=1, alpha=0.25)
ax19.bar(pos_gd, max_y_lim, color=our_color, width=1, alpha=0.25)

ax19.bar(new_gd_counter_keys, sorted_gd_counter_pct, width=1, ec="black", color=counter_col)
ax19.bar(new_gd_counter_keys, overtime_pcts, width=1, ec="black", color="grey", bottom=sorted_gd_counter_pct)

ax19.set_xlabel("Goal Difference")
ax19.set_ylabel("Games")
plt.axvline(x=0, color='grey', linestyle=':')

ax19.set_title("Goal Difference Distribution")

#########

ax20 = fig.add_subplot(spec[2, 0])  # Goals Scored Distribution
ax21 = fig.add_subplot(spec[2, 0])  # Goals Conceded Distribution

gs_counter = Counter(gs_array)
gs_counter_keys = list(gs_counter.keys())
gs_counter_values = list(gs_counter.values())

gc_counter = Counter(gc_array)
gc_counter_keys = list(gc_counter.keys())
gc_counter_values = list(gc_counter.values())

gs_counter_pct = []
for gs in gs_counter_values:
    gs_counter_pct.append((gs / games_nr))

gc_counter_pct = []
for gc in gc_counter_values:
    gc_counter_pct.append((gc / games_nr))

ax20.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0, symbol='%', is_latex=False))
ax20.set_xlim(min(gc_counter_keys + gs_counter_keys) - 0.5, max(gc_counter_keys + gs_counter_keys) + 0.5)
ax21.set_xlim(min(gc_counter_keys + gs_counter_keys) - 0.5, max(gc_counter_keys + gs_counter_keys) + 0.5)
ax21.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=0, symbol='%', is_latex=False))

# Round the max y limit of the bar chart to the next multiple of 0.05 (5%)
gs_gc_max_pct = max(max(gs_counter_pct), max(gc_counter_pct))
max_y_lim = gs_gc_max_pct + ((0.05 - gs_gc_max_pct) % 0.05)
if max_y_lim > 1:
    max_y_lim = 1
ax20.set_ylim(0, max_y_lim)
ax21.set_ylim(0, max_y_lim)

# reverse y-axis of goals conceded
ax21 = plt.gca()
ax21.set_ylim(ax21.get_ylim()[::-1])

keys_to_use = []

min_gc_or_gs_keys = min(min(gc_counter_keys), min(gs_counter_keys))
max_gc_or_gs_keys = max(max(gc_counter_keys), max(gs_counter_keys))

for x in range(min_gc_or_gs_keys, max_gc_or_gs_keys + 1):
    keys_to_use.append(x)

ax20.set_xticks(keys_to_use)
ax21.set_xticks(keys_to_use)

ax20.bar(keys_to_use, max_y_lim, color=our_color, width=1, alpha=0.25)
ax20.bar(gs_counter_keys, gs_counter_pct, width=1, ec="black", color=our_color)

ax21.bar(keys_to_use, max_y_lim, color=their_color, width=1, alpha=0.25)
ax21.bar(gc_counter_keys, gc_counter_pct, width=1, ec="black", color=their_color)

ax20.set_ylabel("Games")
ax21.set_ylabel("Games")
ax21.tick_params(axis="x", bottom=False, top=True, labelbottom=False, labeltop=False)
ax20.set_title("Goals Scored & Conceded Distribution")

ax1.set_position([0, 0.88, 1, 0.1])
ax2.set_position([0.1, 0.1, 1, 0.65])  # 3D Scatterplot

ax3.set_position([0.53, 0.75, 0.075, 0.075])  # Results pie chart
ax17.set_position([0.57, 0.75, 0.075, 0.075])  # OT Results pie chart
ax18.set_position([0.61, 0.75, 0.075, 0.075])  # NT Results pie chart

ax19.set_position([0.39, 0.5, 0.09, 0.325])  # Goal Difference Distribution chart
ax20.set_position([0.39, 0.275, 0.09, 0.15])  # Goals Scored Distribution chart
ax21.set_position([0.39, 0.1, 0.09, 0.15])  # Goals Conceded Distribution chart

ax4.set_position([0.75, 0.55, 0.06, 0.24])  # Allan's positional heatmap
ax12.set_position([0.825, 0.55, 0.06, 0.24])  # Heatmap of the ball
ax5.set_position([0.9, 0.55, 0.06, 0.24])  # Sertalp's positional heatmap
ax13.set_position([0.03, 0.5, 0.08, 0.32])  # Allan's shot & goal heatmap

ax6.set_position([0.15, 0.5, 0.1, 0.32])  # Horizontal Bar Chart (Allan vs Sertalp)
ax14.set_position([0.28, 0.5, 0.08, 0.32])  # Sertalp's shot & goal heatmap

ax15.set_position([0.03, 0.1, 0.08, 0.32])  # Our shot & goal heatmap
ax7.set_position([0.15, 0.1, 0.1, 0.32])  # Horizontal Bar Chart (Us vs Opponent)
ax16.set_position([0.28, 0.1, 0.08, 0.32])  # Opponent's shot & goal heatmap

ax8.set_position([0.75, 0.05, 0.21, 0.1])  # Goals over time
ax9.set_position([0.75, 0.155, 0.21, 0.1])  # Shots over time
ax10.set_position([0.75, 0.26, 0.21, 0.1])  # Saves over time
ax11.set_position([0.75, 0.365, 0.21, 0.1])  # Assists over time

executionTime = (time.time() - startTime)
print('\n\nExecution time in seconds: ', "%.2f" % executionTime)
plt.show()
