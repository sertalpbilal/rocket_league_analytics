import csv
import os

# Names in Rocket League
my_name = "games5425898691"
your_name = "enpitsu"

path_to_csv = 'data/dataframe/'
path_to_trimmed = 'data/dataframe-trimmed/'

csv_files = [pos_csv for pos_csv in os.listdir(path_to_csv) if pos_csv.endswith('.csv')]

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
            write = csv.writer(f)
            write.writerow(overTime)
            for r in reader:
                write.writerow((r[my_x_colNum], r[my_y_colNum], r[my_z_colNum],
                                r[your_x_colNum], r[your_y_colNum], r[your_z_colNum],
                                r[ball_x_colNum], r[ball_y_colNum], r[ball_z_colNum]))


print("Done trimming")

