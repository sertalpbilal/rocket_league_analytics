# TODO: set alpha on heatmaps based on how many games we are plotting
# TODO: split ground and aerial heatmap based on z values
# TODO: find a way to speed up proccessing .csv files for heatmap data
# TODO: calculate how long the ball is in our half vs. the opponent's half
import csv
from math import pi
from pprint import pprint
import pandas as pd
import numpy as np

import json
import os
import matplotlib.pyplot as plt
from statistics import mean
from mpl_toolkits.mplot3d import Axes3D

quick_mode = True # Only processes one heatmap file to speed up program

path_to_json = 'data/json/'
path_to_csv = 'data/dataframe/'
json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]
csv_files = [pos_csv for pos_csv in os.listdir(path_to_csv) if pos_csv.endswith('.csv')]

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

for file in new_json_files:
    f = open(path_to_json + file, )
    new_csv_files.append(file.replace(".json", ".csv"))

my_name = "games5425898691"
your_name = "enpitsu"

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
our_shots_goal_or_miss = []  # my goal = 1, my miss = 0, your goal = 2, your miss = 1

my_id = ""
your_id = ""

print(len(new_json_files), "games")

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

my_misses_x = []
my_misses_y = []
my_misses_z = []

your_misses_x = []
your_misses_y = []
your_misses_z = []

their_misses_x = []
their_misses_y = []
their_misses_z = []

win_count = 0
loss_count = 0
result_array = []
result_array_num = []
gd_array = []
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

        for i in data['players']:
            if i["name"] == my_name:
                if i["isOrange"]:
                    local_color = "orange"
                my_id = i["id"]["id"]
            elif i["name"] == your_name:
                your_id = i["id"]["id"]

        if local_color == "orange":
            our_team_color.append("O")
            if data["teams"][0]["isOrange"]:
                local_GS = data["teams"][0]["score"]
                local_GC = data["teams"][1]["score"]
            if data["teams"][1]["isOrange"]:
                local_GS = data["teams"][1]["score"]
                local_GC = data["teams"][0]["score"]
        elif local_color == "blue":
            our_team_color.append("B")
            if data["teams"][0]["isOrange"]:
                local_GS = data["teams"][1]["score"]
                local_GC = data["teams"][0]["score"]
            if data["teams"][1]["isOrange"]:
                local_GS = data["teams"][0]["score"]
                local_GC = data["teams"][1]["score"]

        for i in data['gameStats']['hits']:

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

            if "assist" in i:
                if i["playerId"]["id"] == my_id:
                    my_assists_count += 1
                    local_my_assists += 1
                elif i["playerId"]["id"] == your_id:
                    your_assists_count += 1
                    local_your_assists += 1
                else:
                    their_assists_count += 1
                    local_their_assists += 1

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
                    local_my_goals += 1

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
                    local_your_goals += 1
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

        print(file, local_GS, local_GC, local_our_shots, local_their_shots)
        if local_GS > local_GC:
            win_count += 1
            result_array.append("W")
            result_array_num.append(1)
            result_color.append("green")
        else:
            loss_count += 1
            result_array.append("L")
            result_array_num.append(-1)
            result_color.append("red")
        gd_array.append(local_GS - local_GC)
        gs_array.append(local_GS)
        gc_array.append(local_GC)
        shot_diff_array.append(local_our_shots - local_their_shots)
        my_goals_over_time.append(local_my_goals)
        your_goals_over_time.append(local_your_goals)
        their_goals_over_time.append(local_GC)

        my_shots_over_time.append(local_my_shots)
        your_shots_over_time.append(local_your_shots)
        their_shots_over_time.append(local_their_shots)

        my_saves_over_time.append(local_my_saves)
        your_saves_over_time.append(local_your_saves)
        their_saves_over_time.append(local_their_saves)

        my_assists_over_time.append(local_my_assists)
        your_assists_over_time.append(local_your_assists)
        their_assists_over_time.append(local_their_assists)

