# TODO: split ground and aerial heatmap based on z values
# TODO: calculate how long the ball is in our half vs. the opponent's half
# TODO: detect forfeits
# TODO: detect overtime without having to load CSVs (CSVs aren't being used for anything else other than that right now)
# TODO: fix issues with GD chart when there is only 1 game and it's an overtime game
# TODO: fix axes on charts which show game numbers to only show ints and not floats
# TODO: handle own-goals (add stats for own goals scored)
# TODO: decide whether to plot "non-shot" goals in the 4 goal heatmaps
# TODO: plot assists (maybe highlight assisted goals in a different color in the 4 goal heatmaps)
# TODO: add a check to see whether there are any games to check (i.e. indicate error if no games found)

# TODO: Add corresponding matches to records.tsv and replays [WIP] ---> need frames in /xg_out/ files
# TODO: Link dashboard match URLs next to where replays are added
# TODO: Add average expected win % to streak files
# TODO: Add luck % (win % - expected win %)
# TODO: Go over accuracy of record replays ---> some discrepancies (Allan's lowest shot game)

import csv
import json
import math
import os
import shutil
import time
from collections import Counter
from statistics import mean
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from tabulate import tabulate
from astropy.convolution.kernels import Gaussian2DKernel
from astropy.convolution import convolve
from numpy.lib.stride_tricks import sliding_window_view
from colorama import Fore, Back, Style
from PIL import Image

startTime = time.time()

check_new = False  # Only processes new files (in separate directory)
show_xg_scorelines = False  # Shows xG scorelines and normal scorelines and replay names of games
save_and_crop = True  # Saves an image of the dashboard and then crops charts into their own images


def link_replay(matchID, frame, showTimestamp):
    replay_base_url = "https://ballchasing.com/replay/"
    notimestamp_text = "#watch"
    timestamp_text = "#watch?t="

    if ".json" in matchID:
        matchID = matchID.replace(".json","")

    if ".csv" in matchID:
        matchID = matchID.replace(".csv","")

    if showTimestamp:
        convertedTime = round((int(frame) / 27.5 - 3), 2)
        return replay_base_url + matchID + timestamp_text + str(convertedTime) + "s"
    else:
        return replay_base_url + matchID + notimestamp_text


