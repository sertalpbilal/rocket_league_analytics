import os
import csv
import time
import pandas as pd

startTime = time.time()

# Names in Rocket League
my_name = "games5425898691"
your_name = "enpitsu"

# Directory paths (input and output)
path_to_untrimmed_csv = '../data/dataframe/'
path_to_csv = '../data/dataframe_trimmed/'

# Trim CSVs if they haven't been trimmed before
if len(os.listdir(path_to_untrimmed_csv)) > 0:
    csv_files = [pos_csv for pos_csv in os.listdir(path_to_untrimmed_csv) if pos_csv.endswith('.csv')]
    new_csv_files = []
    print("Found", len(csv_files), "CSV(s)")

    # Only keep files that haven't been trimmed
    for file in csv_files:
        if not os.path.exists(path_to_csv + file):
            new_csv_files.append(file)

    csv_files = new_csv_files

    print("Trimming", len(csv_files), "CSV(s)")
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

        dfObj.to_csv(index=False, path_or_buf=path_to_csv + file)

    trimexecutionTime = (time.time() - startTime)
    print('Trimming completed in ', "%.2f" % trimexecutionTime, 'seconds\n\n')

else:
    print("No CSVs found in /dataframe/")