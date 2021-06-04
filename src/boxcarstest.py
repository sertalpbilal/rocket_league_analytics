from pprint import pprint
import numpy as np

import json
import os
import matplotlib.pyplot as plt
from statistics import mean
from mpl_toolkits.mplot3d import Axes3D

path_to_json = 'data/json/'
json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]
file_counter = 0

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

print(len(json_files))

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

all_colors = []
all_sizes = []

our_markers = []

for file in json_files:
    file_counter += 1
    if file_counter < len(json_files):

        f = open(path_to_json + file, )
        data = json.load(f)

        print(file)

        local_color = "blue"

        for i in data['players']:
            if i["name"] == my_name:
                if i["isOrange"]:
                    local_color = "orange"
                my_id = i["id"]["id"]
            elif i["name"] == your_name:
                your_id = i["id"]["id"]

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
                        all_colors.append("green")
                        all_sizes.append(150)
                    else:
                        all_colors.append("green")
                        all_sizes.append(5)

                else:
                    if local_color == "orange":
                        all_shots_x.append(i["ballData"]["posX"] * -1)
                        all_shots_y.append(i["ballData"]["posY"] * -1)
                    else:
                        all_shots_x.append(i["ballData"]["posX"])
                        all_shots_y.append(i["ballData"]["posY"])
                    all_shots_z.append(i["ballData"]["posZ"])

                    if "goal" in i:
                        all_colors.append("red")
                        all_sizes.append(150)
                        their_goals_distancetogoal.append(i["distanceToGoal"])

                    else:
                        all_colors.append("red")
                        all_sizes.append(5)
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
                    our_markers.append('s')

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
                    our_markers.append('s')

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
                    our_markers.append('o')

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
                    our_markers.append('o')

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

# print("Ball average distance to goal when I score: ", "%.2f" % mean(my_goals_distancetogoal))
# print("Ball average distance to goal when you score: ", "%.2f" % mean(your_goals_distancetogoal))
# print("Ball average distance to goal when I miss: ", "%.2f" % mean(my_misses_distancetogoal))
# print("Ball average distance to goal when you miss: ", "%.2f" % mean(your_misses_distancetogoal))
#
# print("\nBall average distance to goal when we score: ", "%.2f" % mean(my_goals_distancetogoal+your_goals_distancetogoal))
# print("Ball average distance to goal when we miss: ", "%.2f" % mean(my_misses_distancetogoal+your_misses_distancetogoal))
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
ax = plt.axes(projection="3d")

# ax.set_ylim(-5050,5050)
# ax.set_xlim(-5050,5050)

ax.set_xlabel("X Axis")
ax.set_ylabel("Y Axis")
ax.set_zlabel("Z Axis")

ax.scatter3D(all_shots_x, all_shots_y, all_shots_z, color=all_colors, alpha=0.5, s=all_sizes)
ax.get_proj = lambda: np.dot(Axes3D.get_proj(ax), np.diag([1, 1.25, 0.75, 1]))
# ax.view_init(0, 180)

plt.show()
