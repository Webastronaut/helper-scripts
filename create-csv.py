#!/usr/local/bin/python3git 

from sys import argv
from os import listdir
from datetime import date
from statistics import mean, stdev
from json import loads

# Usage:
# python create-csv.py ./[RESULTS_FOLDER]/ [OUTPUT_FOLDER_NAME] [RUNS]

today = date.today()

runsolver_path = "/run$/runsolver.solver"
csv_file_path = "./" + today.strftime("%Y%m%d")
instances_path = argv[1]
runs = int(argv[3])
csv_file_path += "-" + argv[2] + ".csv"

delimiter = ","

header = [
    "Instance",
    "Horizon",
    "Time Mean",
    "Time StDev",
    "Solving Mean",
    "Solving StDev",
    "Grounding Mean",
    "Grounding StDev"
]

# create csv header
stats_header=""
for head in header:
    stats_header += head

    if head != header[-1]:
        stats_header += delimiter
    else:
        stats_header += "\n"

stats = []

# go through all subdirs of results folder to read out stats from clingo
dir_list = listdir(instances_path)

for dir in dir_list:
    if dir[0] == ".":
        continue

    # extract instance number
    stats_csv_line = str(int(dir[(len(dir)-6):(len(dir)-3)])) + delimiter
    # extract horizon
    stats_csv_line += dir[0:2] + delimiter

    total_list = []
    solving_list = []
    grounding_list = []

    for i in range(1,runs + 1):
        stats_file_path = instances_path + dir + runsolver_path.replace("$", str(i))
        stats_file = open(stats_file_path, "r")
        interrupt = False

        if stats_file.mode == "r":
            file_content = stats_file.read()
            # fix broken JSON
            if "*** Info : (clingo): INTERRUPTED by signal!" in file_content:
                interrupt = True
                file_content = file_content.replace("*** Info : (clingo): INTERRUPTED by signal!\n", "")

            stats_file_contents = (loads(file_content))

            total_list.append(stats_file_contents["Time"]["Total"])
            solving_list.append(stats_file_contents["Time"]["Solve"])
            grounding_list.append((stats_file_contents["Time"]["Total"] - stats_file_contents["Time"]["Solve"]))

            if i == runs:
                total_mean = mean(total_list)
                solving_mean = mean(solving_list)
                grounding_mean = mean(grounding_list)

                total_stdev = stdev(total_list)
                solving_stdev = stdev(solving_list)
                grounding_stdev = stdev(grounding_list)

                # create csv line for current instance
                stats_csv_line += str(total_mean) + "," + str(total_stdev) + "," +\
                    str(solving_mean) + "," + str(solving_stdev) + "," +\
                    str(grounding_mean) + "," + str(grounding_stdev)

                if dir != dir_list[-1]:
                    stats_csv_line += "\n"

                stats.append(stats_csv_line)
        stats_file.close()

# write created csv lines to csv file
csv_file = open(csv_file_path, "w+")
csv_file.write(stats_header)

for stat in stats:
    csv_file.write(stat)

csv_file.close()

print("Created file: %s" % csv_file_path)