# print("Ball average distance to goal when I score: ", "%.2f" % mean(my_goals_distancetogoal))
# print("Ball average distance to goal when you score: ", "%.2f" % mean(your_goals_distancetogoal))
# print("Ball average distance to goal when I miss: ", "%.2f" % mean(my_misses_distancetogoal))
# print("Ball average distance to goal when you miss: ", "%.2f" % mean(your_misses_distancetogoal))
#
# print("\nBall average distance to goal when we score: ",
#       "%.2f" % mean(my_goals_distancetogoal + your_goals_distancetogoal))
# print("Ball average distance to goal when we miss: ",
#       "%.2f" % mean(my_misses_distancetogoal + your_misses_distancetogoal))
# print("Ball average distance to goal when they score: ", "%.2f" % mean(their_goals_distancetogoal))
# print("Ball average distance to goal when they miss: ", "%.2f" % mean(their_misses_distancetogoal))

# max_distance = max(max(my_shots_distancetogoal), max(your_shots_distancetogoal))
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

# plt.bar(range(len(our_shots_distancetogoal)), our_shots_distancetogoal, color = our_col)
# plt.ylim(0,max_distance)
# plt.ylabel("Distance to goal")
# plt.xlabel("Shot number")

fig = plt.figure(figsize=(40, 20))

# ax.set_ylim(-5050,5050)
# ax.set_xlim(-5050,5050)

your_miss_count = 0
your_goal_count = 0
for shot in range(0, len(your_shots_goal_or_miss)):
    if your_shots_goal_or_miss[shot] == 0:
        your_miss_count += 1
    else:
        your_goal_count += 1

my_miss_count = 0
my_goal_count = 0
for shot in range(0, len(my_shots_goal_or_miss)):
    if my_shots_goal_or_miss[shot] == 0:
        my_miss_count += 1
    else:
        my_goal_count += 1

their_miss_count = len(their_misses_distancetogoal)
their_goal_count = len(their_goals_distancetogoal)

their_gs_ratio = their_goal_count / (their_goal_count + their_miss_count)

print("\nAllan goals:", my_goal_count, "\tAllan misses:", my_miss_count)
print("Sertalp goals:", your_goal_count, "\tSertalp misses:", your_miss_count)
print("Allan G/Shot ratio:", "%.2f" % (my_goal_count / (my_miss_count + my_goal_count)))
print("Sertalp G/Shot ratio:", "%.2f" % (your_goal_count / (your_miss_count + your_goal_count)))
print("Allan assists:", my_assists_count)
print("Sertalp assists:", your_assists_count)
print("Allan saves:", my_saves_count)
print("Sertalp saves:", your_saves_count)

print("\nOur goals:", my_goal_count + your_goal_count, "\tOur misses:", my_miss_count + your_miss_count,
      "\tOur G/Shot ratio:", "%.2f" % ((your_goal_count + my_goal_count) / (
            my_miss_count + your_miss_count + my_goal_count + your_goal_count)))
print("Our assists:", my_assists_count + your_assists_count)
print("Our saves:", my_saves_count + your_saves_count)

print("Their goals:", their_goal_count, "\tTheir misses:", their_miss_count, "\tTheir G/Shot ratio:",
      "%.2f" % their_gs_ratio)
print("Their assists:", their_assists_count)
print("Their saves:", their_saves_count)

sep = " "
print("\nResults:", sep.join(result_array))
print(win_count, "Wins, ", loss_count, "Losses")
print("Win Ratio:", "%.2f" % (win_count / (win_count + loss_count) * 100), "%")

my_x_coords = []
my_y_coords = []
my_z_coords = []

your_x_coords = []
your_y_coords = []
your_z_coords = []

ball_x_coords = []
ball_y_coords = []
ball_z_coords = []

#TODO: see what happens if a user is called "ball"

file_counter = 0

