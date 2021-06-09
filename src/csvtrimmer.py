# TODO: More accurate rounding (use round, not int)

import csv
import os
import time

startTime = time.time()

# Names in Rocket League
my_name = "games5425898691"
your_name = "enpitsu"

path_to_csv = 'data/dataframe/'
path_to_trimmed = 'data/dataframe-trimmed/'

csv_files = [pos_csv for pos_csv in os.listdir(path_to_csv) if pos_csv.endswith('.csv')]

print(csv_files)
frames_to_skip = 20

for file in csv_files:
    with open(path_to_csv + file) as f:
        reader = csv.reader(f)
        my_list = list(reader)

    nrows = len(my_list)
    ncols = len(my_list[0])
    my_x_colNum = -1
    my_y_colNum = -1
    my_z_colNum = -1
    your_x_colNum = -1
    your_y_colNum = -1
    your_z_colNum = -1
    ball_x_colNum = -1
    ball_y_colNum = -1
    ball_z_colNum = -1
    overTime = "F"

    for col in range(ncols):
        if my_list[0][col] == my_name:
            if my_list[1][col] == "pos_x":
                my_x_colNum = col
            if my_list[1][col] == "pos_y":
                my_y_colNum = col
            if my_list[1][col] == "pos_z":
                my_z_colNum = col
        if my_list[0][col] == your_name:
            if my_list[1][col] == "pos_x":
                your_x_colNum = col
            if my_list[1][col] == "pos_y":
                your_y_colNum = col
            if my_list[1][col] == "pos_z":
                your_z_colNum = col
        if my_list[0][col] == "ball":
            if my_list[1][col] == "pos_x":
                ball_x_colNum = col
            if my_list[1][col] == "pos_y":
                ball_y_colNum = col
            if my_list[1][col] == "pos_z":
                ball_z_colNum = col
        if my_list[0][col] == "game":
            if my_list[1][col] == "is_overtime":
                overTime = "T"

    with open(path_to_csv + file) as f:
        reader = csv.reader(f)

        with open(path_to_trimmed + file, 'w') as f:
            row_num = 0
            write = csv.writer(f)
            write.writerow(overTime)
            for r in reader:
                if row_num < 2:
                    write.writerow((r[my_x_colNum], r[my_y_colNum], r[my_z_colNum],
                                    r[your_x_colNum], r[your_y_colNum], r[your_z_colNum],
                                    r[ball_x_colNum], r[ball_y_colNum], r[ball_z_colNum]))
                else:
                    if row_num % frames_to_skip == 0:
                        if not (r[my_x_colNum] == "" or r[my_y_colNum] == "" or r[my_z_colNum] == "" or r[your_x_colNum] == "" or r[your_y_colNum] == "" or r[your_z_colNum] == "" or r[ball_x_colNum] == "" or r[ball_y_colNum] == "" or r[ball_z_colNum] == ""):
                            write.writerow((int(float(r[my_x_colNum])), int(float(r[my_y_colNum])), int(float(r[my_z_colNum])),
                                            int(float(r[your_x_colNum])), int(float(r[your_y_colNum])), int(float(r[your_z_colNum])),
                                            int(float(r[ball_x_colNum])), int(float(r[ball_y_colNum])), int(float(r[ball_z_colNum]))))

                row_num+=1


print("Done trimming")
executionTime = (time.time() - startTime)
print('\n\nExecution time in seconds: ', "%.2f" % executionTime)
