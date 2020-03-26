#!/usr/local/bin/python3

from sys import stdin, argv
from re import findall
from json import loads
from time import time

class PrettyPrintClingoOutput:
    """
    Class containing methods to pretty print clingo output. Requires clingo output in JSON format and predicates occurs/2 and holds/2. Usage: clingo my_program.lp --outf=2 | python3 pretty-print.py
    
    Attributes
    ----------
    clingo_output : str
        A raw JSON string from the command line
    num_results : str
        The number of models found by clingo
    time : str
        The time needed by clingo to solve
    actions : list
        All occuring actions per model
    fluents : list
        All fluents per model that hold
    output_file : str
        Destination of pretty printed output
    template : dict
        Format strings for output

    Methods
    -------
    print_to_file(timestamp=False, only_time=False)
        Prints clingo output to designated file
    print(only_time=False)
        Prints clingo output to command line
    
    """

    clingo_output = ""
    num_results = ""
    time = ""
    clingo_input = ""
    actions = []
    fluents = []
    output_file = "./results.txt"
    template = {
        "divider": "+------+------------------------------+----------------------------+",
        "title": "RESULTS FOR ",
        "models": "Models: {}\n\n",
        "time total": "Time (Total):    {:10.3f}s\n",
        "time solving": "Time (Solving):  {:10.3f}s ({:.2f}% of total time)\n",
        "time grounding": "Time (Grounding):{:10.3f}s ({:.2f}% of total time)\n\n",
        "header model": "|{:^66}|\n",
        "header time": "| TIME |",
        "header occurs": " OCCURS                       |",
        "header holds": " HOLDS                      |\n",
        "empty action time": "                              |",
        "empty action notime": "|      |                              |",
        "cell action notime": "|      | {:<29}|",
        "cell action": " {:<29}|",
        "cell fluent": " {:<27}|\n"
    }

    def __init__(self, output):
        """
        Parameters
        ----------
        output : str
         Raw clingo JSON output from command line
        """

        self.clingo_output = (loads(output))
        self.clingo_input = self.clingo_output["Input"]
        
        if self.clingo_output["Result"] == "UNSATISFIABLE":
            print("Nothing to print! Reason: %s" % self.clingo_output["Result"])
        else:
            self.num_results = self.clingo_output["Models"]["Number"]
            self.time = self.clingo_output["Time"]
            self.time["Grounding"] = self.time["Total"] - self.time["Solve"]
            self.clingo_output = self.clingo_output["Call"][0]["Witnesses"]

            for result in self.clingo_output:
                a = {}
                f = {}

                for atom in result["Value"]:
                    # remove trailing "."
                    atom = atom[:-1]
                    is_action = False

                    if atom.startswith("occurs"):
                        is_action = True
                        # remove "occurs("
                        atom = atom[7:]
                    elif atom.startswith("holds("):
                        # remove "holds("
                        atom = atom[6:]
                    else:
                        continue

                    # find and remove trailing time step, e.g. move(1,10)
                    timestep = int(findall("[0-9]{1,}$", atom)[0])
                    atom = atom.rstrip(str(timestep))[:-1]

                    if is_action:
                        if a.get(timestep) != None:
                            a[timestep].append(atom)
                        else:
                            a[timestep] = [atom]
                    else:
                        if f.get(timestep) != None:
                            f[timestep].append(atom)
                        else:
                            f[timestep] = [atom]

                if len(f) == 0:
                    print("Not enough data provided!")
                    return

                # fluents are one timestep ahead
                max_time = list(sorted(f.keys()))[-1]

                if max_time == 0 and len(a) == 0:
                    a[0] = []
                else:
                    # add another element to actions to have as much as fluents
                    for i in range((list(sorted(a.keys()))[-1])+1, max_time+1):
                        a[i] = []
                    
                    for timestep in f:
                        f[timestep] = sorted(f[timestep])
                        a[timestep] = sorted(a[timestep])

                self.fluents.append(f)
                self.actions.append(a)

    def print_to_file(self, timestamp=False, only_time=False):
        """
        Create output file and write output into it

        Parameters
        ----------
        timestamp : bool, optional
            Add timestamp to name of output file (default is False)
        only_time : bool, optional
            Print only time needed by clingo to solve (default is False)
        """

        if len(self.fluents) == 0 or len(self.actions) == 0:
            return

        print("Writing results to file ...")

        if timestamp:
            filename = self.output_file.replace(".txt", "-" + str(time()) + ".txt")
        else:
            filename = self.output_file

        file = open(filename, "w+")

        file.write(self.template["title"] + " ".join(self.clingo_input) + "\n")
        file.write(self.template["models"].format(self.num_results))
        file.write(self.template["time total"].format(self.time["Total"]))
        file.write(self.template["time solving"].format(self.time["Solve"], (self.time["Solve"]*100/self.time["Total"])))
        file.write(self.template["time grounding"].format(self.time["Grounding"], (self.time["Grounding"]*100/self.time["Total"])))

        if not only_time:
            for i in range(0,len(self.fluents)):
                f = self.fluents[i]
                a = self.actions[i]

                file.write("+" + self.template["divider"].replace("-", "=").replace("+", "=")[1:-1] + "+\n")
                file.write(self.template["header model"].format((" MODEL: " + str(i+1) + " ")))
                file.write(self.template["divider"] + "\n")
                file.write(self.template["header time"])
                file.write(self.template["header occurs"])
                file.write(self.template["header holds"])

                for timestep in sorted(f.keys()):
                    file.write(self.template["divider"])
                    
                    # compensate length of actions and fluents if there are 
                    # less actions than fluents per timestep (and vice versa)
                    while len(a[timestep]) < len(f[timestep]):
                        a[timestep].append("")

                    while len(f[timestep]) < len(a[timestep]):
                        f[timestep].append("")

                    file.write("\n|")
                    file.write((str(timestep).rjust(5) + " |"))

                    for i in range(0,len(f[timestep])):
                        if a[timestep][i] == "":
                            if i == 0:
                                file.write(self.template["empty action time"])
                            else:
                                file.write(self.template["empty action notime"])
                        else:
                            if i == 0:
                                file.write(self.template["cell action"].format(a[timestep][i]))
                            else:
                                file.write(self.template["cell action notime"].format(a[timestep][i]))
                        
                        file.write(self.template["cell fluent"].format(f[timestep][i]))
                
                file.write(self.template["divider"].replace("-", "=") + "\n\n")

        file.close()
        print("... Done.")

    def print_to_shell(self, only_time=False):
        """
        Write output to command line

        Parameters
        ----------
        only_time : bool, optional
            Print only time needed by clingo to solve (default is False)
        """

        if len(self.fluents) == 0 or len(self.actions) == 0:
            return

        print(self.template["title"] + " ".join(self.clingo_input))
        print(self.template["models"].format(self.num_results), end="")
        print(self.template["time total"].format(self.time["Total"]), end="")
        print(self.template["time solving"].format(self.time["Solve"], (self.time["Solve"]*100/self.time["Total"])), end="")
        print(self.template["time grounding"].format(self.time["Grounding"], (self.time["Grounding"]*100/self.time["Total"])), end="")

        if not only_time:
            for i in range(0,len(self.fluents)):
                f = self.fluents[i]
                a = self.actions[i]

                print("+" + self.template["divider"].replace("-", "=").replace("+", "=")[1:-1] + "+")
                print(self.template["header model"].format((" MODEL: " + str(i+1) + " ")), end="")
                print(self.template["divider"])
                print(self.template["header time"], end="")
                print(self.template["header occurs"], end="")
                print(self.template["header holds"], end="")

                for timestep in sorted(f.keys()):
                    print(self.template["divider"], end="")
                    
                    # compensate length of actions and fluents if there are 
                    # less actions than fluents per timestep (and vice versa)
                    while len(a[timestep]) < len(f[timestep]):
                        a[timestep].append("")

                    while len(f[timestep]) < len(a[timestep]):
                        f[timestep].append("")

                    print("\n|", end="")
                    print(str(timestep).rjust(5), end=" |")

                    for i in range(0,len(f[timestep])):
                        if a[timestep][i] == "":
                            if i == 0:
                                print(self.template["empty action time"], end="")
                            else:
                                print(self.template["empty action notime"], end="")
                        else:
                            if i == 0:
                                print(self.template["cell action"].format(a[timestep][i]), end="")
                            else:
                                print(self.template["cell action notime"].format(a[timestep][i]), end="")
                        
                        print(self.template["cell fluent"].format(f[timestep][i]), end="")
                
                print(self.template["divider"].replace("-", "="), end="\n\n")

def main():
    pretty_printer = PrettyPrintClingoOutput(stdin.read())
    pretty_printer.print_to_file(timestamp=False, only_time=False)

if __name__ == "__main__":
    main()