for file in new_csv_files:
    file_counter += 1
    if file_counter < len(new_csv_files) + 1:
        print(file_counter)

        with open(path_to_csv + file) as f:
            reader = csv.reader(f)
            my_list = list(reader)

        nrows = len(my_list)
        ncols = len(my_list[0])

        multiplier = 1
        if our_team_color[file_counter - 1] == "O":
            multiplier = -1

        for col in range(ncols):
            if my_list[0][col] == my_name:
                for row in range(nrows):
                    if my_list[1][col] == "pos_x":
                        if row > 1 and my_list[row][col] != "":
                            local_x = float(my_list[row][col])
                            my_x_coords.append(local_x * multiplier)
                    if my_list[1][col] == "pos_y":
                        if row > 1 and my_list[row][col] != "":
                            local_y = float(my_list[row][col])
                            my_y_coords.append(local_y * multiplier)
                    if my_list[1][col] == "pos_z":
                        if row > 1 and my_list[row][col] != "":
                            my_z_coords.append(float(my_list[row][col]))
            if my_list[0][col] == your_name:
                for row in range(nrows):
                    if my_list[1][col] == "pos_x":
                        if row > 1 and my_list[row][col] != "":
                            local_x = float(my_list[row][col])
                            your_x_coords.append(local_x * multiplier)
                    if my_list[1][col] == "pos_y":
                        if row > 1 and my_list[row][col] != "":
                            local_y = float(my_list[row][col])
                            your_y_coords.append(local_y * multiplier)
                    if my_list[1][col] == "pos_z":
                        if row > 1 and my_list[row][col] != "":
                            your_z_coords.append(float(my_list[row][col]))
            if my_list[0][col] == "ball":
                for row in range(nrows):
                    if my_list[1][col] == "pos_x":
                        if row > 1 and my_list[row][col] != "":
                            local_x = float(my_list[row][col])
                            ball_x_coords.append(local_x * multiplier)
                    if my_list[1][col] == "pos_y":
                        if row > 1 and my_list[row][col] != "":
                            local_y = float(my_list[row][col])
                            ball_y_coords.append(local_y * multiplier)
                    if my_list[1][col] == "pos_z":
                        if row > 1 and my_list[row][col] != "":
                            ball_z_coords.append(float(my_list[row][col]))
        if quick_mode:
            break

n_plots = 12
widths = [1]
heights = [1] * n_plots
spec = fig.add_gridspec(ncols=1, nrows=n_plots, width_ratios=widths, height_ratios=heights)

ax1 = fig.add_subplot(spec[0, 0])  # results
ax1.bar(range(len(gd_array)), gd_array, color=result_color)
ax1.plot(range(len(shot_diff_array)), shot_diff_array, color="blue", linestyle='--')
ax1.set_ylim(-10, 10)
ax1.set_xlim(-1, len(gd_array))
ax1.axis("off")
plt.axhline(y=0, color='grey', linestyle=':')

ax2 = fig.add_subplot(spec[1, 0], projection='3d')  # shot positions
ax2.set_xlabel("X Axis")
ax2.set_ylabel("Y Axis")
ax2.set_zlabel("Z Axis")
ax2.set_xlim(-4100, 4100)
ax2.set_ylim(-5140, 5140)
ax2.set_zlim(0, 2050)
ax2.scatter(my_goals_x, my_goals_y, my_goals_z, color="green", alpha=0.5, s=75)
ax2.scatter(your_goals_x, your_goals_y, your_goals_z, color="blue", alpha=0.5, s=75)
ax2.scatter(their_goals_x, their_goals_y, their_goals_z, color="red", alpha=0.5, s=75)

ax2.scatter(my_misses_x, my_misses_y, my_misses_z, color="green", alpha=0.5, s=30, marker="x")
ax2.scatter(your_misses_x, your_misses_y, your_misses_z, color="blue", alpha=0.5, s=30, marker="x")
ax2.scatter(their_misses_x, their_misses_y, their_misses_z, color="red", alpha=0.5, s=30, marker="x")

ax2.scatter(my_x_coords, my_y_coords, my_z_coords, color="green", alpha=0.01, s=1, marker=",")
ax2.scatter(your_x_coords, your_y_coords, your_z_coords, color="blue", alpha=0.01, s=1, marker=",")
ax2.scatter(ball_x_coords, ball_y_coords, ball_z_coords, color="grey", alpha=0.1, s=1, marker="1")


# side view
# ax2.view_init(0, 180)
games_nr = len(new_json_files)

my_goal_count_per_game = my_goal_count / games_nr
your_goal_count_per_game = your_goal_count / games_nr
our_goal_count_per_game = (my_goal_count + your_goal_count) / games_nr
opp_goal_count_per_game = their_goal_count / games_nr

my_shot_count_per_game = (my_goal_count + my_miss_count) / games_nr
your_shot_count_per_game = (your_goal_count + your_miss_count) / games_nr
our_shot_count_per_game = (my_goal_count + my_miss_count + your_goal_count + your_miss_count) / games_nr
opp_shot_count_per_game = (their_goal_count + their_miss_count) / games_nr

