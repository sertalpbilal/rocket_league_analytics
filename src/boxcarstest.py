import csv
from pprint import pprint

import numpy
import numpy as np

import json
import os
import matplotlib.pyplot as plt
from statistics import mean
from mpl_toolkits.mplot3d import Axes3D

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
    new_csv_files.append(file.replace(".json",".csv"))

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

our_team_color = []

for file in new_json_files:
    file_counter += 1
    if file_counter < len(new_json_files) + 1:

        f = open(path_to_json + file, )
        data = json.load(f)

        local_color = "blue"
        local_GS = 0
        local_GC = 0

        for i in data['players']:
            if i["name"] == my_name:
                if i["isOrange"]:
                    local_color = "orange"
                my_id = i["id"]["id"]
            elif i["name"] == your_name:
                your_id = i["id"]["id"]

        if local_color == "orange":
            our_team_color.append("O")
            local_GS = data["teams"][1]["score"]
            local_GC = data["teams"][0]["score"]
        elif local_color == "blue":
            our_team_color.append("B")
            local_GS = data["teams"][0]["score"]
            local_GC = data["teams"][1]["score"]

        for i in data['gameStats']['hits']:
            if "shot" in i:
                if i["playerId"]["id"] == my_id or i["playerId"]["id"] == your_id:
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
                        else:
                            if local_color == "orange":
                                your_goals_x.append(i["ballData"]["posX"] * -1)
                                your_goals_y.append(i["ballData"]["posY"] * -1)
                            else:
                                your_goals_x.append(i["ballData"]["posX"])
                                your_goals_y.append(i["ballData"]["posY"])
                            your_goals_z.append(i["ballData"]["posZ"])

                    else:
                        if i["playerId"]["id"] == my_id:
                            if local_color == "orange":
                                my_misses_x.append(i["ballData"]["posX"] * -1)
                                my_misses_y.append(i["ballData"]["posY"] * -1)
                            else:
                                my_misses_x.append(i["ballData"]["posX"])
                                my_misses_y.append(i["ballData"]["posY"])
                            my_misses_z.append(i["ballData"]["posZ"])
                        else:
                            if local_color == "orange":
                                your_misses_x.append(i["ballData"]["posX"] * -1)
                                your_misses_y.append(i["ballData"]["posY"] * -1)
                            else:
                                your_misses_x.append(i["ballData"]["posX"])
                                your_misses_y.append(i["ballData"]["posY"])
                            your_misses_z.append(i["ballData"]["posZ"])

                else:
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

        # print(file, local_GS, local_GC)
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

fig = plt.figure(figsize=(20, 20))

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
print("\nOur goals:", my_goal_count + your_goal_count, "\tOur misses:", my_miss_count + your_miss_count,
      "\tOur G/Shot ratio:", "%.2f" % ((your_goal_count + my_goal_count) / (
            my_miss_count + your_miss_count + my_goal_count + your_goal_count)))
print("Their goals:", their_goal_count, "\tTheir misses:", their_miss_count, "\tTheir G/Shot ratio:",
      "%.2f" % their_gs_ratio)

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

file_counter = 0

for file in new_csv_files:
    file_counter += 1
    if file_counter < len(new_csv_files) + 1:
        print(file_counter)

        with open(path_to_csv+file) as f:
            reader = csv.reader(f)
            my_list = list(reader)
        f = open(path_to_csv+file, 'r')
        reader = csv.reader(f)
        nrows = len(my_list)
        ncols = len(next(reader))
        multiplier = 1
        if our_team_color[file_counter-1] == "O":
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


n_plots = 8
widths = [1]
heights = [1] * n_plots
spec = fig.add_gridspec(ncols=1, nrows=n_plots, width_ratios=widths, height_ratios=heights)

ax1 = fig.add_subplot(spec[0, 0])  # results
ax1.bar(range(len(gd_array)), gd_array, color=result_color)
ax1.set_ylim(-7, 7)
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

#ax2.view_init(0, 180)

my_goal_count_per_game = my_goal_count / len(new_json_files)
your_goal_count_per_game = your_goal_count / len(new_json_files)
our_goal_count_per_game = (my_goal_count+your_goal_count) / len(new_json_files)
opp_goal_count_per_game = their_goal_count / len(new_json_files)

