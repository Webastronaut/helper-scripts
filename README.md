# helper-scripts

This repository encompasses Python scripts I developed during the writing of my bachelor thesis. All scripts require Python 3.x.

## create-csv.py

This script can be used to extract benchmark results and create CSV files. More information can be found [here](https://github.com/Webastronaut/benchmark-asprilo-golog).

## golog-to-asp.py

A [Golog](https://www.sciencedirect.com/science/article/pii/S0743106696001215/pdf?md5=e389b27881be7c041b0ab34ed71612ba&pid=1-s2.0-S0743106696001215-main.pdf&_valck=1) to [ASP](https://wvvw.aaai.org/ojs/index.php/aimagazine/article/download/2671/2573)/Dot translator (requires [Graphviz](https://www.graphviz.org/)). Example for usage:

```shell
python3 golog-to-asp.py "[move(X,D){robot(X), direction(D)}|wait(R){robot(R)}]*;#~battery_low(R){robot(R)} & [robot_on_target(R,T){robot(R), target(T)} + robot_loading(R){robot(R)}]#?"
```

This creates files `gst.lp` and `gst.dot.png` that represent the entered Golog program.

## pretty-print.py

Creates tabular [clingo](https://github.com/potassco/clingo) output for better readability. An ASP program must output `occurs/2` and `holds/2` predicates through
```
#show occurs/2.
#show holds/2.
```

Example output:
```
RESULTS FOR example.lp
Models: 4

Time (Total):         0.008s
Time (Solving):       0.000s (0.00% of Total Time)
Time (Grounding):     0.008s (100.00% of Total Time)

+==================================================================+
|                            ANSWER: 1                             |
+------+------------------------------+----------------------------+
| TIME | OCCURS                       | HOLDS                      |
+------+------------------------------+----------------------------+
|    0 | a                            | e                          |
|      |                              | f                          |
|      |                              | g                          |
|      |                              | h                          |
+------+------------------------------+----------------------------+
|    1 | b                            | e                          |
|      |                              | h                          |
+------+------------------------------+----------------------------+
|    2 | b                            | g                          |
|      |                              | h                          |
+------+------------------------------+----------------------------+
|    3 | b                            | f                          |
|      |                              | g                          |
+------+------------------------------+----------------------------+
|    4 | b                            | g                          |
|      |                              | h                          |
+------+------------------------------+----------------------------+
|    5 |                              | e                          |
|      |                              | g                          |
|      |                              | h                          |
+======+==============================+============================+
```

To create readable output download the .py file and pipe the clingo output to it:

```
clingo [MY_PROG].lp [NUM_OF_RESULTS] --outf=2 | python3 pretty-print.py
```

Notice the `--outf=2` option which tells clingo to output a JSON string. This option is necessary for the pretty printer to work properly. It then generates a file named `results.txt` as per default. If you prefer command line output change line 275 to:

```python
pretty_printer.print_to_shell()
```