my_goalshot_ratio = my_goal_count / (my_goal_count + my_miss_count)
your_goalshot_ratio = your_goal_count / (your_goal_count + your_miss_count)
our_goalshot_ratio = (my_goal_count + your_goal_count) / (
            my_goal_count + my_miss_count + your_goal_count + your_miss_count)

my_assist_count_per_game = my_assists_count / games_nr
your_assist_count_per_game = your_assists_count / games_nr
our_assist_count_per_game = (my_assists_count + your_assists_count) / games_nr
opp_assist_count_per_game = their_assists_count / games_nr

my_save_count_per_game = my_saves_count / games_nr
your_save_count_per_game = your_saves_count / games_nr
our_save_count_per_game = (my_saves_count + your_saves_count) / games_nr
opp_save_count_per_game = their_saves_count / games_nr

my_miss_count_per_game = my_miss_count / games_nr
your_miss_count_per_game = your_miss_count / games_nr
our_miss_count_per_game = (my_miss_count + your_miss_count) / games_nr
opp_miss_count_per_game = their_miss_count / games_nr

ax3 = fig.add_subplot(spec[2, 0])  # Results
our_win_ratio = win_count / len(new_json_files)
our_loss_ratio = 1 - our_win_ratio
sizes = [our_win_ratio, our_loss_ratio]
labels = "Win %", "Loss %"
ax3.pie(sizes, colors=["green", "red"], startangle=90, autopct='%1.1f%%', explode=(0.1, 0), shadow=True,
        textprops={'color': "black", 'bbox': dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
                   })

ax4 = fig.add_subplot(spec[3, 0])  # My heatmap
ax4.set_title("Allan's Heatmap")
ax4.axis("off")
ax4.scatter(my_x_coords, my_y_coords, alpha=0.005, color="green", s=1)

ax5 = fig.add_subplot(spec[4, 0])  # Your heatmap
ax5.set_title("Sertalp's Heatmap")
ax5.axis("off")
ax5.scatter(your_x_coords, your_y_coords, alpha=0.005, color="blue", s=1)

ax6 = fig.add_subplot(spec[5, 0])  # Team balance horizontal stacked bar chart
ticks = [1, 2, 3, 4, 5, 6]
ax6.set_yticks(ticks)

dic = {1.0: "Assists", 2.0: "Saves", 3.0: "Goals", 4.0: "Misses", 5.0: "Shots", 6.0: "Goals/Shot"}
labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]
ax6.set_yticklabels(labels)
ax6.set_xticklabels("")
ax6.tick_params(bottom=False)  # remove the ticks

ax6.set_xlim(0, 1)

# ASSISTS
my_assist_share = my_assists_count / (my_assists_count + your_assists_count)
your_assist_share = 1 - my_assist_share
ax6.barh(1, my_assist_share, color="green")
ax6.barh(1, your_assist_share, left=my_assist_share, color="blue")

# SAVES
my_save_share = my_saves_count / (my_saves_count + your_saves_count)
your_save_share = 1 - my_save_share
ax6.barh(2, my_save_share, color="green")
ax6.barh(2, your_save_share, left=my_save_share, color="blue")

# GOALS
my_goal_share = my_goal_count / (my_goal_count + your_goal_count)
your_goal_share = 1 - my_goal_share
ax6.barh(3, my_goal_share, color="green")
ax6.barh(3, your_goal_share, left=my_goal_share, color="blue")

# MISSES
my_miss_share = my_miss_count / (my_miss_count + your_miss_count)
your_miss_share = 1 - my_miss_share
ax6.barh(4, my_miss_share, color="green")
ax6.barh(4, your_miss_share, left=my_miss_share, color="blue")

# SHOTS
my_shot_share = (my_miss_count + my_goal_count) / (my_miss_count + my_goal_count + your_miss_count + your_goal_count)
your_shot_share = 1 - my_shot_share
ax6.barh(5, my_shot_share, color="green")
ax6.barh(5, your_shot_share, left=my_shot_share, color="blue")

# GOAL/SHOT RATIO
my_gs_ratio_share = my_goalshot_ratio / (my_goalshot_ratio + your_goalshot_ratio)
your_gs_ratio_share = 1 - my_gs_ratio_share
ax6.barh(6, my_gs_ratio_share, color="green")
ax6.barh(6, your_gs_ratio_share, left=my_gs_ratio_share, color="blue")