ax3 = fig.add_subplot(spec[2, 0])  # Goals Scored / Game
ax3_label1 = "Allan (" + str("%.2f" % my_goal_count_per_game) + ")\nSertalp (" + str("%.2f" % your_goal_count_per_game) + ")\nTOTAL (" + str("%.2f" % our_goal_count_per_game) + ")"
ax3_label2 = "Opp. (" + str("%.2f" % opp_goal_count_per_game) + ")"
ax3.bar([ax3_label1,ax3_label2], [our_goal_count_per_game, opp_goal_count_per_game], color=["green", "red"])
ax3.set_title("Goals Scored / Game")

ax4 = fig.add_subplot(spec[3, 0])  # Shots / Game
my_shot_count_per_game = (my_goal_count + my_miss_count) / len(new_json_files)
your_shot_count_per_game = (your_goal_count + your_miss_count) / len(new_json_files)
our_shot_count_per_game = (my_goal_count + my_miss_count + your_goal_count + your_miss_count) / len(new_json_files)
opp_shot_count_per_game = (their_goal_count + their_miss_count) / len(new_json_files)
ax4_label1 = "Allan (" + str("%.2f" % my_shot_count_per_game) + ")\nSertalp (" + str("%.2f" % your_shot_count_per_game) + ")\nTOTAL (" + str("%.2f" % our_shot_count_per_game) + ")"
ax4_label2 = "Opp. (" + str("%.2f" % opp_shot_count_per_game) + ")"
ax4.bar([ax4_label1, ax4_label2], [our_shot_count_per_game, opp_shot_count_per_game], color=["green", "red"])
ax4.set_title("Shots / Game")

ax5 = fig.add_subplot(spec[4, 0])  # Goal/Shot Ratio
my_goalshot_ratio = my_goal_count/(my_goal_count+my_miss_count)
your_goalshot_ratio = your_goal_count/(your_goal_count+your_miss_count)
our_goalshot_ratio = (my_goal_count+your_goal_count)/(my_goal_count+my_miss_count+your_goal_count+your_miss_count)
ax5_label1 = "Allan (" + str("%.2f" % my_goalshot_ratio) + ")\nSertalp (" + str("%.2f" % your_goalshot_ratio) + ")\nTOTAL (" + str("%.2f" % our_goalshot_ratio) + ")"
ax5_label2 = "Opp. (" + str("%.2f" % their_gs_ratio) + ")"
ax5.bar([ax5_label1, ax5_label2], [our_goalshot_ratio, their_gs_ratio], color=["green", "red"])
ax5.set_title("Goal/Shot Ratio")

ax6 = fig.add_subplot(spec[5, 0])  # Results
our_win_ratio = win_count / len(new_json_files)
our_loss_ratio = 1 - our_win_ratio
sizes = [our_win_ratio,our_loss_ratio]
labels = "Win %","Loss %"
ax6.pie(sizes, colors=["green","red"],startangle=90,autopct='%1.1f%%',explode=(0.1,0), shadow=True, textprops={'color':"black", 'bbox':dict(boxstyle="square,pad=0.4", fc="white", alpha=0.9)
})
ax6.set_title("Results")




ax7 = fig.add_subplot(spec[6, 0])  # My heatmap
ax7.set_title(my_name+" Heatmap")
ax7.scatter(my_x_coords,my_y_coords,alpha=0.015,color="green",s=1)

ax8 = fig.add_subplot(spec[7, 0])  # Your heatmap
ax8.set_title(your_name+" Heatmap")
ax8.scatter(your_x_coords,your_y_coords,alpha=0.015,color="blue",s=1)

ax1.set_position([0, 0.88, 1, 0.1])
ax2.set_position([0, 0, 1, 0.85])
ax3.set_position([0.1, 0.1, 0.1, 0.1])
ax4.set_position([0.1, 0.3, 0.1, 0.1])
ax5.set_position([0.1, 0.5, 0.1, 0.1])
ax6.set_position([0.1, 0.6, 0.1, 0.3])

ax7.set_position([0.85, 0.5, 0.1, 0.3])
ax8.set_position([0.85, 0.1, 0.1, 0.3])

# ax2.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([1, 1.12, 0.75, 1]))

plt.show()