# Program runs twice - once to update using all games, and another time to update using the latest streak of games
for i in range(0, 2):
    # On second iteration, only process new files
    if i == 0:
        print("Considering all games...\n")
        goal_scatter_alpha = 0.25

    if i == 1:
        check_new = True
        show_xg_scorelines = True
        print("\n\n\nConsidering newest games...\n")
        goal_scatter_alpha = 0.5

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

    bg_img = plt.imread("../simple-pitch.png")

    if check_new:
        path_to_json = '../data/json_new/'
        path_to_tables = '../data/tables/latest_streak/'
        path_to_charts = '../data/charts/latest_streak/'
    else:
        path_to_json = '../data/json/'
        path_to_tables = '../data/tables/'
        path_to_charts = '../data/charts/'

    path_to_untrimmed_csv = '../data/dataframe/'
    path_to_csv = '../data/dataframe_trimmed/'
    path_to_xg = '../data/xg_out/'

    if not os.path.exists(path_to_tables):
        os.makedirs(path_to_tables)

    if not os.path.exists(path_to_charts):
        os.makedirs(path_to_charts)

    json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]

    json_files_2v2 = []
    file_counter = 0
    file_time = []

    # Only keep RANKED_DOUBLES games
    for file in json_files:
        # exclude abandoned game
        if file != "9e4c5030-ff84-49b5-b32f-2e4d585fd44e.json":
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

        local_time = data["gameMetadata"]["time"]

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
        local_time = 0

        local_time = data["gameMetadata"]["time"]
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
    your_shots_distancetogoal = []
    our_shots_distancetogoal = []

    my_id = ""
    your_id = ""

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

    my_dribbles_count = 0
    your_dribbles_count = 0
    their_dribbles_count = 0

    my_aerials_count = 0
    your_aerials_count = 0
    their_aerials_count = 0

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

    win_chance_per_game = []
    total_win_chance = 0

    loss_chance_per_game = []

    # positional tendencies
    my_pos_tendencies = [0] * 23
    your_pos_tendencies = [0] * 23
    # columns: time stats...
    # 0 - ground
    # 1 - low in air
    # 2 - high in air
    # 3 - defending half
    # 4 - attacking half
    # 5 - defending third
    # 6 - neutral third
    # 7 - attacking third
    # 8 - behind ball
    # 9 - in front of ball
    # 10 - near wall
    # 11 - in corner
    # 12 - on wall
    # 13 - full boost
    # 14 - low boost
    # 15 - no boost
    # 16 - closest to ball
    # 17 - close to ball
    # 18 - furthest from ball
    # 19 - slow speed
    # 20 - boost speed
    # 21 - supersonic
    # 22 - carrying ball

    my_total_xg = 0
    your_total_xg = 0
    their_total_xg = 0

    my_shot_xg = 0
    your_shot_xg = 0
    their_shot_xg = 0

    my_nonshot_xg = 0
    your_nonshot_xg = 0
    their_nonshot_xg = 0

    my_goal_xg = 0
    your_goal_xg = 0
    their_goal_xg = 0

    my_xg_over_time = []
    your_xg_over_time = []
    their_xg_over_time = []

    my_shot_xg_over_time = []
    your_shot_xg_over_time = []
    their_shot_xg_over_time = []

    my_nonshot_xg_over_time = []
    your_nonshot_xg_over_time = []
    their_nonshot_xg_over_time = []

    my_xg_per_shot_goal_list = []
    your_xg_per_shot_goal_list = []
    their_xg_per_shot_goal_list = []

    my_xg_per_nonshot_goal_list = []
    your_xg_per_nonshot_goal_list = []
    their_xg_per_nonshot_goal_list = []

    my_xg_per_miss_from_shot_list = []
    your_xg_per_miss_from_shot_list = []
    their_xg_per_miss_from_shot_list = []

    my_xg_per_miss_from_nonshot_list = []
    your_xg_per_miss_from_nonshot_list = []
    their_xg_per_miss_from_nonshot_list = []
    
    my_xg_per_shot_goal_file_list = []
    your_xg_per_shot_goal_file_list = []
    their_xg_per_shot_goal_file_list = []

    my_xg_per_nonshot_goal_file_list = []
    your_xg_per_nonshot_goal_file_list = []
    their_xg_per_nonshot_goal_file_list = []

    my_xg_per_miss_from_shot_file_list = []
    your_xg_per_miss_from_shot_file_list = []
    their_xg_per_miss_from_shot_file_list = []

    my_xg_per_miss_from_nonshot_file_list = []
    your_xg_per_miss_from_nonshot_file_list = []
    their_xg_per_miss_from_nonshot_file_list = []
    
    my_xg_per_shot_goal_frame_list = []
    your_xg_per_shot_goal_frame_list = []
    their_xg_per_shot_goal_frame_list = []

    my_xg_per_nonshot_goal_frame_list = []
    your_xg_per_nonshot_goal_frame_list = []
    their_xg_per_nonshot_goal_frame_list = []

    my_xg_per_miss_from_shot_frame_list = []
    your_xg_per_miss_from_shot_frame_list = []
    their_xg_per_miss_from_shot_frame_list = []

    my_xg_per_miss_from_nonshot_frame_list = []
    your_xg_per_miss_from_nonshot_frame_list = []
    their_xg_per_miss_from_nonshot_frame_list = []

    my_goals_from_shots_over_time = []
    your_goals_from_shots_over_time = []
    their_goals_from_shots_over_time = []

    my_hits_over_time = []
    our_hits_over_time = []
    your_hits_over_time = []
    their_hits_over_time = []

    my_goals_from_shots = 0
    your_goals_from_shots = 0
    their_goals_from_shots = 0

    my_goals_from_nonshots = 0
    your_goals_from_nonshots = 0
    their_goals_from_nonshots = 0

    scoreline_data = []
    scoreline_data_no_colors = []

    my_scores_over_time = []
    your_scores_over_time = []
    their_scores_over_time = []

    # also includes non-shot goals
    my_goals_per_match = []
    your_goals_per_match = []

    my_mvp_count = 0
    your_mvp_count = 0
    their_mvp_count = 0
    our_mvp_count = 0
    mvp_per_match = []

    my_shots_goal_or_miss = []  # 0 = miss, 1 = goal
    your_shots_goal_or_miss = []
    our_shots_goal_or_miss = []
    their_shots_goal_or_miss = []

    my_hit_count = 0
    your_hit_count = 0
    their_hit_count = 0

    for file in new_json_files:
        file_counter += 1
        if file_counter < len(new_json_files) + 1:

            f = open(path_to_json + file, )
            data = json.load(f)

            # load corresponding xG data file
            with open(path_to_xg + file.replace("json", "csv"), encoding="utf8") as f:
                reader = csv.reader(f)
                my_list = list(reader)

            nrows = len(my_list)
            ncols = len(my_list[0])

            my_local_xg = 0
            your_local_xg = 0
            their_local_xg = 0

            my_local_shot_xg = 0
            your_local_shot_xg = 0
            their_local_shot_xg = 0

            my_local_nonshot_xg = 0
            your_local_nonshot_xg = 0
            their_local_nonshot_xg = 0

            my_local_goals_from_shots = 0
            your_local_goals_from_shots = 0
            their_local_goals_from_shots = 0

            my_local_goals_from_nonshots = 0
            your_local_goals_from_nonshots = 0
            their_local_goals_from_nonshots = 0

            our_local_xg_per_hit = []
            their_local_xg_per_hit = []

            my_local_hits = 0
            your_local_hits = 0
            their_local_hits = 0

            for col in range(ncols):
                for row in range(0, nrows):
                    if my_list[0][col] == "shot_taker_name":
                        if row != 0:
                            if my_list[row][col] == my_name or my_list[row][col] == your_name:
                                if my_list[row][6] == "True" and my_list[row][5] == "True":
                                    our_shots_goal_or_miss.append(1)
                                elif my_list[row][6] == "False" and my_list[row][5] == "True":
                                    our_shots_goal_or_miss.append(0)
                                our_local_xg_per_hit.append(float(my_list[row][4]))

                            if my_list[row][col] != my_name and my_list[row][col] != your_name:
                                if my_list[row][6] == "True" and my_list[row][5] == "True":
                                    their_shots_goal_or_miss.append(1)
                                elif my_list[row][6] == "False" and my_list[row][5] == "True":
                                    their_shots_goal_or_miss.append(0)
                                their_local_xg_per_hit.append(float(my_list[row][4]))

                            if my_list[row][col] == my_name:
                                my_hit_count += 1
                                my_local_hits += 1
                                my_local_xg += float(my_list[row][4])
                                my_total_xg += float(my_list[row][4])

                                # shots
                                if my_list[row][5] == "True":
                                    my_shot_xg += float(my_list[row][4])
                                    my_local_shot_xg += float(my_list[row][4])

                                # non-shots
                                if my_list[row][5] == "False":
                                    my_nonshot_xg += float(my_list[row][4])
                                    my_local_nonshot_xg += float(my_list[row][4])
                                    # Non-shot Goals
                                    if my_list[row][6] == "True":
                                        my_goals_from_nonshots += 1
                                        my_local_goals_from_nonshots += 1
                                        my_xg_per_nonshot_goal_list.append(float(my_list[row][4]))
                                        my_xg_per_nonshot_goal_file_list.append(file.replace(".json", ""))
                                    else:
                                        my_xg_per_miss_from_nonshot_list.append(float(my_list[row][4]))
                                        my_xg_per_miss_from_nonshot_file_list.append(file.replace(".json", ""))

                                # Shot Goals
                                if my_list[row][6] == "True" and my_list[row][5] == "True":
                                    my_goal_xg += float(my_list[row][4])
                                    my_xg_per_shot_goal_list.append(float(my_list[row][4]))
                                    my_xg_per_shot_goal_file_list.append(file.replace(".json",""))
                                    #my_xg_per_shot_goal_frame_list.append(file.replace(".json","")) #TODO: ADD FRAMES TO XG OUT FILES
                                    my_local_goals_from_shots += 1
                                    my_goals_from_shots += 1
                                    my_shots_goal_or_miss.append(1)

                                # misses from shots
                                elif my_list[row][6] == "False" and my_list[row][5] == "True":
                                    my_shots_goal_or_miss.append(0)
                                    my_xg_per_miss_from_shot_list.append(float(my_list[row][4]))
                                    my_xg_per_miss_from_shot_file_list.append(file.replace(".json",""))



                            elif my_list[row][col] == your_name:
                                your_hit_count += 1
                                your_local_hits += 1
                                your_local_xg += float(my_list[row][4])
                                your_total_xg += float(my_list[row][4])

                                # shots
                                if my_list[row][5] == "True":
                                    your_shot_xg += float(my_list[row][4])
                                    your_local_shot_xg += float(my_list[row][4])

                                # non-shots
                                if my_list[row][5] == "False":
                                    your_nonshot_xg += float(my_list[row][4])
                                    your_local_nonshot_xg += float(my_list[row][4])

                                    if my_list[row][6] == "True":
                                        your_goals_from_nonshots += 1
                                        your_local_goals_from_nonshots += 1
                                        your_xg_per_nonshot_goal_list.append(float(my_list[row][4]))
                                        your_xg_per_nonshot_goal_file_list.append(file.replace(".json", ""))

                                    else:
                                        your_xg_per_miss_from_nonshot_list.append(float(my_list[row][4]))
                                        your_xg_per_miss_from_nonshot_file_list.append(file.replace(".json", ""))

                                if my_list[row][6] == "True" and my_list[row][5] == "True":
                                    your_goal_xg += float(my_list[row][4])
                                    your_xg_per_shot_goal_list.append(float(my_list[row][4]))
                                    your_xg_per_shot_goal_file_list.append(file.replace(".json",""))
                                    your_local_goals_from_shots += 1
                                    your_goals_from_shots += 1
                                    your_shots_goal_or_miss.append(1)
                                elif my_list[row][6] == "False" and my_list[row][5] == "True":
                                    your_shots_goal_or_miss.append(0)
                                    your_xg_per_miss_from_shot_list.append(float(my_list[row][4]))
                                    your_xg_per_miss_from_shot_file_list.append(file.replace(".json",""))

                            else:
                                their_hit_count += 1
                                their_local_hits += 1
                                their_local_xg += float(my_list[row][4])
                                their_total_xg += float(my_list[row][4])

                                # shots
                                if my_list[row][5] == "True":
                                    their_shot_xg += float(my_list[row][4])
                                    their_local_shot_xg += float(my_list[row][4])

                                # non-shots
                                if my_list[row][5] == "False":
                                    their_nonshot_xg += float(my_list[row][4])
                                    their_local_nonshot_xg += float(my_list[row][4])
                                    if my_list[row][6] == "True":
                                        their_goals_from_nonshots += 1
                                        their_local_goals_from_nonshots += 1
                                        their_xg_per_nonshot_goal_list.append(float(my_list[row][4]))
                                        their_xg_per_nonshot_goal_file_list.append(file.replace(".json", ""))

                                    else:
                                        their_xg_per_miss_from_nonshot_list.append(float(my_list[row][4]))
                                        their_xg_per_miss_from_nonshot_file_list.append(file.replace(".json", ""))

                                if my_list[row][6] == "True" and my_list[row][5] == "True":
                                    their_goal_xg += float(my_list[row][4])
                                    their_xg_per_shot_goal_list.append(float(my_list[row][4]))
                                    their_xg_per_shot_goal_file_list.append(file.replace(".json", ""))
                                    their_local_goals_from_shots += 1
                                    their_goals_from_shots += 1
                                elif my_list[row][6] == "False" and my_list[row][5] == "True":
                                    their_xg_per_miss_from_shot_list.append(float(my_list[row][4]))
                                    their_xg_per_miss_from_shot_file_list.append(file.replace(".json", ""))

            my_goals_from_shots_over_time.append(my_local_goals_from_shots)
            your_goals_from_shots_over_time.append(your_local_goals_from_shots)
            their_goals_from_shots_over_time.append(their_local_goals_from_shots)

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

            local_multiplier = 1
            local_time = data["gameMetadata"]["time"]
            local_names = []
            local_ids = []

            # Link our names to IDs and detect our team color
            for i in data['players']:
                local_names.append(i["name"])
                if i["name"] == my_name:
                    if i["isOrange"]:
                        local_color = "orange"
                        local_multiplier = -1
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

            my_goals_per_match.append(local_my_goals)
            your_goals_per_match.append(local_your_goals)

            my_local_score = 0
            your_local_score = 0
            opp1_local_score = 0
            opp2_local_score = 0

            for i in data["players"]:
                if i["id"]["id"] != my_id and i["id"]["id"] != your_id:
                    local_ids.append(i["id"]["id"])

                if i["id"]["id"] == my_id:
                    if "score" in i:
                        my_scores_over_time.append(i["score"])
                        my_local_score = i["score"]
                        my_score_count += i["score"]
                    if "saves" in i:
                        my_saves_count += i["saves"]
                        local_my_saves += i["saves"]
                    if "totalPasses" in i["stats"]["hitCounts"]:
                        my_passes_count += i["stats"]["hitCounts"]["totalPasses"]
                    if "totalClears" in i["stats"]["hitCounts"]:
                        my_clears_count += i["stats"]["hitCounts"]["totalClears"]
                    if "turnovers" in i["stats"]["possession"]:
                        my_turnovers_count += i["stats"]["possession"]["turnovers"]
                    if "wonTurnovers" in i["stats"]["possession"]:
                        my_turnovers_won_count += i["stats"]["possession"]["wonTurnovers"]
                    if "totalDribbles" in i["stats"]["hitCounts"]:
                        my_dribbles_count += i["stats"]["hitCounts"]["totalDribbles"]
                    if "totalAerials" in i["stats"]["hitCounts"]:
                        my_aerials_count += i["stats"]["hitCounts"]["totalAerials"]

                    # positional tendencies
                    if "timeOnGround" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[0] += i["stats"]["positionalTendencies"]["timeOnGround"]
                    if "timeLowInAir" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[1] += i["stats"]["positionalTendencies"]["timeLowInAir"]
                    if "timeHighInAir" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[2] += i["stats"]["positionalTendencies"]["timeHighInAir"]
                    if "timeInDefendingHalf" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[3] += i["stats"]["positionalTendencies"]["timeInDefendingHalf"]
                    if "timeInAttackingHalf" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[4] += i["stats"]["positionalTendencies"]["timeInAttackingHalf"]
                    if "timeInDefendingThird" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[5] += i["stats"]["positionalTendencies"]["timeInDefendingThird"]
                    if "timeInNeutralThird" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[6] += i["stats"]["positionalTendencies"]["timeInNeutralThird"]
                    if "timeInAttackingThird" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[7] += i["stats"]["positionalTendencies"]["timeInAttackingThird"]
                    if "timeBehindBall" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[8] += i["stats"]["positionalTendencies"]["timeBehindBall"]
                    if "timeInFrontBall" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[9] += i["stats"]["positionalTendencies"]["timeInFrontBall"]
                    if "timeNearWall" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[10] += i["stats"]["positionalTendencies"]["timeNearWall"]
                    if "timeInCorner" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[11] += i["stats"]["positionalTendencies"]["timeInCorner"]
                    if "timeOnWall" in i["stats"]["positionalTendencies"]:
                        my_pos_tendencies[12] += i["stats"]["positionalTendencies"]["timeOnWall"]

                    if "timeFullBoost" in i["stats"]["boost"]:
                        my_pos_tendencies[13] += i["stats"]["boost"]["timeFullBoost"]
                    if "timeLowBoost" in i["stats"]["boost"]:
                        my_pos_tendencies[14] += i["stats"]["boost"]["timeLowBoost"]
                    if "timeNoBoost" in i["stats"]["boost"]:
                        my_pos_tendencies[15] += i["stats"]["boost"]["timeNoBoost"]

                    if "timeClosestToBall" in i["stats"]["distance"]:
                        my_pos_tendencies[16] += i["stats"]["distance"]["timeClosestToBall"]
                    if "timeCloseToBall" in i["stats"]["distance"]:
                        my_pos_tendencies[17] += i["stats"]["distance"]["timeCloseToBall"]
                    if "timeFurthestFromBall" in i["stats"]["distance"]:
                        my_pos_tendencies[18] += i["stats"]["distance"]["timeFurthestFromBall"]

                    if "timeAtSlowSpeed" in i["stats"]["speed"]:
                        my_pos_tendencies[19] += i["stats"]["speed"]["timeAtSlowSpeed"]
                    if "timeAtBoostSpeed" in i["stats"]["speed"]:
                        my_pos_tendencies[20] += i["stats"]["speed"]["timeAtBoostSpeed"]
                    if "timeAtSuperSonic" in i["stats"]["speed"]:
                        my_pos_tendencies[21] += i["stats"]["speed"]["timeAtSuperSonic"]

                    if "ballCarries" in i["stats"]:
                        if "totalCarryTime" in i["stats"]["ballCarries"]:
                            my_pos_tendencies[22] += i["stats"]["ballCarries"]["totalCarryTime"]

                elif i["id"]["id"] == your_id:
                    if "score" in i:
                        your_scores_over_time.append(i["score"])
                        your_score_count += i["score"]
                        your_local_score = i["score"]
                    if "saves" in i:
                        your_saves_count += i["saves"]
                        local_your_saves += i["saves"]
                    if "totalPasses" in i["stats"]["hitCounts"]:
                        your_passes_count += i["stats"]["hitCounts"]["totalPasses"]
                    if "totalClears" in i["stats"]["hitCounts"]:
                        your_clears_count += i["stats"]["hitCounts"]["totalClears"]
                    if "turnovers" in i["stats"]["possession"]:
                        your_turnovers_count += i["stats"]["possession"]["turnovers"]
                    if "wonTurnovers" in i["stats"]["possession"]:
                        your_turnovers_won_count += i["stats"]["possession"]["wonTurnovers"]
                    if "totalDribbles" in i["stats"]["hitCounts"]:
                        your_dribbles_count += i["stats"]["hitCounts"]["totalDribbles"]
                    if "totalAerials" in i["stats"]["hitCounts"]:
                        your_aerials_count += i["stats"]["hitCounts"]["totalAerials"]

                    # positional tendencies
                    if "timeOnGround" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[0] += i["stats"]["positionalTendencies"]["timeOnGround"]
                    if "timeLowInAir" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[1] += i["stats"]["positionalTendencies"]["timeLowInAir"]
                    if "timeHighInAir" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[2] += i["stats"]["positionalTendencies"]["timeHighInAir"]
                    if "timeInDefendingHalf" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[3] += i["stats"]["positionalTendencies"]["timeInDefendingHalf"]
                    if "timeInAttackingHalf" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[4] += i["stats"]["positionalTendencies"]["timeInAttackingHalf"]
                    if "timeInDefendingThird" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[5] += i["stats"]["positionalTendencies"]["timeInDefendingThird"]
                    if "timeInNeutralThird" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[6] += i["stats"]["positionalTendencies"]["timeInNeutralThird"]
                    if "timeInAttackingThird" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[7] += i["stats"]["positionalTendencies"]["timeInAttackingThird"]
                    if "timeBehindBall" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[8] += i["stats"]["positionalTendencies"]["timeBehindBall"]
                    if "timeInFrontBall" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[9] += i["stats"]["positionalTendencies"]["timeInFrontBall"]
                    if "timeNearWall" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[10] += i["stats"]["positionalTendencies"]["timeNearWall"]
                    if "timeInCorner" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[11] += i["stats"]["positionalTendencies"]["timeInCorner"]
                    if "timeOnWall" in i["stats"]["positionalTendencies"]:
                        your_pos_tendencies[12] += i["stats"]["positionalTendencies"]["timeOnWall"]

                    if "timeFullBoost" in i["stats"]["boost"]:
                        your_pos_tendencies[13] += i["stats"]["boost"]["timeFullBoost"]
                    if "timeLowBoost" in i["stats"]["boost"]:
                        your_pos_tendencies[14] += i["stats"]["boost"]["timeLowBoost"]
                    if "timeNoBoost" in i["stats"]["boost"]:
                        your_pos_tendencies[15] += i["stats"]["boost"]["timeNoBoost"]

                    if "timeClosestToBall" in i["stats"]["distance"]:
                        your_pos_tendencies[16] += i["stats"]["distance"]["timeClosestToBall"]
                    if "timeCloseToBall" in i["stats"]["distance"]:
                        your_pos_tendencies[17] += i["stats"]["distance"]["timeCloseToBall"]
                    if "timeFurthestFromBall" in i["stats"]["distance"]:
                        your_pos_tendencies[18] += i["stats"]["distance"]["timeFurthestFromBall"]

                    if "timeAtSlowSpeed" in i["stats"]["speed"]:
                        your_pos_tendencies[19] += i["stats"]["speed"]["timeAtSlowSpeed"]
                    if "timeAtBoostSpeed" in i["stats"]["speed"]:
                        your_pos_tendencies[20] += i["stats"]["speed"]["timeAtBoostSpeed"]
                    if "timeAtSuperSonic" in i["stats"]["speed"]:
                        your_pos_tendencies[21] += i["stats"]["speed"]["timeAtSuperSonic"]

                    if "ballCarries" in i["stats"]:
                        if "totalCarryTime" in i["stats"]["ballCarries"]:
                            your_pos_tendencies[22] += i["stats"]["ballCarries"]["totalCarryTime"]

                else:
                    if "score" in i:
                        their_score_count += i["score"]
                        if i["id"]["id"] == local_ids[0]:
                            opp1_local_score = i["score"]
                        elif i["id"]["id"] == local_ids[1]:
                            opp2_local_score = i["score"]

                    if "saves" in i:
                        their_saves_count += i["saves"]
                        local_their_saves += i["saves"]
                    if "totalPasses" in i["stats"]["hitCounts"]:
                        their_passes_count += i["stats"]["hitCounts"]["totalPasses"]
                    if "totalClears" in i["stats"]["hitCounts"]:
                        their_clears_count += i["stats"]["hitCounts"]["totalClears"]
                    if "turnovers" in i["stats"]["possession"]:
                        their_turnovers_count += i["stats"]["possession"]["turnovers"]
                    if "wonTurnovers" in i["stats"]["possession"]:
                        their_turnovers_won_count += i["stats"]["possession"]["wonTurnovers"]
                    if "totalDribbles" in i["stats"]["hitCounts"]:
                        their_dribbles_count += i["stats"]["hitCounts"]["totalDribbles"]
                    if "totalAerials" in i["stats"]["hitCounts"]:
                        their_aerials_count += i["stats"]["hitCounts"]["totalAerials"]

            max_local_score = max(max(my_local_score, your_local_score), max(opp1_local_score, opp2_local_score))
            local_mvp_per_match = ["", "", "", ""]
            their_scores_over_time.append(opp1_local_score + opp2_local_score)

            # determine MVP - no tiebreaker (players can share MVP if they scored the same amount of pts)
            if my_local_score == max_local_score:
                my_mvp_count += 1
                local_mvp_per_match[0] = my_alias

            if your_local_score == max_local_score:
                your_mvp_count += 1
                local_mvp_per_match[1] = your_alias

            if opp1_local_score == max_local_score:
                local_mvp_per_match[2] = "Opponent1"

            if opp2_local_score == max_local_score:
                local_mvp_per_match[3] = "Opponent2"

            if my_alias in local_mvp_per_match or your_alias in local_mvp_per_match:
                our_mvp_count += 1

            if "Opponent1" in local_mvp_per_match or "Opponent2" in local_mvp_per_match:
                their_mvp_count += 1

            mvp_per_match.append(local_mvp_per_match)

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
                    my_touches_x.append(i["ballData"]["posX"] * local_multiplier)
                    my_touches_y.append(i["ballData"]["posY"] * local_multiplier)
                    my_touches_z.append(i["ballData"]["posZ"])
                elif i["playerId"]["id"] == your_id:
                    your_touches_count += 1
                    your_touches_x.append(i["ballData"]["posX"] * local_multiplier)
                    your_touches_y.append(i["ballData"]["posY"] * local_multiplier)
                    your_touches_z.append(i["ballData"]["posZ"])
                else:
                    their_touches_count += 1

                if "shot" in i:
                    if i["playerId"]["id"] == my_id or i["playerId"]["id"] == your_id:
                        local_our_shots += 1

                        if "goal" in i:
                            if i["playerId"]["id"] == my_id:
                                my_goals_x.append(i["ballData"]["posX"] * local_multiplier)
                                my_goals_y.append(i["ballData"]["posY"] * local_multiplier)
                                my_goals_z.append(i["ballData"]["posZ"])
                                local_my_shots += 1
                            else:
                                your_goals_x.append(i["ballData"]["posX"] * local_multiplier)
                                your_goals_y.append(i["ballData"]["posY"] * local_multiplier)
                                your_goals_z.append(i["ballData"]["posZ"])
                                local_your_shots += 1

                        else:
                            if i["playerId"]["id"] == my_id:
                                my_misses_x.append(i["ballData"]["posX"] * local_multiplier)
                                my_misses_y.append(i["ballData"]["posY"] * local_multiplier)
                                my_misses_z.append(i["ballData"]["posZ"])
                                local_my_shots += 1
                            else:
                                your_misses_x.append(i["ballData"]["posX"] * local_multiplier)
                                your_misses_y.append(i["ballData"]["posY"] * local_multiplier)
                                your_misses_z.append(i["ballData"]["posZ"])
                                local_your_shots += 1

                    else:
                        local_their_shots += 1

                        if "goal" in i:
                            their_goals_x.append(i["ballData"]["posX"] * local_multiplier)
                            their_goals_y.append(i["ballData"]["posY"] * local_multiplier)
                            their_goals_z.append(i["ballData"]["posZ"])
                            their_goals_distancetogoal.append(i["distanceToGoal"])

                        else:
                            their_misses_x.append(i["ballData"]["posX"] * local_multiplier)
                            their_misses_y.append(i["ballData"]["posY"] * local_multiplier)
                            their_misses_z.append(i["ballData"]["posZ"])
                            their_misses_distancetogoal.append(i["distanceToGoal"])

                if i["playerId"]["id"] == my_id and "shot" in i:
                    my_shots_distancetogoal.append(i["distanceToGoal"])
                    my_shots_x.append(i["ballData"]["posX"] * local_multiplier)
                    my_shots_y.append(i["ballData"]["posY"] * local_multiplier)
                    my_shots_z.append(i["ballData"]["posZ"])

                    if "goal" in i:
                        my_goals_distancetogoal.append(i["distanceToGoal"])
                    else:
                        my_misses_distancetogoal.append(i["distanceToGoal"])

                if i["playerId"]["id"] == your_id and "shot" in i:
                    your_shots_distancetogoal.append(i["distanceToGoal"])
                    your_shots_x.append(i["ballData"]["posX"] * local_multiplier)
                    your_shots_y.append(i["ballData"]["posY"] * local_multiplier)
                    your_shots_z.append(i["ballData"]["posZ"])
                    if "goal" in i:
                        your_goals_distancetogoal.append(i["distanceToGoal"])
                    else:
                        your_misses_distancetogoal.append(i["distanceToGoal"])

                if (i["playerId"]["id"] != my_id and i["playerId"]["id"] != your_id) and "shot" in i:
                    their_shots_x.append(i["ballData"]["posX"] * local_multiplier)
                    their_shots_y.append(i["ballData"]["posY"] * local_multiplier)
                    their_shots_z.append(i["ballData"]["posZ"])

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

            my_xg_over_time.append(my_local_xg)
            your_xg_over_time.append(your_local_xg)
            their_xg_over_time.append(their_local_xg)

            my_shot_xg_over_time.append(my_local_shot_xg)
            your_shot_xg_over_time.append(your_local_shot_xg)
            their_shot_xg_over_time.append(their_local_shot_xg)

            my_nonshot_xg_over_time.append(my_local_nonshot_xg)
            your_nonshot_xg_over_time.append(your_local_nonshot_xg)
            their_nonshot_xg_over_time.append(their_local_nonshot_xg)

            my_hits_over_time.append(my_local_hits)
            your_hits_over_time.append(your_local_hits)
            our_hits_over_time.append(my_local_hits + your_local_hits)
            their_hits_over_time.append(their_local_hits)

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

            # games where we conceded "other goals"
            """
            if local_GC > (their_local_goals_from_nonshots + their_local_goals_from_shots):
                print(file)
            """


            def poisson_binomial_pmf(p):
                """Returns the p.m.f. of the Poisson Binomial distribution.

                The Poisson Binomial distribution is the sum of `len(p)` independent yes/no
                trials, with trial `i` having success probability `p[i]`. (The special case
                of all probabilities being equal is the Binomial distribution.)

                Return value is a numpy array of length `len(p)+1`, where element `i` is the
                chance of `i` successes.

                >>> poisson_binomial_pmf([.25])
                array([ 0.75,  0.25])
                >>> poisson_binomial_pmf([.5, .25])
                array([ 0.375,  0.5  ,  0.125])
                >>> poisson_binomial_pmf([.5, .25, .125])
                array([ 0.328125,  0.484375,  0.171875,  0.015625])
                """
                n = len(p)
                pmf = np.zeros(n + 1, dtype=float)
                pmf[0] = 1.0
                for i in range(n):
                    success = pmf[:i + 1] * p[i]
                    pmf[:i + 2] *= (1 - p[i])  # failure
                    pmf[1:i + 2] += success
                return pmf


            def poisson_probability(actual, mean):
                # iterative, to keep the components from getting too large or small:
                p = math.exp(-mean)
                for i in range(actual):
                    p *= mean
                    p /= i + 1
                return p


            win_chance = 0
            draw_chance = 0
            loss_chance = 0
            our_xgf_prob = []
            our_xgc_prob = []
            local_xgf_prob = 0
            local_xgc_prob = 0

            chance_of_missing = 1
            chance_of_scoring = 1

            # our chances of scoring up to N goals where N is the number of shots we took
            our_xgf_prob_raw = poisson_binomial_pmf(our_local_xg_per_hit)
            our_xgc_prob_raw = poisson_binomial_pmf(their_local_xg_per_hit)

            max_possible_goals = max(len(our_xgf_prob_raw), len(our_xgc_prob_raw))

            our_xgf_prob = [0] * max_possible_goals
            our_xgc_prob = [0] * max_possible_goals

            local_our_hits_att = len(our_local_xg_per_hit)
            local_our_hits_con = len(their_local_xg_per_hit)

            for i in range(len(our_xgf_prob_raw)):
                our_xgf_prob[i] = our_xgf_prob_raw[i]

            for i in range(len(our_xgc_prob_raw)):
                our_xgc_prob[i] = our_xgc_prob_raw[i]

            for i in range(0, max_possible_goals):
                draw_chance += (our_xgf_prob[i] * our_xgc_prob[i])
                for j in range(0, max_possible_goals):
                    if i > j:
                        win_chance += (our_xgf_prob[i] * our_xgc_prob[j])
                        loss_chance += (our_xgf_prob[j] * our_xgc_prob[i])

            win_chance += (draw_chance / 2)
            loss_chance += (draw_chance / 2)

            if local_GS < max_possible_goals and local_GC < max_possible_goals:
                score_prob = (our_xgf_prob[local_GS] * our_xgc_prob[local_GC]) / (1 - draw_chance)
            else:
                score_prob = 0

            win_chance_per_game.append(win_chance * 100)
            loss_chance_per_game.append(loss_chance * 100)
            total_win_chance += (win_chance * 100)

            result_type = "W"
            if local_GC > local_GS:
                if local_wentOvertime:
                    result_type = "L*"
                else:
                    result_type = "L"
            if local_GS > local_GC and local_wentOvertime:
                result_type = "W*"
            if result_type == "W" or result_type == "W*":
                result_fairness = win_chance
            else:
                result_fairness = loss_chance
            if result_type == "W":
                color_to_add = Fore.GREEN
            if result_type == "W*":
                color_to_add = Fore.LIGHTGREEN_EX
            if result_type == "L":
                color_to_add = Fore.RED
            if result_type == "L*":
                color_to_add = Fore.LIGHTRED_EX

            local_goal_difference = local_GS - local_GC
            local_xg_difference = (my_local_xg + your_local_xg) - their_local_xg
            local_hit_difference = local_our_hits_att - local_our_hits_con

            scoreline_data.append(
                [color_to_add + "%.2f" % (my_local_xg + your_local_xg), "%.2f" % their_local_xg, local_GS, local_GC,
                 local_our_hits_att, local_our_hits_con, "%.2f" % local_xg_difference, local_goal_difference,
                 local_hit_difference, file.replace(".json", ""),
                 round((win_chance * 100), 2), round((result_fairness * 100), 2), round((score_prob * 100), 2),
                 result_type + Style.RESET_ALL])
            scoreline_data_no_colors.append(
                ["%.2f" % (my_local_xg + your_local_xg), "%.2f" % their_local_xg, local_GS, local_GC,
                 local_our_hits_att, local_our_hits_con, "%.2f" % local_xg_difference, local_goal_difference,
                 local_hit_difference, file.replace(".json", ""),
                 round((win_chance * 100), 2), round((result_fairness * 100), 2), round((score_prob * 100), 2),
                 result_type, local_time])
    if show_xg_scorelines:
        print(tabulate(scoreline_data,
                       headers=["xGF", "xGC", "GF", "GC", "HF", "HC", "xGD", "GD", "HD", "Replay ID", "P(Win)",
                                "P(Result)", "P(Score)",
                                "Outcome"], numalign="right"))
        print("\n")

    content = tabulate(scoreline_data_no_colors,
                       headers=["xGF", "xGC", "GF", "GC", "HF", "HC", "xGD", "GD", "HD", "Replay ID", "P(Win)",
                                "P(Result)", "P(Score)",
                                "Outcome", "StartTime"], tablefmt="tsv")
    if not os.path.exists(path_to_tables + "scorelines.tsv"):
        open(path_to_tables + "scorelines.tsv", 'w').close()
    f = open(path_to_tables + "scorelines.tsv", "w")
    f.write(content)
    f.close()

    your_miss_count = len(your_misses_distancetogoal)
    my_miss_count = len(my_misses_distancetogoal)
    their_miss_count = len(their_misses_distancetogoal)

    our_goal_count = my_goal_count + your_goal_count
    our_miss_count = my_miss_count + your_miss_count

    our_hit_count = my_hit_count + your_hit_count

    my_shot_count = len(my_shots_x)
    your_shot_count = len(your_shots_x)
    our_shot_count = my_shot_count + your_shot_count
    their_shot_count = len(their_shots_x)

    if their_shot_count > 0:
        their_gs_ratio = their_goals_from_shots / their_shot_count
    else:
        their_gs_ratio = 0

    if my_shot_count > 0:
        my_gs_ratio = my_goals_from_shots / my_shot_count
    else:
        my_gs_ratio = 0

    if your_shot_count > 0:
        your_gs_ratio = your_goals_from_shots / your_shot_count
    else:
        your_gs_ratio = 0

    if our_shot_count > 0:
        our_gs_ratio = (my_goals_from_shots + your_goals_from_shots) / our_shot_count
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
    our_dribbles_count = my_dribbles_count + your_dribbles_count
    our_aerials_count = my_aerials_count + your_aerials_count

    # TODO: fix possible div by 0 bugs for following variables
    our_total_xg = my_total_xg + your_total_xg
    our_total_goals_from_shots = my_goals_from_shots + your_goals_from_shots
    our_total_goals_from_nonshots = my_goals_from_nonshots + your_goals_from_nonshots
    our_nonshot_xg = my_nonshot_xg + your_nonshot_xg
    our_shot_xg = my_shot_xg + your_shot_xg

    # gfs = Shot Goals
    my_gfs_xg_ratio = my_goals_from_shots / my_shot_xg
    your_gfs_xg_ratio = your_goals_from_shots / your_shot_xg
    our_gfs_xg_ratio = our_total_goals_from_shots / our_shot_xg
    their_gfs_xg_ratio = their_goals_from_shots / their_shot_xg

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

    if my_shot_count > 0 and your_shot_count == 0:
        our_avg_shot_distance = my_avg_shot_distance
    if my_shot_count == 0 and your_shot_count > 0:
        our_avg_shot_distance = your_avg_shot_distance
    if my_shot_count == 0 and your_shot_count == 0:
        our_avg_shot_distance = 0
    if my_shot_count > 0 and your_shot_count > 0:
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

    my_other_goals = my_goal_count - my_goals_from_shots - my_goals_from_nonshots
    your_other_goals = your_goal_count - your_goals_from_shots - your_goals_from_nonshots
    our_goals_from_shots = my_goals_from_shots + your_goals_from_shots
    our_goals_from_nonshots = my_goals_from_nonshots + your_goals_from_nonshots
    our_other_goals = our_goal_count - our_goals_from_shots - our_goals_from_nonshots
    their_other_goals = their_goal_count - their_goals_from_shots - their_goals_from_nonshots

    individual_data = [["Goals", my_goal_count, your_goal_count],
                       ["Shot Goals", my_goals_from_shots, your_goals_from_shots],
                       ["Non-shot Goals", my_goals_from_nonshots, your_goals_from_nonshots],
                       ["Other Goals", my_other_goals, your_other_goals],
                       ["xG", "%.0f" % my_total_xg, "%.0f" % your_total_xg],
                       ["Shot xG", "%.0f" % my_shot_xg, "%.0f" % your_shot_xg],
                       ["Non-shot xG", "%.0f" % my_nonshot_xg, "%.0f" % your_nonshot_xg],
                       ["GfS/Shot Ratio", "%.2f" % my_gs_ratio, "%.2f" % your_gs_ratio],
                       ["GfS/Shot xG Ratio", "%.2f" % my_gfs_xg_ratio, "%.2f" % your_gfs_xg_ratio],
                       ["Shots", my_shot_count, your_shot_count],
                       ["Misses", my_miss_count, your_miss_count],
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
                       ["Lost Ball", my_turnovers_count, your_turnovers_count],
                       ["Dribbles", my_dribbles_count, your_dribbles_count],
                       ["Aerials", my_aerials_count, your_aerials_count],
                       ["MVPs", my_mvp_count, your_mvp_count],
                       ["Hits", my_hit_count, your_hit_count]
                       ]

    team_data = [["Goals", our_goal_count, their_goal_count],
                 ["Shot Goals", our_goals_from_shots, their_goals_from_shots],
                 ["Non-shot Goals", our_goals_from_nonshots, their_goals_from_nonshots],
                 ["Other Goals", our_other_goals, their_other_goals],
                 ["xG", "%.0f" % our_total_xg, "%.0f" % their_total_xg],
                 ["Shot xG", "%.0f" % our_shot_xg, "%.0f" % their_shot_xg],
                 ["Non-shot xG", "%.0f" % our_nonshot_xg, "%.0f" % their_nonshot_xg],
                 ["GfS/Shot Ratio", "%.2f" % our_gs_ratio, "%.2f" % their_gs_ratio],
                 ["GfS/Shot xG Ratio", "%.2f" % our_gfs_xg_ratio, "%.2f" % their_gfs_xg_ratio],
                 ["Shots", our_shot_count, their_shot_count],
                 ["Misses", our_miss_count, their_miss_count],
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
                 ["Dribbles", our_dribbles_count, their_dribbles_count],
                 ["Aerials", our_aerials_count, their_aerials_count],
                 ["MVPs", our_mvp_count, their_mvp_count],
                 ["Hits", our_hit_count, their_hit_count]
                 ]

    content = tabulate(individual_data, headers=["Stat", my_alias, your_alias], numalign="right", tablefmt="tsv")
    if not os.path.exists(path_to_tables + "player_comparison.tsv"):
        open(path_to_tables + "player_comparison.tsv", 'w').close()
    f = open(path_to_tables + "player_comparison.tsv", "w")
    f.write(content)
    f.close()

    content = tabulate(team_data, headers=["Stat", "Us", "Them"], numalign="right", tablefmt="tsv")
    if not os.path.exists(path_to_tables + "team_comparison.tsv"):
        open(path_to_tables + "team_comparison.tsv", 'w').close()
    f = open(path_to_tables + "team_comparison.tsv", "w")
    f.write(content)
    f.close()

    # coloring output
    for i in range(len(individual_data)):
        if individual_data[i][0] != "Misses" and individual_data[i][0] != "Demoed" and individual_data[i][
            0] != "Lost Ball":
            if individual_data[i][1] > individual_data[i][2]:
                individual_data[i][1] = Fore.MAGENTA + str(individual_data[i][1])
                individual_data[i][2] = Fore.CYAN + str(individual_data[i][2]) + Style.RESET_ALL
            if individual_data[i][1] == individual_data[i][2]:
                individual_data[i][1] = Fore.YELLOW + str(individual_data[i][1])
                individual_data[i][2] = Fore.YELLOW + str(individual_data[i][2]) + Style.RESET_ALL
            if individual_data[i][1] < individual_data[i][2]:
                individual_data[i][1] = Fore.CYAN + str(individual_data[i][1])
                individual_data[i][2] = Fore.MAGENTA + str(individual_data[i][2]) + Style.RESET_ALL
        else:
            if individual_data[i][1] < individual_data[i][2]:
                individual_data[i][1] = Fore.MAGENTA + str(individual_data[i][1])
                individual_data[i][2] = Fore.CYAN + str(individual_data[i][2]) + Style.RESET_ALL
            if individual_data[i][1] == individual_data[i][2]:
                individual_data[i][1] = Fore.YELLOW + str(individual_data[i][1])
                individual_data[i][2] = Fore.YELLOW + str(individual_data[i][2]) + Style.RESET_ALL
            if individual_data[i][1] > individual_data[i][2]:
                individual_data[i][1] = Fore.CYAN + str(individual_data[i][1])
                individual_data[i][2] = Fore.MAGENTA + str(individual_data[i][2]) + Style.RESET_ALL

    for i in range(len(team_data)):
        if team_data[i][0] != "Misses":
            if team_data[i][1] > team_data[i][2]:
                team_data[i][1] = Fore.GREEN + str(team_data[i][1])
                team_data[i][2] = Fore.RED + str(team_data[i][2]) + Style.RESET_ALL
            if team_data[i][1] == team_data[i][2]:
                team_data[i][1] = Fore.YELLOW + str(team_data[i][1])
                team_data[i][2] = Fore.YELLOW + str(team_data[i][2]) + Style.RESET_ALL
            if team_data[i][1] < team_data[i][2]:
                team_data[i][1] = Fore.RED + str(team_data[i][1])
                team_data[i][2] = Fore.GREEN + str(team_data[i][2]) + Style.RESET_ALL
        else:
            if team_data[i][1] < team_data[i][2]:
                team_data[i][1] = Fore.GREEN + str(team_data[i][1])
                team_data[i][2] = Fore.RED + str(team_data[i][2]) + Style.RESET_ALL
            if team_data[i][1] == team_data[i][2]:
                team_data[i][1] = Fore.YELLOW + str(team_data[i][1])
                team_data[i][2] = Fore.YELLOW + str(team_data[i][2]) + Style.RESET_ALL
            if team_data[i][1] > team_data[i][2]:
                team_data[i][1] = Fore.RED + str(team_data[i][1])
                team_data[i][2] = Fore.GREEN + str(team_data[i][2]) + Style.RESET_ALL

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
    streak_xg = []
    streak_my_xg = []
    streak_your_xg = []
    streak_their_xg = []
    streak_filenames = []
    local_my_goals_in_streak = 0
    local_your_goals_in_streak = 0
    local_our_goals_in_streak = 0
    local_their_goals_in_streak = 0
    local_my_xg_in_streak = 0
    local_your_xg_in_streak = 0
    local_our_xg_in_streak = 0
    local_their_xg_in_streak = 0
    local_filenames_in_streak = []

    for result in range(0, len(result_array)):
        if result_array[result] == "W":
            local_wins_in_streak += 1
        elif result_array[result] == "L":
            local_losses_in_streak += 1

        local_my_goals_in_streak += my_goals_over_time[result]
        local_your_goals_in_streak += your_goals_over_time[result]

        local_our_goals_in_streak += (my_goals_over_time[result] + your_goals_over_time[result])
        local_their_goals_in_streak += their_goals_over_time[result]

        local_my_xg_in_streak += my_xg_over_time[result]
        local_your_xg_in_streak += your_xg_over_time[result]

        local_our_xg_in_streak += (my_xg_over_time[result] + your_xg_over_time[result])
        local_their_xg_in_streak += their_xg_over_time[result]

        local_streak_results += str(result_array[result] + " ")
        local_filenames_in_streak.append(new_json_files[result])

        if res_num in streak_end_games:
            streak_wins.append(local_wins_in_streak)
            streak_losses.append(local_losses_in_streak)
            streak_results.append(local_streak_results)
            streak_num_games.append(local_wins_in_streak + local_losses_in_streak)
            streak_goals.append(local_our_goals_in_streak)
            streak_my_goals.append(local_my_goals_in_streak)
            streak_your_goals.append(local_your_goals_in_streak)
            streak_their_goals.append(local_their_goals_in_streak)
            streak_xg.append(local_our_xg_in_streak)
            streak_my_xg.append(local_my_xg_in_streak)
            streak_your_xg.append(local_your_xg_in_streak)
            streak_their_xg.append(local_their_xg_in_streak)
            streak_filenames.append(local_filenames_in_streak)
            local_wins_in_streak = 0
            local_losses_in_streak = 0
            local_streak_results = ""
            local_our_goals_in_streak = 0
            local_my_goals_in_streak = 0
            local_your_goals_in_streak = 0
            local_their_goals_in_streak = 0
            local_our_xg_in_streak = 0
            local_my_xg_in_streak = 0
            local_your_xg_in_streak = 0
            local_their_xg_in_streak = 0
            local_filenames_in_streak = []

        res_num += 1

    # Clear json_new directory
    shutil.rmtree("../data/json_new/")
    os.makedirs("../data/json_new/")

    # Copy most recent streak games to /json_new/
    for file in streak_filenames[len(streak_filenames) - 1]:
        src_dir = "../data/json/"
        dst_dir = "../data/json_new/"

        src_filepath = src_dir + file
        dst_filepath = dst_dir + file

        shutil.copyfile(src_filepath, dst_filepath)

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
        our_xg_per_game_streak = "%.1f" % (streak_xg[streak] / num_games_in_streak)
        my_xg_per_game_streak = "%.1f" % (streak_my_xg[streak] / num_games_in_streak)
        your_xg_per_game_streak = "%.1f" % (streak_your_xg[streak] / num_games_in_streak)
        their_xg_per_game_streak = "%.1f" % (streak_their_xg[streak] / num_games_in_streak)
        xgd_per_game_streak = "%.1f" % ((streak_xg[streak] - streak_their_xg[streak]) / num_games_in_streak)

        streak_data.append(
            [win_pct, streak_results[streak], streak_wins[streak] + streak_losses[streak], streak_wins[streak],
             streak_losses[streak],
             my_goals_per_game_streak, your_goals_per_game_streak, our_goals_per_game_streak,
             their_goals_per_game_streak,
             gd_per_game_streak, my_xg_per_game_streak, your_xg_per_game_streak, our_xg_per_game_streak,
             their_xg_per_game_streak,
             xgd_per_game_streak])

    content = tabulate(streak_data,
                       headers=["Win %", "Results", "GP", "W", "L", my_alias + " GS/G", your_alias + "GS/G",
                                "GS/G", "GC/G", "GD/G", my_alias + " xG/G", your_alias + " xG/G",
                                "xG/G", "xGC/G", "xGD/G"], numalign="right", tablefmt="tsv")
    if not os.path.exists(path_to_tables + "streaks.tsv"):
        open(path_to_tables + "streaks.tsv", 'w').close()
    f = open(path_to_tables + "streaks.tsv", "w")
    f.write(content)
    f.close()

    # colored output
    for i in range(len(streak_data)):

        streak_win_pct = streak_data[i][0].replace("%", "")

        if int(streak_win_pct) > 50:
            streak_data[i][0] = Fore.GREEN + str(streak_data[i][0]) + Style.RESET_ALL
            streak_data[i][2] = Fore.GREEN + str(streak_data[i][2]) + Style.RESET_ALL
            streak_data[i][3] = Fore.GREEN + str(streak_data[i][3]) + Style.RESET_ALL
            streak_data[i][4] = Fore.GREEN + str(streak_data[i][4]) + Style.RESET_ALL

        if int(streak_win_pct) == 50:
            streak_data[i][0] = Fore.YELLOW + str(streak_data[i][0]) + Style.RESET_ALL
            streak_data[i][2] = Fore.YELLOW + str(streak_data[i][2]) + Style.RESET_ALL
            streak_data[i][3] = Fore.YELLOW + str(streak_data[i][3]) + Style.RESET_ALL
            streak_data[i][4] = Fore.YELLOW + str(streak_data[i][4]) + Style.RESET_ALL

        if int(streak_win_pct) < 50:
            streak_data[i][0] = Fore.RED + str(streak_data[i][0]) + Style.RESET_ALL
            streak_data[i][2] = Fore.RED + str(streak_data[i][2]) + Style.RESET_ALL
            streak_data[i][3] = Fore.RED + str(streak_data[i][3]) + Style.RESET_ALL
            streak_data[i][4] = Fore.RED + str(streak_data[i][4]) + Style.RESET_ALL

        streak_data[i][1] = streak_data[i][1].replace("W", Fore.GREEN + "W")
        streak_data[i][1] = streak_data[i][1].replace("L", Fore.RED + "L")
        streak_data[i][1] += Style.RESET_ALL

        # individual GS/G values
        if streak_data[i][5] > streak_data[i][6]:
            streak_data[i][5] = Fore.MAGENTA + str(streak_data[i][5])
            streak_data[i][6] = Fore.CYAN + str(streak_data[i][6]) + Style.RESET_ALL
        if streak_data[i][5] == streak_data[i][6]:
            streak_data[i][5] = Fore.YELLOW + str(streak_data[i][5])
            streak_data[i][6] = Fore.YELLOW + str(streak_data[i][6]) + Style.RESET_ALL
        if streak_data[i][5] < streak_data[i][6]:
            streak_data[i][5] = Fore.CYAN + str(streak_data[i][5])
            streak_data[i][6] = Fore.MAGENTA + str(streak_data[i][6]) + Style.RESET_ALL

        # GD / G
        gdpg_in_streak = float(streak_data[i][9])

        if gdpg_in_streak > 0:
            streak_data[i][9] = Fore.GREEN + str(streak_data[i][9]) + Style.RESET_ALL
            streak_data[i][8] = Fore.GREEN + str(streak_data[i][8]) + Style.RESET_ALL
            streak_data[i][7] = Fore.GREEN + str(streak_data[i][7]) + Style.RESET_ALL

        if gdpg_in_streak == 0:
            streak_data[i][9] = Fore.YELLOW + str(streak_data[i][9]) + Style.RESET_ALL
            streak_data[i][8] = Fore.YELLOW + str(streak_data[i][8]) + Style.RESET_ALL
            streak_data[i][7] = Fore.YELLOW + str(streak_data[i][7]) + Style.RESET_ALL

        if gdpg_in_streak < 0:
            streak_data[i][9] = Fore.RED + str(streak_data[i][9]) + Style.RESET_ALL
            streak_data[i][8] = Fore.RED + str(streak_data[i][8]) + Style.RESET_ALL
            streak_data[i][7] = Fore.RED + str(streak_data[i][7]) + Style.RESET_ALL

        # xGD / G
        xgdpg_in_streak = float(streak_data[i][14])

        if xgdpg_in_streak > 0:
            streak_data[i][14] = Fore.GREEN + str(streak_data[i][14]) + Style.RESET_ALL
            streak_data[i][13] = Fore.GREEN + str(streak_data[i][13]) + Style.RESET_ALL
            streak_data[i][12] = Fore.GREEN + str(streak_data[i][12]) + Style.RESET_ALL

        if xgdpg_in_streak == 0:
            streak_data[i][14] = Fore.YELLOW + str(streak_data[i][14]) + Style.RESET_ALL
            streak_data[i][13] = Fore.YELLOW + str(streak_data[i][13]) + Style.RESET_ALL
            streak_data[i][12] = Fore.YELLOW + str(streak_data[i][12]) + Style.RESET_ALL

        if xgdpg_in_streak < 0:
            streak_data[i][14] = Fore.RED + str(streak_data[i][14]) + Style.RESET_ALL
            streak_data[i][13] = Fore.RED + str(streak_data[i][13]) + Style.RESET_ALL
            streak_data[i][12] = Fore.RED + str(streak_data[i][12]) + Style.RESET_ALL

        # individual xG/G values
        if streak_data[i][10] > streak_data[i][11]:
            streak_data[i][10] = Fore.MAGENTA + str(streak_data[i][10])
            streak_data[i][11] = Fore.CYAN + str(streak_data[i][11]) + Style.RESET_ALL
        if streak_data[i][10] == streak_data[i][11]:
            streak_data[i][10] = Fore.YELLOW + str(streak_data[i][10])
            streak_data[i][11] = Fore.YELLOW + str(streak_data[i][11]) + Style.RESET_ALL
        if streak_data[i][10] < streak_data[i][11]:
            streak_data[i][10] = Fore.CYAN + str(streak_data[i][10])
            streak_data[i][11] = Fore.MAGENTA + str(streak_data[i][11]) + Style.RESET_ALL

    print("\n")
    print(tabulate(streak_data,
                   headers=["Win %", "Results", "GP", "W", "L", my_alias + " GS/G", your_alias + " GS/G",
                            "GS/G", "GC/G", "GD/G", my_alias + " xG/G", your_alias + " xG/G",
                            "xG/G", "xGC/G", "xGD/G"], numalign="right"))
    print("\n")

    games_nr = len(new_json_files)
    our_shots_over_time = [your_shots_over_time[x] + my_shots_over_time[x] for x in range(games_nr)]
    our_saves_over_time = [your_saves_over_time[x] + my_saves_over_time[x] for x in range(games_nr)]
    our_xg_over_time = [your_xg_over_time[x] + my_xg_over_time[x] for x in range(games_nr)]
    our_assists_over_time = [your_assists_over_time[x] + my_assists_over_time[x] for x in range(games_nr)]

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

    our_xg_over_time = []
    my_goals_minus_xg_over_time = []
    your_goals_minus_xg_over_time = []
    our_goals_from_shots_over_time = []
    our_shot_xg_over_time = []
    our_nonshot_xg_over_time = []

    for xg in range(len(my_xg_over_time)):
        our_xg_over_time.append(my_xg_over_time[xg] + your_xg_over_time[xg])
        my_goals_minus_xg_over_time.append(my_goals_over_time[xg] - my_xg_over_time[xg])
        your_goals_minus_xg_over_time.append(your_goals_over_time[xg] - your_xg_over_time[xg])
        our_goals_from_shots_over_time.append(your_goals_from_shots_over_time[xg] + my_goals_from_shots_over_time[xg])

    for xg in range(len(my_shot_xg_over_time)):
        our_shot_xg_over_time.append(my_shot_xg_over_time[xg] + your_shot_xg_over_time[xg])

    for xg in range(len(my_nonshot_xg_over_time)):
        our_nonshot_xg_over_time.append(my_nonshot_xg_over_time[xg] + your_nonshot_xg_over_time[xg])

    ############

    our_win_ratio = win_count / games_nr
    our_loss_ratio = loss_count / games_nr
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

    content = tabulate(result_data,
                       headers=["Stat", "Overall", "Normaltime", "Overtime"], numalign="right", tablefmt="tsv")
    if not os.path.exists(path_to_tables + "streaks.tsv"):
        open(path_to_tables + "results.tsv", 'w').close()
    f = open(path_to_tables + "results.tsv", "w")
    f.write(content)
    f.close()

    for i in range(len(result_data)):
        if i == 0:
            result_data[i][1] = Fore.YELLOW + str(result_data[i][1]) + Style.RESET_ALL
            result_data[i][2] = Fore.MAGENTA + str(result_data[i][2]) + Style.RESET_ALL
            result_data[i][3] = Fore.CYAN + str(result_data[i][3]) + Style.RESET_ALL

        if i == 1 or i == 3:
            result_data[i][1] = Fore.GREEN + str(result_data[i][1]) + Style.RESET_ALL
            result_data[i][2] = Fore.GREEN + str(result_data[i][2]) + Style.RESET_ALL
            result_data[i][3] = Fore.GREEN + str(result_data[i][3]) + Style.RESET_ALL

        if i == 2 or i == 4:
            result_data[i][1] = Fore.RED + str(result_data[i][1]) + Style.RESET_ALL
            result_data[i][2] = Fore.RED + str(result_data[i][2]) + Style.RESET_ALL
            result_data[i][3] = Fore.RED + str(result_data[i][3]) + Style.RESET_ALL

    print(tabulate(result_data, headers=["STATS", "Overall", "Normaltime", "Overtime"], numalign="right"))

    ### Individual Records

    my_most_consecutive_games_scored_in_helper = 0
    my_most_consecutive_games_scored_in = 0
    my_most_consecutive_games_fts_in_helper = 0
    my_most_consecutive_games_fts_in = 0
    for goals in my_goals_per_match:
        if goals > 0:
            my_most_consecutive_games_scored_in_helper += 1
        else:
            my_most_consecutive_games_scored_in_helper = 0
        if my_most_consecutive_games_scored_in_helper > my_most_consecutive_games_scored_in:
            my_most_consecutive_games_scored_in = my_most_consecutive_games_scored_in_helper

        if goals == 0:
            my_most_consecutive_games_fts_in_helper += 1
        else:
            my_most_consecutive_games_fts_in_helper = 0
        if my_most_consecutive_games_fts_in_helper > my_most_consecutive_games_fts_in:
            my_most_consecutive_games_fts_in = my_most_consecutive_games_fts_in_helper

    your_most_consecutive_games_scored_in_helper = 0
    your_most_consecutive_games_scored_in = 0
    your_most_consecutive_games_fts_in_helper = 0
    your_most_consecutive_games_fts_in = 0
    for goals in your_goals_per_match:
        if goals > 0:
            your_most_consecutive_games_scored_in_helper += 1
        else:
            your_most_consecutive_games_scored_in_helper = 0
        if your_most_consecutive_games_scored_in_helper > your_most_consecutive_games_scored_in:
            your_most_consecutive_games_scored_in = your_most_consecutive_games_scored_in_helper
        if goals == 0:
            your_most_consecutive_games_fts_in_helper += 1
        else:
            your_most_consecutive_games_fts_in_helper = 0
        if your_most_consecutive_games_fts_in_helper > your_most_consecutive_games_fts_in:
            your_most_consecutive_games_fts_in = your_most_consecutive_games_fts_in_helper

    my_most_consecutive_games_shot_in_helper = 0
    my_most_consecutive_games_shot_in = 0
    my_most_consecutive_games_noshot_in_helper = 0
    my_most_consecutive_games_noshot_in = 0
    for shots in my_shots_over_time:
        if shots > 0:
            my_most_consecutive_games_shot_in_helper += 1
        else:
            my_most_consecutive_games_shot_in_helper = 0
        if my_most_consecutive_games_shot_in_helper > my_most_consecutive_games_shot_in:
            my_most_consecutive_games_shot_in = my_most_consecutive_games_shot_in_helper

        if shots == 0:
            my_most_consecutive_games_noshot_in_helper += 1
        else:
            my_most_consecutive_games_noshot_in_helper = 0
        if my_most_consecutive_games_noshot_in_helper > my_most_consecutive_games_noshot_in:
            my_most_consecutive_games_noshot_in = my_most_consecutive_games_noshot_in_helper

    your_most_consecutive_games_shot_in_helper = 0
    your_most_consecutive_games_shot_in = 0
    your_most_consecutive_games_noshot_in_helper = 0
    your_most_consecutive_games_noshot_in = 0
    for shots in your_shots_over_time:
        if shots > 0:
            your_most_consecutive_games_shot_in_helper += 1
        else:
            your_most_consecutive_games_shot_in_helper = 0
        if your_most_consecutive_games_shot_in_helper > your_most_consecutive_games_shot_in:
            your_most_consecutive_games_shot_in = your_most_consecutive_games_shot_in_helper

        if shots == 0:
            your_most_consecutive_games_noshot_in_helper += 1
        else:
            your_most_consecutive_games_noshot_in_helper = 0
        if your_most_consecutive_games_noshot_in_helper > your_most_consecutive_games_noshot_in:
            your_most_consecutive_games_noshot_in = your_most_consecutive_games_noshot_in_helper

    my_most_consecutive_games_assist_in_helper = 0
    my_most_consecutive_games_assist_in = 0
    my_most_consecutive_games_noassist_in_helper = 0
    my_most_consecutive_games_noassist_in = 0
    for assists in my_assists_over_time:
        if assists > 0:
            my_most_consecutive_games_assist_in_helper += 1
        else:
            my_most_consecutive_games_assist_in_helper = 0
        if my_most_consecutive_games_assist_in_helper > my_most_consecutive_games_assist_in:
            my_most_consecutive_games_assist_in = my_most_consecutive_games_assist_in_helper

        if assists == 0:
            my_most_consecutive_games_noassist_in_helper += 1
        else:
            my_most_consecutive_games_noassist_in_helper = 0
        if my_most_consecutive_games_noassist_in_helper > my_most_consecutive_games_noassist_in:
            my_most_consecutive_games_noassist_in = my_most_consecutive_games_noassist_in_helper

    your_most_consecutive_games_assist_in_helper = 0
    your_most_consecutive_games_assist_in = 0
    your_most_consecutive_games_noassist_in_helper = 0
    your_most_consecutive_games_noassist_in = 0
    for assists in your_assists_over_time:
        if assists > 0:
            your_most_consecutive_games_assist_in_helper += 1
        else:
            your_most_consecutive_games_assist_in_helper = 0
        if your_most_consecutive_games_assist_in_helper > your_most_consecutive_games_assist_in:
            your_most_consecutive_games_assist_in = your_most_consecutive_games_assist_in_helper

        if assists == 0:
            your_most_consecutive_games_noassist_in_helper += 1
        else:
            your_most_consecutive_games_noassist_in_helper = 0
        if your_most_consecutive_games_noassist_in_helper > your_most_consecutive_games_noassist_in:
            your_most_consecutive_games_noassist_in = your_most_consecutive_games_noassist_in_helper

    my_most_consecutive_games_save_in_helper = 0
    my_most_consecutive_games_save_in = 0
    my_most_consecutive_games_nosave_in_helper = 0
    my_most_consecutive_games_nosave_in = 0
    for saves in my_saves_over_time:
        if saves > 0:
            my_most_consecutive_games_save_in_helper += 1
        else:
            my_most_consecutive_games_save_in_helper = 0
        if my_most_consecutive_games_save_in_helper > my_most_consecutive_games_save_in:
            my_most_consecutive_games_save_in = my_most_consecutive_games_save_in_helper

        if saves == 0:
            my_most_consecutive_games_nosave_in_helper += 1
        else:
            my_most_consecutive_games_nosave_in_helper = 0
        if my_most_consecutive_games_nosave_in_helper > my_most_consecutive_games_nosave_in:
            my_most_consecutive_games_nosave_in = my_most_consecutive_games_nosave_in_helper

    your_most_consecutive_games_save_in_helper = 0
    your_most_consecutive_games_save_in = 0
    your_most_consecutive_games_nosave_in_helper = 0
    your_most_consecutive_games_nosave_in = 0
    for saves in your_saves_over_time:
        if saves > 0:
            your_most_consecutive_games_save_in_helper += 1
        else:
            your_most_consecutive_games_save_in_helper = 0
        if your_most_consecutive_games_save_in_helper > your_most_consecutive_games_save_in:
            your_most_consecutive_games_save_in = your_most_consecutive_games_save_in_helper

        if saves == 0:
            your_most_consecutive_games_nosave_in_helper += 1
        else:
            your_most_consecutive_games_nosave_in_helper = 0
        if your_most_consecutive_games_nosave_in_helper > your_most_consecutive_games_nosave_in:
            your_most_consecutive_games_nosave_in = your_most_consecutive_games_nosave_in_helper

    # returns (at least 1 goal or 1 assist or 1 returned) / blanks
    my_most_consecutive_games_returned_in_helper = 0
    my_most_consecutive_games_returned_in = 0
    my_most_consecutive_games_blanked_in_helper = 0
    my_most_consecutive_games_blanked_in = 0
    for match in range(len(my_saves_over_time)):
        if my_saves_over_time[match] > 0 or my_goals_over_time[match] > 0 or my_assists_over_time[match] > 0:
            my_most_consecutive_games_returned_in_helper += 1
        else:
            my_most_consecutive_games_returned_in_helper = 0
        if my_most_consecutive_games_returned_in_helper > my_most_consecutive_games_returned_in:
            my_most_consecutive_games_returned_in = my_most_consecutive_games_returned_in_helper

        if my_saves_over_time[match] == 0 and my_goals_over_time[match] == 0 and my_assists_over_time[match] == 0:
            my_most_consecutive_games_blanked_in_helper += 1
        else:
            my_most_consecutive_games_blanked_in_helper = 0
        if my_most_consecutive_games_blanked_in_helper > my_most_consecutive_games_blanked_in:
            my_most_consecutive_games_blanked_in = my_most_consecutive_games_blanked_in_helper

    your_most_consecutive_games_returned_in_helper = 0
    your_most_consecutive_games_returned_in = 0
    your_most_consecutive_games_blanked_in_helper = 0
    your_most_consecutive_games_blanked_in = 0
    for match in range(len(your_saves_over_time)):
        if your_saves_over_time[match] > 0 or your_goals_over_time[match] > 0 or your_assists_over_time[match] > 0:
            your_most_consecutive_games_returned_in_helper += 1
        else:
            your_most_consecutive_games_returned_in_helper = 0
        if your_most_consecutive_games_returned_in_helper > your_most_consecutive_games_returned_in:
            your_most_consecutive_games_returned_in = your_most_consecutive_games_returned_in_helper

        if your_saves_over_time[match] == 0 and your_goals_over_time[match] == 0 and your_assists_over_time[match] == 0:
            your_most_consecutive_games_blanked_in_helper += 1
        else:
            your_most_consecutive_games_blanked_in_helper = 0
        if your_most_consecutive_games_blanked_in_helper > your_most_consecutive_games_blanked_in:
            your_most_consecutive_games_blanked_in = your_most_consecutive_games_blanked_in_helper

    my_highest_xg_without_scoring = 0
    your_highest_xg_without_scoring = 0
    our_highest_xg_without_scoring = 0
    their_highest_xg_without_scoring = 0

    my_biggest_xg_overperformance = 0
    your_biggest_xg_overperformance = 0
    our_biggest_xg_overperformance = 0
    their_biggest_xg_overperformance = 0

    my_biggest_xg_overperformance_goals = 0
    your_biggest_xg_overperformance_goals = 0
    our_biggest_xg_overperformance_goals = 0
    their_biggest_xg_overperformance_goals = 0

    my_biggest_xg_overperformance_xg = 0
    your_biggest_xg_overperformance_xg = 0
    our_biggest_xg_overperformance_xg = 0
    their_biggest_xg_overperformance_xg = 0
    
    my_highest_xg_without_scoring_game = 0
    your_highest_xg_without_scoring_game = 0
    our_highest_xg_without_scoring_game = 0
    their_highest_xg_without_scoring_game = 0

    my_biggest_xg_overperformance_shot_game = 0
    your_biggest_xg_overperformance_shot_game = 0
    our_biggest_xg_overperformance_shot_game = 0
    their_biggest_xg_overperformance_shot_game = 0
    
    my_biggest_xg_overperformance_nonshot_game = 0
    your_biggest_xg_overperformance_nonshot_game = 0
    our_biggest_xg_overperformance_nonshot_game = 0
    their_biggest_xg_overperformance_nonshot_game = 0

    for match in range(len(my_goals_from_shots_over_time)):
        if my_xg_over_time[match] != 0:
            if my_goals_from_shots_over_time[match] / my_xg_over_time[match] > my_biggest_xg_overperformance:
                my_biggest_xg_overperformance = my_goals_from_shots_over_time[match] / my_xg_over_time[match]
                my_biggest_xg_overperformance_goals = my_goals_from_shots_over_time[match]
                my_biggest_xg_overperformance_xg = my_xg_over_time[match]
                my_biggest_xg_overperformance_shot_game = match

        if your_xg_over_time[match] != 0:
            if your_goals_from_shots_over_time[match] / your_xg_over_time[match] > your_biggest_xg_overperformance:
                your_biggest_xg_overperformance = your_goals_from_shots_over_time[match] / your_xg_over_time[match]
                your_biggest_xg_overperformance_goals = your_goals_from_shots_over_time[match]
                your_biggest_xg_overperformance_xg = your_xg_over_time[match]
                your_biggest_xg_overperformance_shot_game = match

        if our_xg_over_time[match] != 0:
            if our_goals_from_shots_over_time[match] / our_xg_over_time[match] > our_biggest_xg_overperformance:
                our_biggest_xg_overperformance = our_goals_from_shots_over_time[match] / our_xg_over_time[match]
                our_biggest_xg_overperformance_goals = our_goals_from_shots_over_time[match]
                our_biggest_xg_overperformance_xg = our_xg_over_time[match]
                our_biggest_xg_overperformance_shot_game = match

        if their_xg_over_time[match] != 0:
            if their_goals_from_shots_over_time[match] / their_xg_over_time[match] > their_biggest_xg_overperformance:
                their_biggest_xg_overperformance = their_goals_from_shots_over_time[match] / their_xg_over_time[match]
                their_biggest_xg_overperformance_goals = their_goals_from_shots_over_time[match]
                their_biggest_xg_overperformance_xg = their_xg_over_time[match]
                their_biggest_xg_overperformance_shot_game = match

        if my_goals_from_shots_over_time[match] == 0:
            if my_xg_over_time[match] > my_highest_xg_without_scoring:
                my_highest_xg_without_scoring = my_xg_over_time[match]
                my_highest_xg_without_scoring_game = match

        if your_goals_from_shots_over_time[match] == 0:
            if your_xg_over_time[match] > your_highest_xg_without_scoring:
                your_highest_xg_without_scoring = your_xg_over_time[match]
                your_highest_xg_without_scoring_game = match

        if our_goals_from_shots_over_time[match] == 0:
            if our_xg_over_time[match] > our_highest_xg_without_scoring:
                our_highest_xg_without_scoring = our_xg_over_time[match]
                our_highest_xg_without_scoring_game = match

        if their_goals_from_shots_over_time[match] == 0:
            if their_xg_over_time[match] > their_highest_xg_without_scoring:
                their_highest_xg_without_scoring = their_xg_over_time[match]
                their_highest_xg_without_scoring_game = match

    # TODO: ADD FRAMES
    my_biggest_xg_miss_from_shot = 0
    my_lowest_xg_goal_from_shot = 0
    my_biggest_xg_miss_from_shot_file = ""
    my_lowest_xg_goal_from_shot_file = ""
    for shot in range(len(my_xg_per_shot_goal_list)):
        if shot == 0:
            my_lowest_xg_goal_from_shot = my_xg_per_shot_goal_list[shot]
        else:
            if my_xg_per_shot_goal_list[shot] < my_lowest_xg_goal_from_shot:
                my_lowest_xg_goal_from_shot = my_xg_per_shot_goal_list[shot]
                my_lowest_xg_goal_from_shot_file = my_xg_per_shot_goal_file_list[shot]

    for shot in range(len(my_xg_per_miss_from_shot_list)):
        if my_xg_per_miss_from_shot_list[shot] > my_biggest_xg_miss_from_shot:
            my_biggest_xg_miss_from_shot = my_xg_per_miss_from_shot_list[shot]
            my_biggest_xg_miss_from_shot_file = my_xg_per_miss_from_shot_file_list[shot]

    your_biggest_xg_miss_from_shot = 0
    your_lowest_xg_goal_from_shot = 0
    for shot in range(len(your_xg_per_shot_goal_list)):
        if shot == 0:
            your_lowest_xg_goal_from_shot = your_xg_per_shot_goal_list[shot]
        else:
            if your_xg_per_shot_goal_list[shot] < your_lowest_xg_goal_from_shot:
                your_lowest_xg_goal_from_shot = your_xg_per_shot_goal_list[shot]
                your_lowest_xg_goal_from_shot_file = your_xg_per_shot_goal_file_list[shot]

    for shot in range(len(your_xg_per_miss_from_shot_list)):
        if your_xg_per_miss_from_shot_list[shot] > your_biggest_xg_miss_from_shot:
            your_biggest_xg_miss_from_shot = your_xg_per_miss_from_shot_list[shot]
            your_biggest_xg_miss_from_shot_file = your_xg_per_miss_from_shot_file_list[shot]

    our_biggest_xg_miss_from_shot = max(your_biggest_xg_miss_from_shot, my_biggest_xg_miss_from_shot)
    our_lowest_xg_goal_from_shot = min(your_lowest_xg_goal_from_shot, my_lowest_xg_goal_from_shot)

    our_biggest_xg_miss_from_shot_file = ""
    if our_biggest_xg_miss_from_shot == your_biggest_xg_miss_from_shot:
        our_biggest_xg_miss_from_shot_file = your_biggest_xg_miss_from_shot_file
    if our_biggest_xg_miss_from_shot == my_biggest_xg_miss_from_shot:
        our_biggest_xg_miss_from_shot_file = my_biggest_xg_miss_from_shot_file

    our_lowest_xg_goal_from_shot_file = ""
    if our_lowest_xg_goal_from_shot == your_lowest_xg_goal_from_shot:
        our_lowest_xg_goal_from_shot_file = your_lowest_xg_goal_from_shot_file
    if our_lowest_xg_goal_from_shot == my_lowest_xg_goal_from_shot:
        our_lowest_xg_goal_from_shot_file = my_lowest_xg_goal_from_shot_file
    
    their_biggest_xg_miss_from_shot = 0
    their_lowest_xg_goal_from_shot = 0
    their_biggest_xg_miss_from_shot_file = ""
    their_lowest_xg_goal_from_shot_file = ""
    for shot in range(len(their_xg_per_shot_goal_list)):
        if shot == 0:
            their_lowest_xg_goal_from_shot = their_xg_per_shot_goal_list[shot]
            their_lowest_xg_goal_from_shot_file = their_xg_per_shot_goal_file_list[shot]
        else:
            if their_xg_per_shot_goal_list[shot] < their_lowest_xg_goal_from_shot:
                their_lowest_xg_goal_from_shot = their_xg_per_shot_goal_list[shot]
                their_lowest_xg_goal_from_shot_file = their_xg_per_shot_goal_file_list[shot]

    for shot in range(len(their_xg_per_miss_from_shot_list)):
        if their_xg_per_miss_from_shot_list[shot] > their_biggest_xg_miss_from_shot:
            their_biggest_xg_miss_from_shot = their_xg_per_miss_from_shot_list[shot]
            their_biggest_xg_miss_from_shot_file = their_xg_per_miss_from_shot_file_list[shot]

    my_biggest_xg_miss_from_nonshot = 0
    my_lowest_xg_goal_from_nonshot = 0
    my_biggest_xg_miss_from_nonshot_file = ""
    my_lowest_xg_goal_from_nonshot_file = ""
    for nonshot in range(len(my_xg_per_nonshot_goal_list)):
        if nonshot == 0:
            my_lowest_xg_goal_from_nonshot = my_xg_per_nonshot_goal_list[nonshot]
            my_lowest_xg_goal_from_nonshot_file = my_xg_per_nonshot_goal_file_list[nonshot]
        else:
            if my_xg_per_nonshot_goal_list[nonshot] < my_lowest_xg_goal_from_nonshot:
                my_lowest_xg_goal_from_nonshot = my_xg_per_nonshot_goal_list[nonshot]
                my_lowest_xg_goal_from_nonshot_file = my_xg_per_nonshot_goal_file_list[nonshot]

    for nonshot in range(len(my_xg_per_miss_from_nonshot_list)):
        if my_xg_per_miss_from_nonshot_list[nonshot] > my_biggest_xg_miss_from_nonshot:
            my_biggest_xg_miss_from_nonshot = my_xg_per_miss_from_nonshot_list[nonshot]
            my_biggest_xg_miss_from_nonshot_file = my_xg_per_miss_from_nonshot_file_list[nonshot]

    your_biggest_xg_miss_from_nonshot = 0
    your_lowest_xg_goal_from_nonshot = 0
    your_biggest_xg_miss_from_nonshot_file = ""
    your_lowest_xg_goal_from_nonshot_file = ""
    for nonshot in range(len(your_xg_per_nonshot_goal_list)):
        if nonshot == 0:
            your_lowest_xg_goal_from_nonshot = your_xg_per_nonshot_goal_list[nonshot]
            your_lowest_xg_goal_from_nonshot_file = your_xg_per_nonshot_goal_file_list[nonshot]
        else:
            if your_xg_per_nonshot_goal_list[nonshot] < your_lowest_xg_goal_from_nonshot:
                your_lowest_xg_goal_from_nonshot = your_xg_per_nonshot_goal_list[nonshot]
                your_lowest_xg_goal_from_nonshot_file = your_xg_per_nonshot_goal_file_list[nonshot]

    for nonshot in range(len(your_xg_per_miss_from_nonshot_list)):
        if your_xg_per_miss_from_nonshot_list[nonshot] > your_biggest_xg_miss_from_nonshot:
            your_biggest_xg_miss_from_nonshot = your_xg_per_miss_from_nonshot_list[nonshot]
            your_biggest_xg_miss_from_nonshot_file = your_xg_per_miss_from_nonshot_file_list[nonshot]

    our_biggest_xg_miss_from_nonshot = max(your_biggest_xg_miss_from_nonshot, my_biggest_xg_miss_from_nonshot)
    our_lowest_xg_goal_from_nonshot = min(your_lowest_xg_goal_from_nonshot, my_lowest_xg_goal_from_nonshot)
    
    our_biggest_xg_miss_from_nonshot_file = ""
    if our_biggest_xg_miss_from_nonshot == your_biggest_xg_miss_from_nonshot:
        our_biggest_xg_miss_from_nonshot_file = your_biggest_xg_miss_from_nonshot_file
    if our_biggest_xg_miss_from_nonshot == my_biggest_xg_miss_from_nonshot:
        our_biggest_xg_miss_from_nonshot_file = my_biggest_xg_miss_from_nonshot_file

    our_lowest_xg_goal_from_nonshot_file = ""
    if our_lowest_xg_goal_from_nonshot == your_lowest_xg_goal_from_nonshot:
        our_lowest_xg_goal_from_nonshot_file = your_lowest_xg_goal_from_nonshot_file
    if our_lowest_xg_goal_from_nonshot == my_lowest_xg_goal_from_nonshot:
        our_lowest_xg_goal_from_nonshot_file = my_lowest_xg_goal_from_nonshot_file

    their_biggest_xg_miss_from_nonshot = 0
    their_lowest_xg_goal_from_nonshot = 0
    their_biggest_xg_miss_from_nonshot_file = ""
    their_lowest_xg_goal_from_nonshot_file = ""
    for nonshot in range(len(their_xg_per_nonshot_goal_list)):
        if nonshot == 0:
            their_lowest_xg_goal_from_nonshot = their_xg_per_nonshot_goal_list[nonshot]
            their_lowest_xg_goal_from_nonshot_file = their_xg_per_nonshot_goal_file_list[nonshot]
        else:
            if their_xg_per_nonshot_goal_list[nonshot] < their_lowest_xg_goal_from_nonshot:
                their_lowest_xg_goal_from_nonshot = their_xg_per_nonshot_goal_list[nonshot]
                their_lowest_xg_goal_from_nonshot_file = their_xg_per_nonshot_goal_file_list[nonshot]

    for nonshot in range(len(their_xg_per_miss_from_nonshot_list)):
        if their_xg_per_miss_from_nonshot_list[nonshot] > their_biggest_xg_miss_from_nonshot:
            their_biggest_xg_miss_from_nonshot = their_xg_per_miss_from_nonshot_list[nonshot]
            their_biggest_xg_miss_from_nonshot_file = their_xg_per_miss_from_nonshot_file_list[nonshot]

    #TODO: Add frame and file for highest and furthest goals scored
    my_highest_goal_scored = 0
    my_furthest_goal_scored = 0
    for distance in my_goals_distancetogoal:
        if distance > my_furthest_goal_scored:
            my_furthest_goal_scored = distance

    for z in my_goals_z:
        if z > my_highest_goal_scored:
            my_highest_goal_scored = z

    your_highest_goal_scored = 0
    your_furthest_goal_scored = 0
    for distance in your_goals_distancetogoal:
        if distance > your_furthest_goal_scored:
            your_furthest_goal_scored = distance

    for z in your_goals_z:
        if z > your_highest_goal_scored:
            your_highest_goal_scored = z

    my_most_consecutive_mvp_helper = 0
    my_most_consecutive_mvp = 0
    my_most_consecutive_nomvp_in_helper = 0
    my_most_consecutive_nomvp_in = 0
    your_most_consecutive_mvp_helper = 0
    your_most_consecutive_mvp = 0
    your_most_consecutive_nomvp_in_helper = 0
    your_most_consecutive_nomvp_in = 0

    our_most_consecutive_mvp_helper = 0
    our_most_consecutive_mvp = 0
    our_most_consecutive_nomvp_in_helper = 0
    our_most_consecutive_nomvp_in = 0
    their_most_consecutive_mvp_helper = 0
    their_most_consecutive_mvp = 0
    their_most_consecutive_nomvp_in_helper = 0
    their_most_consecutive_nomvp_in = 0
    for match in range(len(mvp_per_match)):
        if my_alias in mvp_per_match[match]:
            my_most_consecutive_mvp_helper += 1
        else:
            my_most_consecutive_mvp_helper = 0
        if my_most_consecutive_mvp_helper > my_most_consecutive_mvp:
            my_most_consecutive_mvp = my_most_consecutive_mvp_helper

        if my_alias not in mvp_per_match[match]:
            my_most_consecutive_nomvp_in_helper += 1
        else:
            my_most_consecutive_nomvp_in_helper = 0
        if my_most_consecutive_nomvp_in_helper > my_most_consecutive_nomvp_in:
            my_most_consecutive_nomvp_in = my_most_consecutive_nomvp_in_helper

        if your_alias in mvp_per_match[match]:
            your_most_consecutive_mvp_helper += 1
        else:
            your_most_consecutive_mvp_helper = 0
        if your_most_consecutive_mvp_helper > your_most_consecutive_mvp:
            your_most_consecutive_mvp = your_most_consecutive_mvp_helper

        if your_alias not in mvp_per_match[match]:
            your_most_consecutive_nomvp_in_helper += 1
        else:
            your_most_consecutive_nomvp_in_helper = 0
        if your_most_consecutive_nomvp_in_helper > your_most_consecutive_nomvp_in:
            your_most_consecutive_nomvp_in = your_most_consecutive_nomvp_in_helper

        if (my_alias in mvp_per_match[match]) or (your_alias in mvp_per_match[match]):
            our_most_consecutive_mvp_helper += 1
        else:
            our_most_consecutive_mvp_helper = 0
        if our_most_consecutive_mvp_helper > our_most_consecutive_mvp:
            our_most_consecutive_mvp = our_most_consecutive_mvp_helper

        if (my_alias not in mvp_per_match[match]) and (your_alias not in mvp_per_match[match]):
            our_most_consecutive_nomvp_in_helper += 1
        else:
            our_most_consecutive_nomvp_in_helper = 0
        if our_most_consecutive_nomvp_in_helper > our_most_consecutive_nomvp_in:
            our_most_consecutive_nomvp_in = our_most_consecutive_nomvp_in_helper

        if ("Opponent1" in mvp_per_match[match]) or ("Opponent2" in mvp_per_match[match]):
            their_most_consecutive_mvp_helper += 1
        else:
            their_most_consecutive_mvp_helper = 0
        if their_most_consecutive_mvp_helper > their_most_consecutive_mvp:
            their_most_consecutive_mvp = their_most_consecutive_mvp_helper

        if ("Opponent1" not in mvp_per_match[match]) and ("Opponent2" not in mvp_per_match[match]):
            their_most_consecutive_nomvp_in_helper += 1
        else:
            their_most_consecutive_nomvp_in_helper = 0
        if their_most_consecutive_nomvp_in_helper > their_most_consecutive_nomvp_in:
            their_most_consecutive_nomvp_in = their_most_consecutive_nomvp_in_helper

    my_most_consecutive_goals_from_shots_helper = 0
    my_most_consecutive_goals_from_shots = 0
    my_most_consecutive_misses_from_shots_helper = 0
    my_most_consecutive_misses_from_shots = 0
    for shot in my_shots_goal_or_miss:
        if shot == 1:
            my_most_consecutive_goals_from_shots_helper += 1
        else:
            my_most_consecutive_goals_from_shots_helper = 0
        if my_most_consecutive_goals_from_shots_helper > my_most_consecutive_goals_from_shots:
            my_most_consecutive_goals_from_shots = my_most_consecutive_goals_from_shots_helper

        if shot == 0:
            my_most_consecutive_misses_from_shots_helper += 1
        else:
            my_most_consecutive_misses_from_shots_helper = 0
        if my_most_consecutive_misses_from_shots_helper > my_most_consecutive_misses_from_shots:
            my_most_consecutive_misses_from_shots = my_most_consecutive_misses_from_shots_helper

    your_most_consecutive_goals_from_shots_helper = 0
    your_most_consecutive_goals_from_shots = 0
    your_most_consecutive_misses_from_shots_helper = 0
    your_most_consecutive_misses_from_shots = 0
    for shot in your_shots_goal_or_miss:
        if shot == 1:
            your_most_consecutive_goals_from_shots_helper += 1
        else:
            your_most_consecutive_goals_from_shots_helper = 0
        if your_most_consecutive_goals_from_shots_helper > your_most_consecutive_goals_from_shots:
            your_most_consecutive_goals_from_shots = your_most_consecutive_goals_from_shots_helper

        if shot == 0:
            your_most_consecutive_misses_from_shots_helper += 1
        else:
            your_most_consecutive_misses_from_shots_helper = 0
        if your_most_consecutive_misses_from_shots_helper > your_most_consecutive_misses_from_shots:
            your_most_consecutive_misses_from_shots = your_most_consecutive_misses_from_shots_helper

    our_most_consecutive_goals_from_shots_helper = 0
    our_most_consecutive_goals_from_shots = 0
    our_most_consecutive_misses_from_shots_helper = 0
    our_most_consecutive_misses_from_shots = 0
    for shot in our_shots_goal_or_miss:
        if shot == 1:
            our_most_consecutive_goals_from_shots_helper += 1
        else:
            our_most_consecutive_goals_from_shots_helper = 0
        if our_most_consecutive_goals_from_shots_helper > our_most_consecutive_goals_from_shots:
            our_most_consecutive_goals_from_shots = our_most_consecutive_goals_from_shots_helper

        if shot == 0:
            our_most_consecutive_misses_from_shots_helper += 1
        else:
            our_most_consecutive_misses_from_shots_helper = 0
        if our_most_consecutive_misses_from_shots_helper > our_most_consecutive_misses_from_shots:
            our_most_consecutive_misses_from_shots = our_most_consecutive_misses_from_shots_helper

    their_most_consecutive_goals_from_shots_helper = 0
    their_most_consecutive_goals_from_shots = 0
    their_most_consecutive_misses_from_shots_helper = 0
    their_most_consecutive_misses_from_shots = 0
    for shot in their_shots_goal_or_miss:
        if shot == 1:
            their_most_consecutive_goals_from_shots_helper += 1
        else:
            their_most_consecutive_goals_from_shots_helper = 0
        if their_most_consecutive_goals_from_shots_helper > their_most_consecutive_goals_from_shots:
            their_most_consecutive_goals_from_shots = their_most_consecutive_goals_from_shots_helper

        if shot == 0:
            their_most_consecutive_misses_from_shots_helper += 1
        else:
            their_most_consecutive_misses_from_shots_helper = 0
        if their_most_consecutive_misses_from_shots_helper > their_most_consecutive_misses_from_shots:
            their_most_consecutive_misses_from_shots = their_most_consecutive_misses_from_shots_helper

    my_most_consecutive_games_scored_or_assisted_in_helper = 0
    my_most_consecutive_games_scored_or_assisted_in = 0
    my_most_consecutive_games_ftsoa_in_helper = 0
    my_most_consecutive_games_ftsoa_in = 0
    my_most_goals_or_assists_in_one_game = 0
    for match in range(len(my_goals_over_time)):
        if my_goals_over_time[match] > 0 or my_assists_over_time[match] > 0:
            my_most_consecutive_games_ftsoa_in_helper = 0
            my_most_consecutive_games_scored_or_assisted_in_helper += 1
            if my_goals_over_time[match] + my_assists_over_time[match] > my_most_goals_or_assists_in_one_game:
                my_most_goals_or_assists_in_one_game = my_goals_over_time[match] + my_assists_over_time[match]
            if my_most_consecutive_games_scored_or_assisted_in_helper > my_most_consecutive_games_scored_or_assisted_in:
                my_most_consecutive_games_scored_or_assisted_in = my_most_consecutive_games_scored_or_assisted_in_helper

        if my_goals_over_time[match] == 0 and my_assists_over_time[match] == 0:
            my_most_consecutive_games_scored_or_assisted_in_helper = 0
            my_most_consecutive_games_ftsoa_in_helper += 1
            if my_most_consecutive_games_ftsoa_in_helper > my_most_consecutive_games_ftsoa_in:
                my_most_consecutive_games_ftsoa_in = my_most_consecutive_games_ftsoa_in_helper

    your_most_consecutive_games_scored_or_assisted_in_helper = 0
    your_most_consecutive_games_scored_or_assisted_in = 0
    your_most_consecutive_games_ftsoa_in_helper = 0
    your_most_consecutive_games_ftsoa_in = 0
    your_most_goals_or_assists_in_one_game = 0
    for match in range(len(your_goals_over_time)):
        if your_goals_over_time[match] > 0 or your_assists_over_time[match] > 0:
            your_most_consecutive_games_ftsoa_in_helper = 0
            your_most_consecutive_games_scored_or_assisted_in_helper += 1
            if your_goals_over_time[match] + your_assists_over_time[match] > your_most_goals_or_assists_in_one_game:
                your_most_goals_or_assists_in_one_game = your_goals_over_time[match] + your_assists_over_time[match]
            if your_most_consecutive_games_scored_or_assisted_in_helper > your_most_consecutive_games_scored_or_assisted_in:
                your_most_consecutive_games_scored_or_assisted_in = your_most_consecutive_games_scored_or_assisted_in_helper

        if your_goals_over_time[match] == 0 and your_assists_over_time[match] == 0:
            your_most_consecutive_games_scored_or_assisted_in_helper = 0
            your_most_consecutive_games_ftsoa_in_helper += 1
            if your_most_consecutive_games_ftsoa_in_helper > your_most_consecutive_games_ftsoa_in:
                your_most_consecutive_games_ftsoa_in = your_most_consecutive_games_ftsoa_in_helper

    individual_record_data = [["Most goals scored in one match", max(my_goals_per_match), max(your_goals_per_match),
                               link_replay(new_json_files[my_goals_per_match.index(max(my_goals_per_match))], 0, False),
                               link_replay(new_json_files[your_goals_per_match.index(max(your_goals_per_match))], 0, False)],
                              ["Most consecutive matches scored in", my_most_consecutive_games_scored_in,
                               your_most_consecutive_games_scored_in],
                              ["Most consecutive matches failed to scored in", my_most_consecutive_games_fts_in,
                               your_most_consecutive_games_fts_in],
                              ["Most shots in one match", max(my_shots_over_time), max(your_shots_over_time),
                               link_replay(new_json_files[my_shots_over_time.index(max(my_shots_over_time))], 0, False),
                               link_replay(new_json_files[your_shots_over_time.index(max(your_shots_over_time))], 0, False)],
                              ["Most consecutive matches shot in", my_most_consecutive_games_shot_in,
                               your_most_consecutive_games_shot_in],
                              ["Most consecutive matches failed to shoot in", my_most_consecutive_games_noshot_in,
                               your_most_consecutive_games_noshot_in],
                              ["Most assists in one match", max(my_assists_over_time), max(your_assists_over_time),
                              link_replay(new_json_files[my_assists_over_time.index(max(my_assists_over_time))], 0, False),
                              link_replay(new_json_files[your_assists_over_time.index(max(your_assists_over_time))], 0,False)],
                              ["Most consecutive matches assisted in", my_most_consecutive_games_assist_in,
                               your_most_consecutive_games_assist_in],
                              ["Most consecutive matches failed to assist in", my_most_consecutive_games_noassist_in,
                               your_most_consecutive_games_noassist_in],
                              ["Most saves in one match", max(my_saves_over_time), max(your_saves_over_time),
                               link_replay(new_json_files[my_saves_over_time.index(max(my_saves_over_time))], 0, False),
                               link_replay(new_json_files[your_saves_over_time.index(max(your_saves_over_time))], 0, False)],
                              ["Most consecutive matches saved in", my_most_consecutive_games_save_in,
                               your_most_consecutive_games_save_in],
                              ["Most consecutive matches failed to save in", my_most_consecutive_games_nosave_in,
                               your_most_consecutive_games_nosave_in],
                              ["Highest score in one match", max(my_scores_over_time), max(your_scores_over_time),
                              link_replay(new_json_files[my_scores_over_time.index(max(my_scores_over_time))], 0, False),
                              link_replay(new_json_files[your_scores_over_time.index(max(your_scores_over_time))], 0, False)],
                              ["Lowest score in one match", min(my_scores_over_time), min(your_scores_over_time),
                               link_replay(new_json_files[my_scores_over_time.index(min(my_scores_over_time))], 0, False),
                               link_replay(new_json_files[your_scores_over_time.index(min(your_scores_over_time))], 0, False)],
                              ["Highest xG in one match", round(max(my_xg_over_time), 2), round(max(your_xg_over_time), 2),
                               link_replay(new_json_files[my_xg_over_time.index(max(my_xg_over_time))], 0,False),
                               link_replay(new_json_files[your_xg_over_time.index(max(your_xg_over_time))], 0, False)],
                              ["Highest xG without scoring in one match (only shot-goals)",
                               round(my_highest_xg_without_scoring, 2), round(your_highest_xg_without_scoring, 2),
                               link_replay(new_json_files[my_highest_xg_without_scoring_game], 0, False),
                               link_replay(new_json_files[your_highest_xg_without_scoring_game], 0, False)],
                              ["Highest shot xG in one match", round(max(my_shot_xg_over_time), 2), round(max(your_shot_xg_over_time), 2),
                              link_replay(new_json_files[my_shot_xg_over_time.index(max(my_shot_xg_over_time))], 0, False),
                              link_replay(new_json_files[your_shot_xg_over_time.index(max(your_shot_xg_over_time))], 0, False)],
                             ["Highest non-shot xG in one match", round(max(my_nonshot_xg_over_time), 2), round(max(your_nonshot_xg_over_time), 2),
                              link_replay(new_json_files[my_nonshot_xg_over_time.index(max(my_nonshot_xg_over_time))], 0,
                                          False),
                              link_replay(new_json_files[your_nonshot_xg_over_time.index(max(your_nonshot_xg_over_time))], 0,
                                          False)],
                             ["Biggest xG overperformance in one match (only shot-goals)",
                               str(my_biggest_xg_overperformance_goals) + "G from " + str(
                                   round(my_biggest_xg_overperformance_xg, 2)) + " xG",
                               str(your_biggest_xg_overperformance_goals) + "G from " + str(
                                   round(your_biggest_xg_overperformance_xg, 2)) + " xG",
                              link_replay(new_json_files[my_biggest_xg_overperformance_shot_game], 0, False),
                              link_replay(new_json_files[your_biggest_xg_overperformance_shot_game], 0, False)],
                              ["Biggest xG overperformance in one match (only shot-goals) %", "%.0f" % (((my_biggest_xg_overperformance_goals / my_biggest_xg_overperformance_xg) * 100) - 100) + "%",
                               "%.0f" % (((your_biggest_xg_overperformance_goals / your_biggest_xg_overperformance_xg) * 100) - 100) + "%",
                               link_replay(new_json_files[my_biggest_xg_overperformance_shot_game], 0, False),
                               link_replay(new_json_files[your_biggest_xg_overperformance_shot_game], 0, False)],
                              ["Biggest shot chance missed (xG)", round(my_biggest_xg_miss_from_shot, 6),
                               round(your_biggest_xg_miss_from_shot, 6), link_replay(my_biggest_xg_miss_from_shot_file,0, False), link_replay(your_biggest_xg_miss_from_shot_file,0, False)],
                              ["Unlikeliest shot-goal scored (xG)", round(my_lowest_xg_goal_from_shot, 6),
                               round(your_lowest_xg_goal_from_shot, 6), link_replay(my_lowest_xg_goal_from_shot_file,0, False), link_replay(your_lowest_xg_goal_from_shot_file,0, False)],
                              ["Biggest non-shot chance missed (xG)", round(my_biggest_xg_miss_from_nonshot, 6),
                               round(your_biggest_xg_miss_from_nonshot, 6), link_replay(my_biggest_xg_miss_from_nonshot_file,0, False),link_replay(your_biggest_xg_miss_from_nonshot_file,0, False)],
                              ["Unlikeliest non-shot-goal scored (xG)", round(my_lowest_xg_goal_from_nonshot, 6),
                               round(your_lowest_xg_goal_from_nonshot, 6), link_replay(my_lowest_xg_goal_from_nonshot_file,0, False),link_replay(your_lowest_xg_goal_from_nonshot_file,0, False)],
                              ["Furthest goal scored (m)", round(my_furthest_goal_scored / 100),
                               round(your_furthest_goal_scored / 100)],
                              ["Highest goal scored (m)", round(my_highest_goal_scored / 100),
                               round(your_highest_goal_scored / 100)],
                              ["Most consecutive matches returned in", my_most_consecutive_games_returned_in,
                               your_most_consecutive_games_returned_in],
                              ["Most consecutive matches blanked in", my_most_consecutive_games_blanked_in,
                               your_most_consecutive_games_blanked_in],
                              ["Most consecutive MVPs (no tiebreaker)", my_most_consecutive_mvp,
                               your_most_consecutive_mvp],
                              ["Most consecutive matches without MVP", my_most_consecutive_nomvp_in,
                               your_most_consecutive_nomvp_in],
                              ["Most consecutive goals from shots", my_most_consecutive_goals_from_shots,
                               your_most_consecutive_goals_from_shots],
                              ["Most consecutive misses from shots", my_most_consecutive_misses_from_shots,
                               your_most_consecutive_misses_from_shots],
                              ["Most goal involvements (G+A) in one match", my_most_goals_or_assists_in_one_game,
                               your_most_goals_or_assists_in_one_game],
                              ["Most consecutive matches with a goal involvement",
                               my_most_consecutive_games_scored_or_assisted_in,
                               your_most_consecutive_games_scored_or_assisted_in],
                              ["Most consecutive matches without a goal involvement",
                               my_most_consecutive_games_ftsoa_in, your_most_consecutive_games_ftsoa_in],
                              ["Most hits in one match", max(my_hits_over_time), max(your_hits_over_time),
                              link_replay(new_json_files[my_hits_over_time.index(max(my_hits_over_time))], 0,
                                          False),
                              link_replay(new_json_files[your_hits_over_time.index(max(your_hits_over_time))], 0,
                                          False)],
                              ["Least hits in one match", min(my_hits_over_time), min(your_hits_over_time),
                               link_replay(new_json_files[my_hits_over_time.index(min(my_hits_over_time))], 0,
                                           False),
                               link_replay(new_json_files[your_hits_over_time.index(min(your_hits_over_time))], 0,
                                           False)],
                              ]

    content = tabulate(individual_record_data,
                       headers=["Record", my_alias, your_alias, "My latest replay", "Your latest replay"],
                       numalign="right",
                       tablefmt="tsv")
    if not os.path.exists(path_to_tables + "player_records.tsv"):
        open(path_to_tables + "player_records.tsv", 'w').close()
    f = open(path_to_tables + "player_records.tsv", "w")
    f.write(content)
    f.close()

    ### Team Records
    biggest_winstreak = 0
    biggest_lossstreak = 0
    winstreak_helper = 0
    lossstreak_helper = 0
    biggest_50plus_streak = 0
    biggest_lessthan50_streak = 0
    helper_50plus = 0
    helper_lessthan50 = 0
    biggest_scoredstreak = 0
    biggest_concededstreak = 0
    biggest_ftscorestreak = 0
    biggest_csstreak = 0
    scoredstreak_helper = 0
    concededstreak_helper = 0
    ftscorestreak_helper = 0
    csstreak_helper = 0
    our_unlikeliest_win_pct_in_a_win = 0
    our_likeliest_win_pct_in_a_win = 0
    their_unlikeliest_win_pct_in_a_win = 0
    their_likeliest_win_pct_in_a_win = 0

    our_unlikeliest_win_gs = 0
    our_unlikeliest_win_gc = 0
    our_unlikeliest_win_xgs = 0
    our_unlikeliest_win_xgc = 0
    our_likeliest_win_gs = 0
    our_likeliest_win_gc = 0
    our_likeliest_win_xgs = 0
    our_likeliest_win_xgc = 0

    their_unlikeliest_win_gs = 0
    their_unlikeliest_win_gc = 0
    their_unlikeliest_win_xgs = 0
    their_unlikeliest_win_xgc = 0
    their_likeliest_win_gs = 0
    their_likeliest_win_gc = 0
    their_likeliest_win_xgs = 0
    their_likeliest_win_xgc = 0

    firstwin_pos = 0
    firstloss_pos = 0

    our_highest_total_pts = 0
    our_lowest_total_pts = my_scores_over_time[0] + your_scores_over_time[0]

    for result in range(len(result_array)):
        if (my_scores_over_time[result] + your_scores_over_time[result]) > our_highest_total_pts:
            our_highest_total_pts = (my_scores_over_time[result] + your_scores_over_time[result])

        if (my_scores_over_time[result] + your_scores_over_time[result]) < our_lowest_total_pts:
            our_lowest_total_pts = (my_scores_over_time[result] + your_scores_over_time[result])

        if result_array[result] == "W":
            if firstwin_pos == 0:
                firstwin_pos = result
                our_unlikeliest_win_gs = gs_array[result]
                our_unlikeliest_win_gc = gc_array[result]
                our_unlikeliest_win_xgs = our_xg_over_time[result]
                our_unlikeliest_win_xgc = their_xg_over_time[result]
                our_likeliest_win_gs = gs_array[result]
                our_likeliest_win_gc = gc_array[result]
                our_likeliest_win_xgs = our_xg_over_time[result]
                our_likeliest_win_xgc = their_xg_over_time[result]

            if result == firstwin_pos:
                our_unlikeliest_win_pct_in_a_win = win_chance_per_game[result]
                our_likeliest_win_pct_in_a_win = win_chance_per_game[result]

            else:
                if win_chance_per_game[result] < our_unlikeliest_win_pct_in_a_win:
                    our_unlikeliest_win_pct_in_a_win = win_chance_per_game[result]
                    our_unlikeliest_win_gs = gs_array[result]
                    our_unlikeliest_win_gc = gc_array[result]
                    our_unlikeliest_win_xgs = our_xg_over_time[result]
                    our_unlikeliest_win_xgc = their_xg_over_time[result]
                if win_chance_per_game[result] > our_likeliest_win_pct_in_a_win:
                    our_likeliest_win_pct_in_a_win = win_chance_per_game[result]
                    our_likeliest_win_gs = gs_array[result]
                    our_likeliest_win_gc = gc_array[result]
                    our_likeliest_win_xgs = our_xg_over_time[result]
                    our_likeliest_win_xgc = their_xg_over_time[result]

            winstreak_helper += 1
            lossstreak_helper = 0
            if winstreak_helper > biggest_winstreak:
                biggest_winstreak = winstreak_helper

        if result_array[result] == "L":
            if firstloss_pos == 0:
                firstloss_pos = result
                their_unlikeliest_win_gs = gc_array[result]
                their_unlikeliest_win_gc = gs_array[result]
                their_unlikeliest_win_xgs = their_xg_over_time[result]
                their_unlikeliest_win_xgc = our_xg_over_time[result]
                their_likeliest_win_gs = gc_array[result]
                their_likeliest_win_gc = gs_array[result]
                their_likeliest_win_xgs = their_xg_over_time[result]
                their_likeliest_win_xgc = our_xg_over_time[result]

            if result == firstloss_pos:
                their_unlikeliest_win_pct_in_a_win = loss_chance_per_game[result]
                their_likeliest_win_pct_in_a_win = loss_chance_per_game[result]

            else:
                if loss_chance_per_game[result] < their_unlikeliest_win_pct_in_a_win:
                    their_unlikeliest_win_pct_in_a_win = loss_chance_per_game[result]
                    their_unlikeliest_win_gs = gc_array[result]
                    their_unlikeliest_win_gc = gs_array[result]
                    their_unlikeliest_win_xgs = their_xg_over_time[result]
                    their_unlikeliest_win_xgc = our_xg_over_time[result]
                if loss_chance_per_game[result] > their_likeliest_win_pct_in_a_win:
                    their_likeliest_win_pct_in_a_win = loss_chance_per_game[result]
                    their_likeliest_win_gs = gc_array[result]
                    their_likeliest_win_gc = gs_array[result]
                    their_likeliest_win_xgs = their_xg_over_time[result]
                    their_likeliest_win_xgc = our_xg_over_time[result]

            lossstreak_helper += 1
            winstreak_helper = 0
            if lossstreak_helper > biggest_lossstreak:
                biggest_lossstreak = lossstreak_helper

        if win_chance_per_game[result] >= 50:
            helper_50plus += 1
            helper_lessthan50 = 0
            if helper_50plus > biggest_50plus_streak:
                biggest_50plus_streak = helper_50plus

        if win_chance_per_game[result] < 50:
            helper_lessthan50 += 1
            helper_50plus = 0
            if helper_lessthan50 > biggest_lessthan50_streak:
                biggest_lessthan50_streak = helper_lessthan50

        if gs_array[result] > 0:
            scoredstreak_helper += 1
            ftscorestreak_helper = 0
        else:
            ftscorestreak_helper += 1
            scoredstreak_helper = 0

        if gc_array[result] > 0:
            concededstreak_helper += 1
            csstreak_helper = 0
        else:
            csstreak_helper += 1
            concededstreak_helper = 0

        if concededstreak_helper > biggest_concededstreak:
            biggest_concededstreak = concededstreak_helper
        if csstreak_helper > biggest_csstreak:
            biggest_csstreak = csstreak_helper
        if scoredstreak_helper > biggest_scoredstreak:
            biggest_scoredstreak = scoredstreak_helper
        if ftscorestreak_helper > biggest_ftscorestreak:
            biggest_ftscorestreak = ftscorestreak_helper

    team_record_data = [["Longest winstreak", biggest_winstreak, biggest_lossstreak],
                        ["Most consecutive games with a win chance of at least 50%", biggest_50plus_streak,
                         biggest_lessthan50_streak],
                        ["Most goals scored in one match", max(gs_array), max(gc_array)],
                        ["Biggest winning margin", max(gd_array), abs(min(gd_array))],
                        ["Most consecutive games scored in", biggest_scoredstreak, biggest_concededstreak],
                        ["Most consecutive games failed to score in", biggest_ftscorestreak, biggest_csstreak],
                        ["Most shots in one match", max(our_shots_over_time), max(their_shots_over_time)],
                        ["Most assists in one match", max(our_assists_over_time), max(their_assists_over_time)],
                        ["Most saves in one match", max(our_saves_over_time), max(their_saves_over_time)],
                        ["Highest xG in one match", round(max(our_xg_over_time), 2), round(max(their_xg_over_time), 2)],
                        ["Highest shot xG in one match", round(max(our_shot_xg_over_time), 2),
                         round(max(their_shot_xg_over_time), 2)],
                        ["Highest non-shot xG in one match", round(max(our_nonshot_xg_over_time), 2),
                         round(max(their_nonshot_xg_over_time), 2)],
                        ["Lowest xG in one match", round(min(our_xg_over_time), 2), round(min(their_xg_over_time), 2)],
                        ["Highest xG without scoring in one match (only shot-goals)",
                         round(our_highest_xg_without_scoring, 2), round(their_highest_xg_without_scoring, 2)],
                        ["Biggest xG overperformance in one match (only shot-goals)",
                         str(our_biggest_xg_overperformance_goals) + "G from " + str(
                             round(our_biggest_xg_overperformance_xg, 2)) + " xG",
                         str(their_biggest_xg_overperformance_goals) + "G from " + str(
                             round(their_biggest_xg_overperformance_xg, 2)) + " xG"],
                        ["Biggest xG overperformance in one match (only shot-goals) %", "%.0f" % (((
                                                                                                           our_biggest_xg_overperformance_goals / our_biggest_xg_overperformance_xg) * 100) - 100) + "%",
                         "%.0f" % (((
                                            their_biggest_xg_overperformance_goals / their_biggest_xg_overperformance_xg) * 100) - 100) + "%"],

                        ["Biggest shot chance missed (xG)", round(our_biggest_xg_miss_from_shot, 6),
                         round(their_biggest_xg_miss_from_shot, 6)],
                        ["Unlikeliest shot-goal scored (xG)", round(our_lowest_xg_goal_from_shot, 6),
                         round(their_lowest_xg_goal_from_shot, 6)],
                        ["Biggest non-shot chance missed (xG)", round(our_biggest_xg_miss_from_nonshot, 6),
                         round(their_biggest_xg_miss_from_nonshot, 6)],
                        ["Unlikeliest non-shot-goal scored (xG)", round(our_lowest_xg_goal_from_nonshot, 6),
                         round(their_lowest_xg_goal_from_nonshot, 6)],
                        ["Furthest goal scored (m)",
                         round(max(my_goals_distancetogoal + your_goals_distancetogoal) / 100),
                         round(max(their_goals_distancetogoal) / 100)],
                        ["Highest goal scored (m)", round(max(my_goals_z + your_goals_z) / 100),
                         round(max(their_goals_z) / 100)],
                        ["Most consecutive MVPs (no tiebreaker)", our_most_consecutive_mvp,
                         their_most_consecutive_mvp],
                        ["Most consecutive matches without MVP", our_most_consecutive_nomvp_in,
                         their_most_consecutive_nomvp_in],
                        ["Most consecutive goals from shots", our_most_consecutive_goals_from_shots,
                         their_most_consecutive_goals_from_shots],
                        ["Most consecutive misses from shots", our_most_consecutive_misses_from_shots,
                         their_most_consecutive_misses_from_shots],
                        ["Unlikeliest win scoreline vs expected scoreline",
                         str(our_unlikeliest_win_gs) + "-" + str(our_unlikeliest_win_gc) + " (" + str(
                             round(our_unlikeliest_win_xgs, 2)) + "-" + str(round(our_unlikeliest_win_xgc, 2)) + ")",
                         str(their_unlikeliest_win_gs) + "-" + str(their_unlikeliest_win_gc) + " (" + str(
                             round(their_unlikeliest_win_xgs, 2)) + "-" + str(
                             round(their_unlikeliest_win_xgc, 2)) + ")"],
                        ["Unlikeliest win % in a win", "%.2f" % our_unlikeliest_win_pct_in_a_win + "%",
                         "%.2f" % their_unlikeliest_win_pct_in_a_win + "%"],
                        ["Likeliest win scoreline vs expected scoreline",
                         str(our_likeliest_win_gs) + "-" + str(our_likeliest_win_gc) + " (" + str(
                             round(our_likeliest_win_xgs,
                                   2)) + "-" + str(round(
                             our_likeliest_win_xgc, 2)) + ")",
                         str(their_likeliest_win_gs) + "-" + str(their_likeliest_win_gc) + " (" + str(
                             round(their_likeliest_win_xgs,
                                   2)) + "-" + str(round(
                             their_likeliest_win_xgc, 2)) + ")"],
                        ["Likeliest win % in a win", "%.2f" % our_likeliest_win_pct_in_a_win + "%",
                         "%.2f" % their_likeliest_win_pct_in_a_win + "%"],
                        ["Highest team score", our_highest_total_pts, max(their_scores_over_time)],
                        ["Lowest team score", our_lowest_total_pts, min(their_scores_over_time)],
                        ["Most hits in one match", max(our_hits_over_time), max(their_hits_over_time)],
                        ["Least hits in one match", min(our_hits_over_time), min(their_hits_over_time)]
                        ]

    content = tabulate(team_record_data, headers=["Record", "Our Team", "Opponents"], numalign="right", tablefmt="tsv")
    if not os.path.exists(path_to_tables + "player_records.tsv"):
        open(path_to_tables + "team_records.tsv", 'w').close()
    f = open(path_to_tables + "team_records.tsv", "w")
    f.write(content)
    f.close()

    ###########
    fig = plt.figure(figsize=(40, 20))
    n_plots = 26
    widths = [1]
    heights = [1] * n_plots
    spec = fig.add_gridspec(ncols=1, nrows=n_plots, width_ratios=widths, height_ratios=heights)

    pitch_min_x = 4500
    pitch_min_y = -6300

    pitch_max_x = pitch_min_x * -1
    pitch_max_y = pitch_min_y * -1

    our_xg_diff_over_time = []
    for xg in range(len(my_xg_over_time)):
        our_xg_diff_over_time.append(my_xg_over_time[xg] + your_xg_over_time[xg] - their_xg_over_time[xg])

    ax1 = fig.add_subplot(spec[0, 0])  # results
    ax1.bar(range(len(gd_array)), gd_array, color=result_color, alpha=0.75)
    min_gd = min(gd_array)
    max_gd = max(gd_array)
    min_xgd = min(our_xg_diff_over_time)
    max_xgd = max(our_xg_diff_over_time)
    gd_lim = max(abs(min_gd), max_gd, abs(min_xgd), max_xgd)
    ax1.set_ylim(-gd_lim, gd_lim)
    ax1.set_xlim(-1, len(gd_array))
    ax1.axis("off")
    ax1.plot(range(len(gd_array)), our_xg_diff_over_time, color="black", alpha=1)

    plt.axhline(y=0, color='black', linestyle=':')

    for streak_game_num in streak_start_games:
        plt.axvline(x=streak_game_num - 0.5, color='grey', linestyle='-', alpha=0.25)

    ax3 = fig.add_subplot(spec[2, 0])  # Results

    sizes = [our_win_ratio, our_loss_ratio]
    labels = "Win %", "Loss %"
    ax3.pie(sizes, colors=[our_color, their_color], startangle=90, autopct='%1.1f%%', explode=(0.1, 0), shadow=True,
            textprops={'color': "black", 'bbox': dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
                       })
    ax3.set_title(str(games_nr) + " Games:")

    ax4 = fig.add_subplot(spec[3, 0])  # My heatmap
    ax4.set_title(my_alias + "'s Touches")
    ax4.set_xlim(pitch_min_x, pitch_max_x)
    ax4.set_ylim(pitch_min_y, pitch_max_y)
    ax4.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    # remove touches near kick off
    new_my_touches_x = []
    new_my_touches_y = []
    for touch in range(0, len(my_touches_y)):
        if not ((-350 < int(my_touches_x[touch]) < 350) and (my_touches_y[touch]) > -370 and int(
                my_touches_y[touch]) < 240):
            new_my_touches_x.append(my_touches_x[touch])
            new_my_touches_y.append(my_touches_y[touch])

    ax4.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    heatmap, xedges, yedges = np.histogram2d(new_my_touches_y + [pitch_min_y, pitch_max_y],
                                             new_my_touches_x + [pitch_min_x, pitch_max_x], bins=80)
    im = ax4.imshow(convolve(heatmap, Gaussian2DKernel(x_stddev=1, y_stddev=1)),
                    extent=[pitch_max_x, pitch_min_x, pitch_max_y, pitch_min_y], alpha=0.75)
    im.set_cmap('gist_gray_r')
    ax4.axis("off")

    ax5 = fig.add_subplot(spec[3, 0])  # My heatmap
    ax5.set_title(your_alias + "'s Touches")
    ax5.set_xlim(pitch_min_x, pitch_max_x)
    ax5.set_ylim(pitch_min_y, pitch_max_y)
    ax5.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    # remove touches near kick off
    new_your_touches_x = []
    new_your_touches_y = []
    for touch in range(0, len(your_touches_y)):
        if not ((-350 < int(your_touches_x[touch]) < 350) and (your_touches_y[touch]) > -370 and int(
                your_touches_y[touch]) < 240):
            new_your_touches_x.append(your_touches_x[touch])
            new_your_touches_y.append(your_touches_y[touch])

    ax5.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    heatmap, xedges, yedges = np.histogram2d(new_your_touches_y + [pitch_min_y, pitch_max_y],
                                             new_your_touches_x + [pitch_min_x, pitch_max_x], bins=80)
    im = ax5.imshow(convolve(heatmap, Gaussian2DKernel(x_stddev=1, y_stddev=1)),
                    extent=[pitch_max_x, pitch_min_x, pitch_max_y, pitch_min_y], alpha=0.75)
    im.set_cmap('gist_gray_r')
    ax5.axis("off")

    ##########
    # positional tendencies chart

    ax22 = fig.add_subplot(spec[5, 0])  # Team balance horizontal stacked bar chart

    dic = {1: "Ground", 2: "Low Air", 3: "High Air", 4: "Def 1/2", 5: "Att 1/2", 6: "Def 1/3", 7: "Mid 1/3",
           8: "Att 1/3", 9: "Behind Ball", 10: "In Front of Ball", 11: "Near Wall", 12: "In Corner", 13: "On Wall",
           14: "Full Boost", 15: "Low Boost", 16: "No Boost", 17: "Closest to Ball", 18: "Close to Ball",
           19: "Furthest from Ball",
           20: "Slow Speed", 21: "Boost Speed", 22: "Supersonic", 23: "Carrying Ball"}

    ticks = []

    for num in dic:
        ticks.append(num)

    ax22.set_yticks(ticks)

    labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]

    ax22.set_yticklabels(labels)
    ax22.set_xticklabels("")
    ax22.tick_params(bottom=False)  # remove the ticks

    ax22.set_xlim(0, 1)

    for stat in range(0, len(my_pos_tendencies)):
        if (my_pos_tendencies[stat] + your_pos_tendencies[stat]) > 0:
            our_local_total_tendency = my_pos_tendencies[stat] + your_pos_tendencies[stat]
            my_local_stat_share = my_pos_tendencies[stat] / our_local_total_tendency
            your_local_stat_share = your_pos_tendencies[stat] / our_local_total_tendency
        else:
            my_local_stat_share = 0
            your_local_stat_share = 0

        ax22.barh(stat + 1, my_local_stat_share, color=my_color)
        ax22.barh(stat + 1, your_local_stat_share, left=my_local_stat_share, color=your_color)

    label_count = 0
    for c in ax22.containers:
        # customize the label to account for cases when there might not be a bar section
        labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

        labels[0] = ""

        for stat in range(len(my_pos_tendencies)):
            if label_count == stat * 2 and (my_pos_tendencies[stat] / games_nr) > 0:
                if (my_pos_tendencies[stat] / games_nr) < 1:
                    initialMS = (my_pos_tendencies[stat] / games_nr) * 1000
                    labels[0] = str("%.0f" % initialMS) + "ms"
                else:
                    minutes_to_show, seconds_to_show = divmod((my_pos_tendencies[stat] / games_nr), 60)
                    labels[0] = "%1d:%02d" % (minutes_to_show, seconds_to_show)
            if label_count == ((stat * 2) + 1) and (your_pos_tendencies[stat] / games_nr) > 0:
                if (your_pos_tendencies[stat] / games_nr) < 1:
                    initialMS = (your_pos_tendencies[stat] / games_nr) * 1000
                    labels[0] = str("%.0f" % initialMS) + "ms"
                else:
                    minutes_to_show, seconds_to_show = divmod((your_pos_tendencies[stat] / games_nr), 60)
                    labels[0] = "%1d:%02d" % (minutes_to_show, seconds_to_show)

        # set the bar label
        ax22.bar_label(c, labels=labels, label_type='center', color="white")
        label_count += 1

    plt.axvline(x=0.5, color='white', linestyle='-', alpha=0.5, linewidth=1)
    ax22.set_title("Positional Tendencies (per game)\nMinutes:Seconds")

    ###########################

    my_stats = [my_goal_count, my_goals_from_shots, my_goals_from_nonshots, my_other_goals,
                my_total_xg, my_shot_xg, my_nonshot_xg,
                my_gfs_xg_ratio * games_nr, my_gs_ratio * games_nr,
                my_shot_count, my_miss_count, my_assists_count, my_saves_count, my_touches_count,
                my_passes_count, my_dribbles_count, my_clears_count, my_aerials_count, my_turnovers_won_count,
                my_turnovers_count,
                my_demos_count, my_demos_conceded_count, my_mvp_count, my_score_count, my_hit_count]

    your_stats = [your_goal_count, your_goals_from_shots, your_goals_from_nonshots, your_other_goals,
                  your_total_xg, your_shot_xg, your_nonshot_xg,
                  your_gfs_xg_ratio * games_nr, your_gs_ratio * games_nr,
                  your_shot_count, your_miss_count, your_assists_count, your_saves_count, your_touches_count,
                  your_passes_count, your_dribbles_count, your_clears_count, your_aerials_count,
                  your_turnovers_won_count, your_turnovers_count,
                  your_demos_count, your_demos_conceded_count, your_mvp_count, your_score_count, your_hit_count]

    my_stats.reverse()
    your_stats.reverse()

    ax6 = fig.add_subplot(spec[5, 0])  # Team balance horizontal stacked bar chart

    dic = {1: "Goals", 2: "Shot Goals", 3: "Non-shot Goals", 4: "Other Goals",
           5: "xG", 6: "Shot xG", 7: "Non-shot xG",
           8: "GfS/xG", 9: "GfS/Shots",
           10: "Shots", 11: "Misses", 12: "Assists", 13: "Saves", 14: "Touches",
           15: "Passes", 16: "Dribbles", 17: "Clears", 18: "Aerials", 19: "Won Ball", 20: "Lost Ball",
           21: "Demos", 22: "Demoed", 23: "MVPs", 24: "Scores", 25: "Hits"}

    dic_rev = {len(dic) - i + 1: v for (i, v) in dic.items()}
    dic = dic_rev

    ticks = []

    for num in dic:
        ticks.append(num)

    ax6.set_yticks(ticks)

    labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]
    labels_to_check = labels

    ax6.set_yticklabels(labels)
    ax6.set_xticklabels("")
    ax6.tick_params(bottom=False)  # remove the ticks

    ax6.set_xlim(0, 1)

    for stat in range(len(my_stats)):
        if (my_stats[stat] + your_stats[stat]) > 0:
            our_local_total_stat = my_stats[stat] + your_stats[stat]
            my_local_stat_share = my_stats[stat] / our_local_total_stat
            your_local_stat_share = your_stats[stat] / our_local_total_stat
        else:
            my_local_stat_share = 0
            your_local_stat_share = 0

        ax6.barh(stat + 1, my_local_stat_share, color=my_color)
        ax6.barh(stat + 1, your_local_stat_share, left=my_local_stat_share, color=your_color)

    label_count = 0
    for c in ax6.containers:
        # customize the label to account for cases when there might not be a bar section
        labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

        labels[0] = ""

        for stat in range(len(my_stats)):
            if label_count == stat * 2 and (my_stats[stat] / games_nr) > 0:
                labels[0] = "%.2f" % (my_stats[stat] / games_nr)
            if label_count == ((stat * 2) + 1) and (your_stats[stat] / games_nr) > 0:
                labels[0] = "%.2f" % (your_stats[stat] / games_nr)

        # set the bar label
        ax6.bar_label(c, labels=labels, label_type='center', color="white")
        label_count += 1
    plt.axvline(x=0.5, color='white', linestyle='-', alpha=0.5, linewidth=1)
    ax6.set_title(my_alias + " - " + your_alias + " (per Game)")

    ###########################

    our_stats = []
    labels_to_exclude = ["Demoed", "Lost Ball", "MVPs"]
    labels_div_by_2 = ["GfS/Shots", "GfS/xG"]

    labels_to_check.reverse()

    for stat in range(len(my_stats)):
        # exclude: demos_conceded, turnovers, mvp count
        if labels_to_check[stat] not in labels_to_exclude:
            # gs ratio and gfs/xg ratio require division by 2
            if labels_to_check[stat] in labels_div_by_2:
                our_stats.append((my_stats[stat] + your_stats[stat]) / 2)
            else:
                our_stats.append(my_stats[stat] + your_stats[stat])
        # mvp count
        else:
            if labels_to_check[stat] == "MVPs":
                our_stats.append(our_mvp_count)

    their_stats = [their_goal_count, their_goals_from_shots, their_goals_from_nonshots, their_other_goals,
                   their_total_xg, their_shot_xg, their_nonshot_xg,
                   their_gfs_xg_ratio * games_nr, their_gs_ratio * games_nr,
                   their_shot_count, their_miss_count, their_assists_count, their_saves_count, their_touches_count,
                   their_passes_count, their_dribbles_count, their_clears_count, their_aerials_count,
                   their_turnovers_won_count,
                   their_demos_count, their_mvp_count, their_score_count, their_hit_count]

    their_stats.reverse()

    ax7 = fig.add_subplot(spec[6, 0])  # Horizontal stacked bar chart (us vs opponent)

    dic = {1: "Goals", 2: "Shot Goals", 3: "Non-shot Goals", 4: "Other Goals",
           5: "xG", 6: "Shot xG", 7: "Non-shot xG",
           8: "GfS/xG", 9: "GfS/Shots",
           10: "Shots", 11: "Misses", 12: "Assists", 13: "Saves", 14: "Touches",
           15: "Passes", 16: "Dribbles", 17: "Clears", 18: "Aerials", 19: "Won Ball",
           20: "Demos", 21: "MVPs", 22: "Scores", 23: "Hits"}

    dic_rev = {len(dic) - i + 1: v for (i, v) in dic.items()}
    dic = dic_rev

    ticks = []

    for num in dic:
        ticks.append(num)

    ax7.set_yticks(ticks)

    labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]
    ax7.set_yticklabels(labels)
    ax7.set_xticklabels("")
    ax7.tick_params(bottom=False)  # remove the ticks

    ax7.set_xlim(0, 1)

    for stat in range(len(our_stats)):
        if (our_stats[stat] + their_stats[stat]) > 0:
            all_local_total_stat = our_stats[stat] + their_stats[stat]
            our_local_stat_share = our_stats[stat] / all_local_total_stat
            their_local_stat_share = their_stats[stat] / all_local_total_stat
        else:
            our_local_stat_share = 0
            their_local_stat_share = 0

        ax7.barh(stat + 1, our_local_stat_share, color=our_color)
        ax7.barh(stat + 1, their_local_stat_share, left=our_local_stat_share, color=their_color)

    label_count = 0
    for c in ax7.containers:
        # customize the label to account for cases when there might not be a bar section
        labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

        labels[0] = ""

        for stat in range(len(our_stats)):
            if label_count == stat * 2 and (our_stats[stat] / games_nr) > 0:
                labels[0] = "%.2f" % (our_stats[stat] / games_nr)
            if label_count == ((stat * 2) + 1) and (their_stats[stat] / games_nr) > 0:
                labels[0] = "%.2f" % (their_stats[stat] / games_nr)

        # set the bar label
        ax7.bar_label(c, labels=labels, label_type='center', color="white")
        label_count += 1

    plt.axvline(x=0.5, color='white', linestyle='-', alpha=0.5, linewidth=1)
    ax7.set_title("Us - Opponents (per Game)")

    ###########################

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

    ax8.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25)
    ax8.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25)

    ax8.bar(range(1, games_nr + 1), my_goals_over_time, color=my_color, width=1)
    ax8.bar(range(1, games_nr + 1), your_goals_over_time, color=your_color, bottom=my_goals_over_time, width=1)
    ax8.bar(range(1, games_nr + 1), their_goals_over_time, color=their_color, width=1)
    for streak_game_num in streak_start_games:
        plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
    ax8.set_ylabel("GOALS", rotation="horizontal", ha="center", va="center", labelpad=35)

    for entry in range(0, len(their_shots_over_time)):
        their_shots_over_time[entry] *= -1

    ax9 = fig.add_subplot(spec[0, 0])  # our goals over time
    ax9.set_xlim(0.5, games_nr + 0.5)
    limit1 = min(their_shots_over_time)
    limit2 = max(our_shots_over_time)
    limit = max(abs(limit1), limit2)
    ax9.set_ylim(-limit, limit)

    for entry in range(0, len(result_array_num)):
        new_result_array_num_up = limit
        new_result_array_num_down = -limit

    ax9.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25)
    ax9.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25)

    ax9.bar(range(1, games_nr + 1), my_shots_over_time, color=my_color, width=1)
    ax9.bar(range(1, games_nr + 1), your_shots_over_time, color=your_color, bottom=my_shots_over_time, width=1)
    ax9.bar(range(1, games_nr + 1), their_shots_over_time, color=their_color, width=1)
    ax9.set_xticklabels("")
    for streak_game_num in streak_start_games:
        plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
    ax9.set_ylabel("SHOTS", rotation="horizontal", ha="center", va="center", labelpad=35)

    for entry in range(0, len(their_saves_over_time)):
        their_saves_over_time[entry] *= -1

    ax10 = fig.add_subplot(spec[0, 0])  # our saves over time
    ax10.set_xlim(0.5, games_nr + 0.5)
    limit1 = min(their_saves_over_time)
    limit2 = max(our_saves_over_time)
    limit = max(abs(limit1), limit2)

    for entry in range(0, len(result_array_num)):
        new_result_array_num_up = limit
        new_result_array_num_down = -limit

    ax10.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25)
    ax10.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25)

    ax10.set_ylim(-limit, limit)
    ax10.bar(range(1, games_nr + 1), my_saves_over_time, color=my_color, width=1)
    ax10.bar(range(1, games_nr + 1), your_saves_over_time, color=your_color, bottom=my_saves_over_time, width=1)
    ax10.bar(range(1, games_nr + 1), their_saves_over_time, color=their_color, width=1)
    ax10.set_xticklabels("")
    for streak_game_num in streak_start_games:
        plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
    ax10.set_ylabel("SAVES", rotation="horizontal", ha="center", va="center", labelpad=35)

    for entry in range(0, len(their_assists_over_time)):
        their_assists_over_time[entry] *= -1

    ax11 = fig.add_subplot(spec[0, 0])  # our assists over time
    ax11.set_xlim(0.5, games_nr + 0.5)
    limit1 = min(their_assists_over_time)
    limit2 = max(our_assists_over_time)
    limit = max(abs(limit1), limit2)
    ax11.set_ylim(-limit, limit)

    for entry in range(0, len(result_array_num)):
        new_result_array_num_up = limit
        new_result_array_num_down = -limit

    ax11.bar(range(1, games_nr + 1), new_result_array_num_up, color=result_color, width=1, alpha=0.25)
    ax11.bar(range(1, games_nr + 1), new_result_array_num_down, color=result_color, width=1, alpha=0.25)

    ax11.bar(range(1, games_nr + 1), my_assists_over_time, color=my_color, width=1)
    ax11.bar(range(1, games_nr + 1), your_assists_over_time, color=your_color, bottom=my_assists_over_time, width=1)
    ax11.bar(range(1, games_nr + 1), their_assists_over_time, color=their_color, width=1)
    ax11.set_xticklabels("")
    for streak_game_num in streak_start_games:
        plt.axvline(x=streak_game_num + 0.5, color='black', linestyle='-')
    ax11.set_ylabel("ASSISTS", rotation="horizontal", ha="center", va="center", labelpad=35)

    my_goal_sizes_for_scatter = []
    goal_size_multiplier = 160

    for xg in my_xg_per_shot_goal_list:
        my_goal_sizes_for_scatter.append(xg * goal_size_multiplier)

    ax13 = fig.add_subplot(spec[4, 0])  # Heatmap of Allan's goals
    heatmap, xedges, yedges = np.histogram2d(my_shots_y + [pitch_min_y] + [pitch_max_y],
                                             my_shots_x + [pitch_min_x] + [pitch_max_x], bins=100)
    ax13.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    im = ax13.imshow(convolve(heatmap, Gaussian2DKernel(x_stddev=5, y_stddev=5)),
                     extent=[pitch_max_x, pitch_min_x, pitch_max_y, pitch_min_y], alpha=0.5)
    im.set_cmap('gist_gray_r')

    ax13.scatter(my_goals_x, my_goals_y, alpha=goal_scatter_alpha, color=my_color, s=my_goal_sizes_for_scatter)

    ax13.set_xlim(pitch_min_x, pitch_max_x)
    ax13.set_ylim(pitch_min_y, pitch_max_y)
    ax13.axis("off")
    ax13.set_title(my_alias + "'s Shot & Goal Heatmap")

    your_goal_sizes_for_scatter = []
    for xg in your_xg_per_shot_goal_list:
        your_goal_sizes_for_scatter.append(xg * goal_size_multiplier)

    ax14 = fig.add_subplot(spec[4, 0])  # Heatmap of Sertalp's goals
    heatmap, xedges, yedges = np.histogram2d(your_shots_y + [pitch_min_y] + [pitch_max_y],
                                             your_shots_x + [pitch_min_x] + [pitch_max_x], bins=100)
    ax14.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    im = ax14.imshow(convolve(heatmap, Gaussian2DKernel(x_stddev=5, y_stddev=5)),
                     extent=[pitch_max_x, pitch_min_x, pitch_max_y, pitch_min_y], alpha=0.5)
    im.set_cmap('gist_gray_r')
    ax14.scatter(your_goals_x, your_goals_y, alpha=goal_scatter_alpha, color=your_color, s=your_goal_sizes_for_scatter)
    ax14.set_xlim(pitch_min_x, pitch_max_x)
    ax14.set_ylim(pitch_min_y, pitch_max_y)
    ax14.axis("off")
    ax14.set_title(your_alias + "'s Shot & Goal Heatmap")

    ax15 = fig.add_subplot(spec[4, 0])  # Heatmap of our team's goals
    heatmap, xedges, yedges = np.histogram2d(my_shots_y + your_shots_y + [pitch_min_y] + [pitch_max_y],
                                             my_shots_x + your_shots_x + [pitch_min_x] + [pitch_max_x], bins=100)
    ax15.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    im = ax15.imshow(convolve(heatmap, Gaussian2DKernel(x_stddev=5, y_stddev=5)),
                     extent=[pitch_max_x, pitch_min_x, pitch_max_y, pitch_min_y], alpha=0.5)
    im.set_cmap('gist_gray_r')
    ax15.scatter(my_goals_x + your_goals_x, my_goals_y + your_goals_y, alpha=goal_scatter_alpha, color=our_color,
                 s=my_goal_sizes_for_scatter + your_goal_sizes_for_scatter)
    ax15.set_xlim(pitch_min_x, pitch_max_x)
    ax15.set_ylim(pitch_min_y, pitch_max_y)
    ax15.axis("off")
    ax15.set_title("Our Shot & Goal Heatmap")

    their_goal_sizes_for_scatter = []
    for xg in their_xg_per_shot_goal_list:
        their_goal_sizes_for_scatter.append(xg * goal_size_multiplier)

    ax16 = fig.add_subplot(spec[4, 0])  # Heatmap of Sertalp's goals
    heatmap, xedges, yedges = np.histogram2d(their_shots_y + [pitch_min_y] + [pitch_max_y],
                                             their_shots_x + [pitch_min_x] + [pitch_max_x], bins=100)
    ax16.imshow(bg_img, extent=[pitch_min_x, pitch_max_x, pitch_min_y, pitch_max_y], alpha=1)
    im = ax16.imshow(convolve(heatmap, Gaussian2DKernel(x_stddev=5, y_stddev=5)),
                     extent=[pitch_max_x, pitch_min_x, pitch_max_y, pitch_min_y], alpha=0.5)
    im.set_cmap('gist_gray_r')
    ax16.scatter(their_goals_x, their_goals_y, alpha=goal_scatter_alpha, color=their_color,
                 s=their_goal_sizes_for_scatter)
    ax16.set_xlim(pitch_min_x, pitch_max_x)
    ax16.set_ylim(pitch_min_y, pitch_max_y)
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

    ax18 = fig.add_subplot(spec[2, 0])  # Overtime Results

    sizes = [our_NT_win_ratio, our_NT_loss_ratio]
    ax18.pie(sizes, colors=[our_color, their_color], startangle=90, autopct='%1.1f%%', explode=(0.1, 0), shadow=True,
             normalize=False,
             textprops={'color': "black", 'bbox': dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
                        })
    ax18.set_title(str(normaltime_games_count) + " Normaltime")

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

    rolling_avg_window = 10

    if games_nr < 30:
        rolling_avg_window = 1

    my_xg_over_time_rolling_avg = np.average(sliding_window_view(my_shot_xg_over_time, window_shape=rolling_avg_window),
                                             axis=1)
    my_goals_from_shots_over_time_rolling_avg = np.average(
        sliding_window_view(my_goals_from_shots_over_time, window_shape=rolling_avg_window), axis=1)
    your_xg_over_time_rolling_avg = np.average(
        sliding_window_view(your_shot_xg_over_time, window_shape=rolling_avg_window),
        axis=1)
    your_goals_from_shots_over_time_rolling_avg = np.average(
        sliding_window_view(your_goals_from_shots_over_time, window_shape=rolling_avg_window), axis=1)
    our_xg_over_time_rolling_avg = np.average(
        sliding_window_view(our_shot_xg_over_time, window_shape=rolling_avg_window),
        axis=1)
    our_goals_from_shots_over_time_rolling_avg = np.average(
        sliding_window_view(our_goals_from_shots_over_time, window_shape=rolling_avg_window), axis=1)
    their_xg_over_time_rolling_avg = np.average(
        sliding_window_view(their_shot_xg_over_time, window_shape=rolling_avg_window),
        axis=1)
    their_goals_from_shots_over_time_rolling_avg = np.average(
        sliding_window_view(their_goals_from_shots_over_time, window_shape=rolling_avg_window), axis=1)

    all_rolling_avg_max = max(max(my_xg_over_time_rolling_avg), max(my_goals_from_shots_over_time_rolling_avg),
                              max(your_xg_over_time_rolling_avg), max(your_goals_from_shots_over_time_rolling_avg),
                              max(our_xg_over_time_rolling_avg), max(our_goals_from_shots_over_time_rolling_avg),
                              max(their_xg_over_time_rolling_avg), max(their_goals_from_shots_over_time_rolling_avg))

    individual_rolling_avg_max = max(max(my_xg_over_time_rolling_avg), max(your_xg_over_time_rolling_avg),
                                     max(my_goals_from_shots_over_time_rolling_avg),
                                     max(your_goals_from_shots_over_time_rolling_avg))

    our_results_over_time = []
    for i in range(0, games_nr):
        if gd_array[i] > 0:
            our_results_over_time.append(100)
        else:
            our_results_over_time.append(0)

    our_winrate_over_time_rolling_avg = np.average(
        sliding_window_view(our_results_over_time, window_shape=rolling_avg_window), axis=1)
    our_xwinrate_over_time_rolling_avg = np.average(
        sliding_window_view(win_chance_per_game, window_shape=rolling_avg_window), axis=1)

    our_gd_over_time_rolling_avg = []
    our_xgd_from_shots_over_time_rolling_avg = []

    my_ra_bg_colors = []
    your_ra_bg_colors = []
    our_ra_bg_colors = []
    their_ra_bg_colors = []

    our_xdiff_ra_bg_colors = []
    our_gdiff_bar_colors = []

    our_winrate_bar_colors = []

    for val in range(0, len(my_xg_over_time_rolling_avg)):
        if my_xg_over_time_rolling_avg[val] > my_goals_from_shots_over_time_rolling_avg[val]:
            my_ra_bg_colors.append("red")
        elif my_xg_over_time_rolling_avg[val] == my_goals_from_shots_over_time_rolling_avg[val]:
            my_ra_bg_colors.append("yellow")
        else:
            my_ra_bg_colors.append("green")

        if your_xg_over_time_rolling_avg[val] > your_goals_from_shots_over_time_rolling_avg[val]:
            your_ra_bg_colors.append("red")
        elif your_xg_over_time_rolling_avg[val] == your_goals_from_shots_over_time_rolling_avg[val]:
            your_ra_bg_colors.append("yellow")
        else:
            your_ra_bg_colors.append("green")

        if our_xg_over_time_rolling_avg[val] > our_goals_from_shots_over_time_rolling_avg[val]:
            our_ra_bg_colors.append("red")
        elif our_xg_over_time_rolling_avg[val] == our_goals_from_shots_over_time_rolling_avg[val]:
            our_ra_bg_colors.append("yellow")
        else:
            our_ra_bg_colors.append("green")

        if their_xg_over_time_rolling_avg[val] > their_goals_from_shots_over_time_rolling_avg[val]:
            their_ra_bg_colors.append("red")
        elif their_xg_over_time_rolling_avg[val] == their_goals_from_shots_over_time_rolling_avg[val]:
            their_ra_bg_colors.append("yellow")
        else:
            their_ra_bg_colors.append("green")

        our_gd_over_time_rolling_avg.append(
            our_goals_from_shots_over_time_rolling_avg[val] - their_goals_from_shots_over_time_rolling_avg[val])
        our_xgd_from_shots_over_time_rolling_avg.append(
            our_xg_over_time_rolling_avg[val] - their_xg_over_time_rolling_avg[val])

        if our_gd_over_time_rolling_avg[val] > our_xgd_from_shots_over_time_rolling_avg[val]:
            our_xdiff_ra_bg_colors.append("green")
        elif our_gd_over_time_rolling_avg[val] == our_xgd_from_shots_over_time_rolling_avg[val]:
            our_xdiff_ra_bg_colors.append("yellow")
        else:
            our_xdiff_ra_bg_colors.append("red")

        if our_gd_over_time_rolling_avg[val] > 0:
            our_gdiff_bar_colors.append(our_color)
        elif our_gd_over_time_rolling_avg[val] == 0:
            our_gdiff_bar_colors.append("yellow")
        else:
            our_gdiff_bar_colors.append(their_color)

        if our_winrate_over_time_rolling_avg[val] > our_xwinrate_over_time_rolling_avg[val]:
            our_winrate_bar_colors.append("green")
        elif our_winrate_over_time_rolling_avg[val] == our_xwinrate_over_time_rolling_avg[val]:
            our_winrate_bar_colors.append("yellow")
        else:
            our_winrate_bar_colors.append("red")

    our_gd_xgd_ra_max = max(max(our_gd_over_time_rolling_avg), max(our_xgd_from_shots_over_time_rolling_avg))
    our_gd_xgd_ra_min = min(min(our_gd_over_time_rolling_avg), min(our_xgd_from_shots_over_time_rolling_avg))

    our_gd_ylim = our_gd_xgd_ra_max
    if abs(our_gd_xgd_ra_min) > our_gd_ylim:
        our_gd_ylim = abs(our_gd_xgd_ra_min)

    len_to_use = len(my_xg_over_time_rolling_avg)

    my_avg_xg_line = my_shot_xg / games_nr
    my_avg_gfs_line = my_goals_from_shots / games_nr
    your_avg_xg_line = your_shot_xg / games_nr
    your_avg_gfs_line = your_goals_from_shots / games_nr
    our_avg_xg_line = our_shot_xg / games_nr
    our_avg_gfs_line = (my_goals_from_shots + your_goals_from_shots) / games_nr
    their_avg_xg_line = their_shot_xg / games_nr
    their_avg_gfs_line = their_goals_from_shots / games_nr
    our_avg_xgd_line = (our_shot_xg - their_shot_xg) / games_nr
    our_avg_gdfs_line = (my_goals_from_shots + your_goals_from_shots - their_goals_from_shots) / games_nr
    our_avg_winrate_line = (win_count / games_nr) * 100
    our_avg_xwinrate_line = total_win_chance / games_nr

    ax2 = fig.add_subplot(spec[2, 0])
    ax2.bar(range(0, len_to_use), individual_rolling_avg_max, color=my_ra_bg_colors, alpha=0.1, width=1)
    ax2.bar(range(0, len_to_use), my_goals_from_shots_over_time_rolling_avg, color=my_color, alpha=0.5, width=1)
    ax2.plot(range(0, len_to_use), my_xg_over_time_rolling_avg, color="black", alpha=1)
    plt.axhline(y=my_avg_gfs_line, color=my_color, linestyle='dotted')
    plt.axhline(y=my_avg_xg_line, color='black', linestyle='dotted')
    ax2.set_title(
        my_alias + "'s Shot Goals and xG (black line) over time (" + str(rolling_avg_window) + " game rolling average)")
    ax2.set_ylim(0, individual_rolling_avg_max)
    ax2.set_xlim(0, len_to_use - 1)

    ax23 = fig.add_subplot(spec[2, 0])
    ax23.bar(range(0, len_to_use), individual_rolling_avg_max, color=your_ra_bg_colors, alpha=0.1, width=1)
    ax23.bar(range(0, len_to_use), your_goals_from_shots_over_time_rolling_avg, color=your_color, alpha=0.5, width=1)
    ax23.plot(range(0, len_to_use), your_xg_over_time_rolling_avg, color="black", alpha=1)
    plt.axhline(y=your_avg_gfs_line, color=your_color, linestyle='dotted')
    plt.axhline(y=your_avg_xg_line, color='black', linestyle='dotted')
    ax23.set_title(your_alias + "'s Shot Goals and xG (black line) over time (" + str(
        rolling_avg_window) + " game rolling average)")
    ax23.set_ylim(0, individual_rolling_avg_max)
    ax23.set_xlim(0, len_to_use - 1)

    for i in range(len(their_xg_over_time_rolling_avg)):
        their_xg_over_time_rolling_avg[i] *= -1
        their_goals_from_shots_over_time_rolling_avg[i] *= -1

    ax24 = fig.add_subplot(spec[2, 0])
    ax24.bar(range(0, len_to_use), all_rolling_avg_max, color=our_ra_bg_colors, alpha=0.1, width=1)
    ax24.bar(range(0, len_to_use), -all_rolling_avg_max, color=their_ra_bg_colors, alpha=0.1, width=1)
    ax24.bar(range(0, len_to_use), our_goals_from_shots_over_time_rolling_avg, color=our_color, alpha=0.5, width=1)
    ax24.bar(range(0, len_to_use), their_goals_from_shots_over_time_rolling_avg, color=their_color, alpha=0.5, width=1)
    ax24.plot(range(0, len_to_use), their_xg_over_time_rolling_avg, color="black", alpha=1)
    ax24.plot(range(0, len_to_use), our_xg_over_time_rolling_avg, color="black", alpha=1)
    plt.axhline(y=our_avg_gfs_line, color=our_color, linestyle='dotted')
    plt.axhline(y=our_avg_xg_line, color='black', linestyle='dotted')
    plt.axhline(y=-their_avg_gfs_line, color=their_color, linestyle='dotted')
    plt.axhline(y=-their_avg_xg_line, color='black', linestyle='dotted')
    ax24.set_title("Our goals scored & conceded from shots and xG (black line) over time (" + str(
        rolling_avg_window) + " game rolling average)")
    ax24.set_ylim(-all_rolling_avg_max, all_rolling_avg_max)
    ax24.set_xlim(0, len_to_use - 1)

    ax25 = fig.add_subplot(spec[2, 0])
    ax25.bar(range(0, len_to_use), our_gd_ylim, color=our_xdiff_ra_bg_colors, alpha=0.1, width=1)
    ax25.bar(range(0, len_to_use), -our_gd_ylim, color=our_xdiff_ra_bg_colors, alpha=0.1, width=1)
    ax25.bar(range(0, len_to_use), our_gd_over_time_rolling_avg, color=our_gdiff_bar_colors, alpha=0.5, width=1)
    ax25.plot(range(0, len_to_use), our_xgd_from_shots_over_time_rolling_avg, color="black", alpha=1)
    ax25.set_title("Our GD from goals that came from shots and xGD (black line) over time (" + str(
        rolling_avg_window) + " game rolling average)")
    plt.axhline(y=our_avg_gdfs_line, color=our_color, linestyle='dotted')
    plt.axhline(y=our_avg_xgd_line, color='black', linestyle='dotted')
    ax25.set_ylim(-our_gd_ylim, our_gd_ylim)
    ax25.set_xlim(0, len_to_use - 1)

    ax26 = fig.add_subplot(spec[2, 0])
    ax26.bar(range(0, len_to_use), 100, color=our_winrate_bar_colors, alpha=0.1, width=1)
    ax26.bar(range(0, len_to_use), our_winrate_over_time_rolling_avg, color=our_color, alpha=0.5, width=1)
    ax26.plot(range(0, len_to_use), our_xwinrate_over_time_rolling_avg, color="black", alpha=1)
    plt.axhline(y=our_avg_winrate_line, color=our_color, linestyle='dotted')
    plt.axhline(y=our_avg_xwinrate_line, color='black', linestyle='dotted')
    ax26.set_title("Our win rate and expected win rate (black line) over time (" + str(
        rolling_avg_window) + " game rolling average)")
    ax26.set_ylim(0, 100)
    ax26.set_xlim(0, len_to_use - 1)

    # positioning and scaling of charts

    ax1.set_position([0, 0.88, 1, 0.1])  # Results chart at top

    ax2.set_position([0.5, 0.725, 0.2, 0.1])  # my xG
    ax23.set_position([0.5, 0.56875, 0.2, 0.1])  # your xG
    ax26.set_position([0.5, 0.4125, 0.2, 0.1])  # win rate
    ax24.set_position([0.5, 0.25625, 0.2, 0.1])  # our xG
    ax25.set_position([0.5, 0.1, 0.2, 0.1])  # xGD

    ax19.set_position([0.39, 0.5, 0.09, 0.325])  # Goal Difference Distribution chart
    ax20.set_position([0.39, 0.275, 0.09, 0.15])  # Goals Scored Distribution chart
    ax21.set_position([0.39, 0.1, 0.09, 0.15])  # Goals Conceded Distribution chart

    ax3.set_position([0.85, 0.75, 0.075, 0.075])  # Results pie chart
    ax17.set_position([0.89, 0.75, 0.075, 0.075])  # OT Results pie chart
    ax18.set_position([0.93, 0.75, 0.075, 0.075])  # NT Results pie chart
    ax22.set_position([0.75, 0.5, 0.1, 0.32])  # Positional tendencies chart (Allan vs Sertalp)
    ax4.set_position([0.87, 0.5, 0.05, 0.2])  # Allan's touch heatmap
    ax5.set_position([0.93, 0.5, 0.05, 0.2])  # Sertalp's touch heatmap

    ax13.set_position([0.03, 0.5, 0.08, 0.32])  # Allan's shot & goal heatmap
    ax6.set_position([0.15, 0.5, 0.1, 0.32])  # Horizontal Bar Chart (Allan vs Sertalp)
    ax14.set_position([0.28, 0.5, 0.08, 0.32])  # Sertalp's shot & goal heatmap

    ax15.set_position([0.03, 0.1, 0.08, 0.32])  # Our shot & goal heatmap
    ax7.set_position([0.15, 0.1, 0.1, 0.32])  # Horizontal Bar Chart (Us vs Opponent)
    ax16.set_position([0.28, 0.1, 0.08, 0.32])  # Opponent's shot & goal heatmap

    ax8.set_position([0.75, 0.05, 0.227, 0.1])  # Goals over time
    ax9.set_position([0.75, 0.155, 0.227, 0.1])  # Shots over time
    ax10.set_position([0.75, 0.26, 0.227, 0.1])  # Saves over time
    ax11.set_position([0.75, 0.365, 0.227, 0.1])  # Assists over time

    if save_and_crop:
        plt.savefig(path_to_charts + "full_canvas.png")
        # Divide the canvas into individual charts by cropping
        img = Image.open(path_to_charts + "full_canvas.png")

        # Chart 1 - results chart
        left = 0
        top = 0
        right = 4000
        bottom = 280
        img_res = img.crop((left, top, right, bottom))
        img_res.save(path_to_charts + "results_with_xgd_chart.png")

        # Chart 2 - first player's shot and goal heatmap
        left = 100
        top = 400
        right = 465
        bottom = 920
        img_res_2 = img.crop((left, top, right, bottom))
        img_res_2.save(path_to_charts + "p1_shot_and_goal_heatmap.png")

        # Chart 3 - first player's shot and goal heatmap
        left = 100
        top = 1200
        right = 465
        bottom = 1720
        img_res_3 = img.crop((left, top, right, bottom))
        img_res_3.save(path_to_charts + "t1_shot_and_goal_heatmap.png")

        # Chart 4 - individual stats per game comparison
        left = 460
        top = 325
        right = 1050
        bottom = 1020
        img_res_4 = img.crop((left, top, right, bottom))
        img_res_4.save(path_to_charts + "t1_individual_stat_comparison.png")

        # Chart 5 - team stats per game comparison
        left = 460
        top = 1125
        right = 1050
        bottom = 1820
        img_res_5 = img.crop((left, top, right, bottom))
        img_res_5.save(path_to_charts + "team_stat_comparison.png")

        # Chart 6 - second player's shot and goal heatmap
        left = 1100
        top = 400
        right = 1465
        bottom = 920
        img_res_7 = img.crop((left, top, right, bottom))
        img_res_7.save(path_to_charts + "p2_shot_and_goal_heatmap.png")

        # Chart 7 - opponent's shot and goal heatmap
        left = 1100
        top = 1200
        right = 1465
        bottom = 1720
        img_res_7 = img.crop((left, top, right, bottom))
        img_res_7.save(path_to_charts + "t2_shot_and_goal_heatmap.png")

        # Chart 8 - goal difference distribution
        left = 1480
        top = 310
        right = 1965
        bottom = 1060
        img_res_8 = img.crop((left, top, right, bottom))
        img_res_8.save(path_to_charts + "gd_distribution_chart.png")

        # Chart 9 - goals scored & conceded distribution
        left = 1480
        top = 1115
        right = 1955
        bottom = 1820
        img_res_9 = img.crop((left, top, right, bottom))
        img_res_9.save(path_to_charts + "gs_and_gc_distribution_chart.png")

        # Chart 10 - first player's xg chart
        left = 1950
        top = 310
        right = 2840
        bottom = 605
        img_res_10 = img.crop((left, top, right, bottom))
        img_res_10.save(path_to_charts + "p1_xg_chart.png")

        # Chart 11 - second player's xg chart
        left = 1950
        top = 610
        right = 2840
        bottom = 905
        img_res_11 = img.crop((left, top, right, bottom))
        img_res_11.save(path_to_charts + "p2_xg_chart.png")

        # Chart 12 - team xg chart
        left = 1950
        top = 1245
        right = 2840
        bottom = 1525
        img_res_12 = img.crop((left, top, right, bottom))
        img_res_12.save(path_to_charts + "team_xg_chart.png")

        # Chart 13 - team xgd chart
        left = 1950
        top = 1565
        right = 2840
        bottom = 1840
        img_res_13 = img.crop((left, top, right, bottom))
        img_res_13.save(path_to_charts + "team_xgd_chart.png")

        # Chart 14 - positional tendency comparison
        left = 2840
        top = 300
        right = 3430
        bottom = 1020
        img_res_14 = img.crop((left, top, right, bottom))
        img_res_14.save(path_to_charts + "t1_pos_tendencies_comparison.png")

        # Chart 15 - assists, saves, shots, goals charts
        left = 2880
        top = 1040
        right = 3930
        bottom = 1945
        img_res_15 = img.crop((left, top, right, bottom))
        img_res_15.save(path_to_charts + "stats_per_game_charts.png")

        # Chart 16 - results pie charts
        left = 3450
        top = 305
        right = 3965
        bottom = 510
        img_res_16 = img.crop((left, top, right, bottom))
        img_res_16.save(path_to_charts + "results_pie_charts.png")

        # Chart 17 - first player's touch heatmap
        left = 3460
        top = 610
        right = 3700
        bottom = 965
        img_res_17 = img.crop((left, top, right, bottom))
        img_res_17.save(path_to_charts + "p1_touch_heatmap.png")

        # Chart 18 - second player's touch heatmap
        left = 3700
        top = 610
        right = 3940
        bottom = 965
        img_res_18 = img.crop((left, top, right, bottom))
        img_res_18.save(path_to_charts + "p2_touch_heatmap.png")

        # Chart 19 - team winrate chart
        left = 1950
        top = 940
        right = 2840
        bottom = 1215
        img_res_19 = img.crop((left, top, right, bottom))
        img_res_19.save(path_to_charts + "team_winrate_chart.png")

executionTime = (time.time() - startTime)
print('\n\nExecution time in seconds: ', "%.2f" % executionTime)