label_count = 0
for c in ax6.containers:
    # customize the label to account for cases when there might not be a bar section
    labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

    # assists
    if label_count == 0:
        labels[0] = "%.2f" % my_assist_count_per_game
    if label_count == 1:
        labels[0] = "%.2f" % your_assist_count_per_game

    # saves
    if label_count == 2:
        labels[0] = "%.2f" % my_save_count_per_game
    if label_count == 3:
        labels[0] = "%.2f" % your_save_count_per_game

    # goals
    if label_count == 4:
        labels[0] = "%.2f" % my_goal_count_per_game
    if label_count == 5:
        labels[0] = "%.2f" % your_goal_count_per_game

    # misses
    if label_count == 6:
        labels[0] = "%.2f" % my_miss_count_per_game
    if label_count == 7:
        labels[0] = "%.2f" % your_miss_count_per_game

    # shots
    if label_count == 8:
        labels[0] = "%.2f" % my_shot_count_per_game
    if label_count == 9:
        labels[0] = "%.2f" % your_shot_count_per_game

    # goal / shot ratio
    if label_count == 10:
        labels[0] = "%.2f" % my_goalshot_ratio
    if label_count == 11:
        labels[0] = "%.2f" % your_goalshot_ratio

    # set the bar label
    ax6.bar_label(c, labels=labels, label_type='center', color="white")
    label_count += 1

ax6.set_title("Allan - Sertalp (per Game)")

ax7 = fig.add_subplot(spec[6, 0])  # Horizontal stacked bar chart (us vs opponent)
ticks = [1, 2, 3, 4, 5, 6]
ax7.set_yticks(ticks)

dic = {1.0: "Assists", 2.0: "Saves", 3.0: "Goals", 4.0: "Misses", 5.0: "Shots", 6.0: "Goals/Shot"}
labels = [ticks[i] if t not in dic.keys() else dic[t] for i, t in enumerate(ticks)]
ax7.set_yticklabels(labels)
ax7.set_xticklabels("")
ax7.tick_params(bottom=False)  # remove the ticks

ax7.set_xlim(0, 1)

our_color = "dimgrey"
opp_color = "darkred"

# ASSISTS
our_assist_share = (my_assists_count + your_assists_count) / (
            my_assists_count + your_assists_count + their_assists_count)
opp_assist_share = 1 - our_assist_share
ax7.barh(1, our_assist_share, color=our_color)
ax7.barh(1, opp_assist_share, left=our_assist_share, color=opp_color)

# SAVES
our_save_share = (my_saves_count + your_saves_count) / (my_saves_count + your_saves_count + their_saves_count)
opp_save_share = 1 - our_save_share
ax7.barh(2, our_save_share, color=our_color)
ax7.barh(2, opp_save_share, left=our_save_share, color=opp_color)

# GOALS
our_goal_share = (my_goal_count + your_goal_count) / (my_goal_count + your_goal_count + their_goal_count)
opp_goal_share = 1 - our_goal_share
ax7.barh(3, our_goal_share, color=our_color)
ax7.barh(3, opp_goal_share, left=our_goal_share, color=opp_color)

# MISSES
our_miss_share = (my_miss_count + your_miss_count) / (my_miss_count + your_miss_count + their_miss_count)
opp_miss_share = 1 - our_miss_share
ax7.barh(4, our_miss_share, color=our_color)
ax7.barh(4, opp_miss_share, left=our_miss_share, color=opp_color)

# SHOTS
our_shot_share = (my_miss_count + my_goal_count + your_miss_count + your_goal_count) / (
            my_miss_count + my_goal_count + your_miss_count + your_goal_count + their_goal_count + their_miss_count)
opp_shot_share = 1 - our_shot_share
ax7.barh(5, our_shot_share, color=our_color)
ax7.barh(5, opp_shot_share, left=our_shot_share, color=opp_color)

# GOAL/SHOT RATIO
our_gs_ratio_share = (my_goalshot_ratio + your_goalshot_ratio) / (
            my_goalshot_ratio + your_goalshot_ratio + their_gs_ratio * 2)
opp_gs_ratio_share = 1 - our_gs_ratio_share
ax7.barh(6, our_gs_ratio_share, color=our_color)
ax7.barh(6, opp_gs_ratio_share, left=our_gs_ratio_share, color=opp_color)

label_count = 0
for c in ax7.containers:
    # customize the label to account for cases when there might not be a bar section
    labels = [f'{w * 100:.0f}%' if (w := v.get_width()) > 0 else '' for v in c]

    # assists
    if label_count == 0:
        labels[0] = "%.2f" % our_assist_count_per_game
    if label_count == 1:
        labels[0] = "%.2f" % opp_assist_count_per_game

    # saves
    if label_count == 2:
        labels[0] = "%.2f" % our_save_count_per_game
    if label_count == 3:
        labels[0] = "%.2f" % opp_save_count_per_game

    # goals
    if label_count == 4:
        labels[0] = "%.2f" % our_goal_count_per_game
    if label_count == 5:
        labels[0] = "%.2f" % opp_goal_count_per_game

    # misses
    if label_count == 6:
        labels[0] = "%.2f" % our_miss_count_per_game
    if label_count == 7:
        labels[0] = "%.2f" % opp_miss_count_per_game

    # shots
    if label_count == 8:
        labels[0] = "%.2f" % our_shot_count_per_game
    if label_count == 9:
        labels[0] = "%.2f" % opp_shot_count_per_game

    # goal / shot ratio
    if label_count == 10:
        labels[0] = "%.2f" % our_goalshot_ratio
    if label_count == 11:
        labels[0] = "%.2f" % their_gs_ratio

    # set the bar label
    ax7.bar_label(c, labels=labels, label_type='center', color="white")
    label_count += 1

ax7.set_title("Us - Opponents (per Game)")

new_result_array_num_up = []
new_result_array_num_down = []
new_result_color = []

for entry in range(0, len(their_goals_over_time)):
    their_goals_over_time[entry] *= -1

ax8 = fig.add_subplot(spec[0, 0])  # our goals over time
ax8.set_xlim(0, games_nr + 1)
limit1 = min(their_goals_over_time)
our_goals_over_time = [your_goals_over_time[x] + my_goals_over_time[x] for x in range(games_nr)]
limit2 = max(our_goals_over_time)
limit = max(abs(limit1), limit2)
ax8.set_ylim(-limit, limit)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit
    if result_array_num[entry] == 1:
        new_result_color.append("green")
    else:
        new_result_color.append("red")

ax8.bar(range(1, games_nr + 1), new_result_array_num_up, color=new_result_color, width=1, alpha=0.25)
ax8.bar(range(1, games_nr + 1), new_result_array_num_down, color=new_result_color, width=1, alpha=0.25)

ax8.bar(range(1, games_nr + 1), my_goals_over_time, color="green", width=1, ec="black")
ax8.bar(range(1, games_nr + 1), your_goals_over_time, color="blue", bottom=my_goals_over_time, width=1, ec="black")
ax8.bar(range(1, games_nr + 1), their_goals_over_time, color="red", width=1, ec="black")
ax8.set_ylabel("GOALS", rotation="horizontal", ha="center", va="center", labelpad=35)

for entry in range(0, len(their_shots_over_time)):
    their_shots_over_time[entry] *= -1

ax9 = fig.add_subplot(spec[0, 0])  # our goals over time
ax9.set_xlim(0, games_nr + 1)
limit1 = min(their_shots_over_time)
our_shots_over_time = [your_shots_over_time[x] + my_shots_over_time[x] for x in range(games_nr)]
limit2 = max(our_shots_over_time)
limit = max(abs(limit1), limit2)
ax9.set_ylim(-limit, limit)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax9.bar(range(1, games_nr + 1), new_result_array_num_up, color=new_result_color, width=1, alpha=0.25)
ax9.bar(range(1, games_nr + 1), new_result_array_num_down, color=new_result_color, width=1, alpha=0.25)

ax9.bar(range(1, games_nr + 1), my_shots_over_time, color="green", width=1, ec="black")
ax9.bar(range(1, games_nr + 1), your_shots_over_time, color="blue", bottom=my_shots_over_time, width=1, ec="black")
ax9.bar(range(1, games_nr + 1), their_shots_over_time, color="red", width=1, ec="black")
ax9.set_xticklabels("")
ax9.set_ylabel("SHOTS", rotation="horizontal", ha="center", va="center", labelpad=35)

for entry in range(0, len(their_saves_over_time)):
    their_saves_over_time[entry] *= -1

ax10 = fig.add_subplot(spec[0, 0])  # our saves over time
ax10.set_xlim(0, games_nr + 1)
limit1 = min(their_saves_over_time)
our_saves_over_time = [your_saves_over_time[x] + my_saves_over_time[x] for x in range(games_nr)]
limit2 = max(our_saves_over_time)
limit = max(abs(limit1), limit2)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax10.bar(range(1, games_nr + 1), new_result_array_num_up, color=new_result_color, width=1, alpha=0.25)
ax10.bar(range(1, games_nr + 1), new_result_array_num_down, color=new_result_color, width=1, alpha=0.25)

ax10.set_ylim(-limit, limit)
ax10.bar(range(1, games_nr + 1), my_saves_over_time, color="green", width=1, ec="black")
ax10.bar(range(1, games_nr + 1), your_saves_over_time, color="blue", bottom=my_saves_over_time, width=1, ec="black")
ax10.bar(range(1, games_nr + 1), their_saves_over_time, color="red", width=1, ec="black")
ax10.set_xticklabels("")
ax10.set_ylabel("SAVES", rotation="horizontal", ha="center", va="center", labelpad=35)

for entry in range(0, len(their_assists_over_time)):
    their_assists_over_time[entry] *= -1

ax11 = fig.add_subplot(spec[0, 0])  # our assists over time
ax11.set_xlim(0, games_nr + 1)
limit1 = min(their_assists_over_time)
our_assists_over_time = [your_assists_over_time[x] + my_assists_over_time[x] for x in range(games_nr)]
limit2 = max(our_assists_over_time)
limit = max(abs(limit1), limit2)
ax11.set_ylim(-limit, limit)

for entry in range(0, len(result_array_num)):
    new_result_array_num_up = limit
    new_result_array_num_down = -limit

ax11.bar(range(1, games_nr + 1), new_result_array_num_up, color=new_result_color, width=1, alpha=0.25)
ax11.bar(range(1, games_nr + 1), new_result_array_num_down, color=new_result_color, width=1, alpha=0.25)

ax11.bar(range(1, games_nr + 1), my_assists_over_time, color="green", width=1, ec="black")
ax11.bar(range(1, games_nr + 1), your_assists_over_time, color="blue", bottom=my_assists_over_time, width=1, ec="black")
ax11.bar(range(1, games_nr + 1), their_assists_over_time, color="red", width=1, ec="black")
ax11.set_xticklabels("")
ax11.set_ylabel("ASSISTS", rotation="horizontal", ha="center", va="center", labelpad=35)

ax12 = fig.add_subplot(spec[4, 0])  # Your heatmap
ax12.set_title("Heatmap of the ball")
ax12.axis("off")
ax12.scatter(ball_x_coords, ball_y_coords, alpha=0.005, color="grey", s=1)


ax1.set_position([0, 0.88, 1, 0.1])
ax2.set_position([0, 0, 1, 0.85])  # 3D Scatterplot
ax3.set_position([0.45, 0.8, 0.1, 0.1])  # Results pie chart

ax4.set_position([0.75, 0.55, 0.06, 0.24])  # Allan's heatmap
ax12.set_position([0.825, 0.55, 0.06, 0.24])  # Heatmap of the ball
ax5.set_position([0.9, 0.55, 0.06, 0.24])  # Sertalp's heatmap

ax6.set_position([0.07, 0.5, 0.2, 0.3])  # Horizontal Bar Chart (Allan vs Sertalp)
ax7.set_position([0.07, 0.1, 0.2, 0.3])  # Horizontal Bar Chart (Us vs Opponent)
ax8.set_position([0.75, 0.05, 0.2, 0.1])  # Goals over time
ax9.set_position([0.75, 0.155, 0.2, 0.1])  # Shots over time
ax10.set_position([0.75, 0.26, 0.2, 0.1])  # Saves over time
ax11.set_position([0.75, 0.365, 0.2, 0.1])  # Assists over time

# ax2.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([1, 1.12, 0.75, 1]))

plt.show()
