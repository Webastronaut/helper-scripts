#!/usr/local/bin/Python3

from re import findall, finditer, sub
from sys import argv
from subprocess import call

# based on Dijkstras Shunting Yard Algorithm described in ``ALGOL-60 translation''
# AND
# https://www.esimovmiras.cc/articles/03-build-math-ast-parser/ (accessed: 2019-12-13)
# AND
# https://brilliant.org/wiki/shunting-yard-algorithm/ (accessed: 2019-12-13)
class GOLOGToASP:
    """
    GOLOG to ASP/Dot class. Can be used to translate Golog programs to Dot and ASP. Fluent formulas need to be enclosed in hash symbols. Usage of parentheses:
	() : only for predicates, e.g. move(X,Y)
	{} : used to make variables safe, e.g. move(X,Y){robot(X), direction(Y)}
	[] : Used for grouping of subexpressions, e.g. "#f & ~e + [f & g]#?" or "[a;b]*;c"
    
    Attributes
    ----------
    precedence : dict
        Contains lists for the determination of operator precedence
    names : dict
        Contains lists of operator names
    re : str
        The Golog program from the command line
    ast : list
        Holds the generated abstract syntax tree of the given Golog program
    gst_template : dict
        Template strings for the generation of ASP programs representing the Golog program
    fst_template : dict
        Template strings for the generation of ASP programs representing formulas
    dot_template : dict
        Template string for the generation of DOT files representing the Golog program
    formulas : dict
        All logical formulas found in the given Golog program
    asp_file : str
        The name of the .lp file
    dot_file : str
        The name of the .dot file

    Methods
    -------
    get_name(op, type="gst")
        Returns name of given operator
    get_workable_prog(type="gst", exp=None)
        Prepares the entered Golog program for the generation of the abstract syntax tree
    get_ast_node(op_stack, output_stack, type="gst")
        Returns an abstract syntax tree node
    get_ast(type="gst", exp=None)
        Generates and returns the abstract syntax tree representing the entered Golog program
    extract_clause(string)
        Filters and returns the head and body of an ASP clause inside the entered Golog program
    print_formula_to_asp(file, ast, id)
        Write logical formula to designated file
    print_to_asp(type="gst")
        Write generated AST to file
    print_to_dot(type="gst")
        Write and generate DOT file representing the entered Golog program
    """

    precedence = {
        "gst": ["|", ";", "*", "+", "?"],
        "fst": ["+", "&", "~"]
    }
    names = {
        "gst": ["or", "seq", "star", "plus", "test"],
        "fst": ["or", "and", "neg"]
    }
    re = ""
    ast = []
    gst_template = {
        "atom variables": "gst({}, {}) :- {}.\n",
        "atom": "gst({}, {}).\n",
        "node single": "gst({}, {}({})).\n",
        "node double": "gst({}, {}({},{})).\n"
    }
    fst_template = {
        "atom variables": "fst({}, {}, {}) :- {}.\n",
        "atom": "fst({}, {}, {}).\n",
        "node single": "fst({}, {}, {}({})).\n",
        "node double": "fst({}, {}, {}({},{})).\n"
    }
    dot_template = {
        "start": "graph gst {\ngraph [fontname = \"arial\"];\nnode [fontname = \"arial\"];\nedge [fontname = \"arial\"];",
        "leaf": "{} [label=\"{} | {}\" shape=record style=rounded];\n{};\n",
        "node": "{} [label=\"{} | {}\" shape=record style=rounded penwidth=2];\n{} -- {};\n",
        "end": "}"
    }
    formulas = {}
    asp_file = "gst.lp"
    dot_file = "gst.dot"

    def __init__(self, prog):
        """
        Parameters
        ----------
        prog : str
            Golog program from command line
        """

        self.re = prog

    def get_name(self, op, type="gst"):
        """
        Returns the name of the given operator

        Parameters
        ----------
        op : str
            The Golog/logical operator to get the name from
        type : str, optional
            Used to determine the list to search the name for (default is gst); 
            gst: Golog operator 
            fst: logical operator

        Returns
        -------
        str
            The name of the given operator
        """

        return self.names[type][self.precedence[type].index(op)]

    def get_workable_prog(self, type="gst", exp=None):
        """
        Prepares the entered Golog program for further processing

        Parameters
        ----------
        type : str, optional
            Used to determine how to process the given string (default is gst)
            gst: The Golog program from the command line
            fst: A fluent formula (in combination with exp)
        exp : None, optional
            Used to enter a fluent formula string in combination with type (default is None)

        Returns
        -------
        list
            The entered and prepared Golog program as a list for further processing
        """

        prog = ""

        if type == "gst":
            prog = self.re
            prog = prog.replace(" ", "")
            # remove ASP style comments
            prog = sub(r'%[a-zA-Z0-9\-_:;\.,\s\{\}\(\)\*\+\-\&~]+\n', "", prog)
            prog = prog.replace("\n", "")
            prog = prog.replace("\r", "")
            prog = prog.replace("\t", "")

            # filter fluent formulas
            matches = finditer('#[a-zA-Z_\(\)\{\}0-9+\-\*=!&~\[\],\s]+#\?', prog)

            try:
                # replace fluent formula in Golog program to prevent problems
                # with further processing (formulas are handled separately) 
                while True:
                    m = next(matches)
                    saved = False

                    m.group()[1:-2]

                    for key, value in self.formulas.items():
                        if m.group()[1:-2] == value:
                            saved = True
                            break

                    # no doublets allowed
                    if not saved:
                        self.formulas[m.span()[0]+1] = m.group()[1:-2]
                        
                        prog = prog.replace(m.group()[:-1], str(m.span()[0]+1))
            except StopIteration:
                pass

            # make prog splittable
            prog = prog.replace(";", " ; ")
            prog = prog.replace("|", " | ")
            prog = prog.replace("[", " [ ")
            prog = prog.replace("]", " ] ")
            prog = prog.replace("*", " * nil ")
            prog = prog.replace("?", " ? nil ")
        elif type == "fst" and exp != None:
            prog = exp
            prog = prog.replace("[", " [ ")
            prog = prog.replace("]", " ] ")
            prog = prog.replace("&", " & ")
            prog = prog.replace("+", " + ")
            prog = prog.replace("~", "nil ~ ")

            if prog[0] == "[":
                prog = prog[1:]
            if prog[-1] == "]":
                prog = prog[:-1]

        prog = prog.replace("  ", " ")
        prog = prog.strip()
        prog = prog.split(" ")

        return prog


    def get_ast_node(self, op_stack, output_stack, type="gst"):
        """
        Creates an AST node represented as a three tuple
        
        Parameters
        ----------
        op_stack : list
            The operator stack (Shunting Yard)
        output_stack : list
            The output stack (Shunting Yard)
        type : str, optional
            Used to determine where to look for the operator name (default is gst)
            gst: Golog operators
            fst: logical operators
        """

        right = output_stack.pop()
        left = output_stack.pop()
        label = self.get_name(op_stack.pop(), type=type)

        return (left, label, right)

    
    def get_ast(self, type="gst", exp=None):
        """
        Creates abstract syntax trees for Golog programs and fluent formulas based on Dijkstra's 
        Shunting Yard Algorithm

        Parameters
        ----------
        type : str, optional
            Used to determine what AST is to be created (formula or Golog)
            (default is gst)
        exp : None
            If type is 'fst' then exp holds the fluent formula for which
            the AST is to be generated

        Returns
        -------
        list
            If type is gst the whole AST of the entered Golog program is returned, otherwise
            the AST of the given fluent formula
        """
        if len(self.ast) == 0 or type == "fst":
            if type == "gst":
                prog = self.get_workable_prog(type=type)
            elif type == "fst" and exp != None:
                prog = self.get_workable_prog(type=type, exp=exp)

            op_stack = []
            output_stack = []

            for c in prog:
                # If it's a number add it to queue
                if not (c in self.precedence[type]) and c != "[" and c != "]":
                    output_stack.append((None,c,None))
                if c == "[":
                    op_stack.append(c)
                if c == "]":
                    while op_stack[-1] != "[" and len(op_stack) > 0:
                        output_stack.append(self.get_ast_node(op_stack, output_stack, type))
                    
                    op_stack.pop()
                # If it's an operator
                if c in self.precedence[type]:
                    if len(op_stack) == 0:
                        op_stack.append(c)
                    else:
                        while len(op_stack) > 0 \
                            and op_stack[-1] in self.precedence[type] \
                            and self.precedence[type].index(c) < self.precedence[type].index(op_stack[-1]):
                            
                            output_stack.append(self.get_ast_node(op_stack, output_stack, type))
                        
                        op_stack.append(c)
            
            # just put the rest on the output stack
            while len(op_stack) > 0:
                output_stack.append(self.get_ast_node(op_stack, output_stack, type))

            if type == "gst":
                self.ast = output_stack
        
        if type == "gst":
            return self.ast
        else:
            return output_stack

    def extract_clause(self, string):
        """
        Extracts the head and body of horn clauses from entered 
        strings like 'move(R,D){robot(R),direction(D)}'. Needed to 
        write safe ASP

        Parameters
        ----------
        string : str
            A string that may contain head and body of a horn clause

        Returns
        -------
        str, str
            Returns the found head and body or None, None
        """
        body = findall('\{[a-zA-Z\(\),0-9_]+\}', string)

        if len(body) == 1:
            body = str(body[0])

            string = string.replace(body, "")
            string = string.replace("}", "")

            body = body.replace("{", "")
            body = body.replace("}", "")

            return string, body
        elif len(body) > 1: # needed for printing to dot, because the whole formula will be printed as is
            for b in body:
                string = string.replace(b, "")

            return string, ""


        return None, None

    def print_formula_to_asp(self, file, ast, id):
        """
        Prints a given AST of a fluent formula to ASP
        
        Parameters
        ----------
        file : IO
            The object of the output file
        ast : list
            The abstract syntax tree of the fluent formula
        id : int
            The ID of the formula AST
        """
        queue = ast

        file.write("\n")

        i = 0
        j = 0
        while len(queue) > 0:
            node = queue.pop(0)
            el = node[1]

            if el == "nil":
                continue
            # atom?
            if not (el in self.names["fst"]):
                head, body = self.extract_clause(el)

                if head != None:
                    file.write(self.fst_template["atom variables"].format(id, i, head, body))
                else:
                    file.write(self.fst_template["atom"].format(id, i, el))
            else: # operator!
                if el == "neg":
                    index = j+1
                    j = index
                    file.write(self.fst_template["node single"].format(id, i, el, index))
                else:
                    index1 = j+1
                    index2 = index1+1
                    j = index2
                    file.write(self.fst_template["node double"].format(id, i, el, index1, index2))
            
            if node[0] != None:
                queue.append(node[0])
            if node[2] != None:
                queue.append(node[2])

            i += 1

        file.write("\n")

    def print_to_asp(self, type="gst"):
        """
        Writes the entered Golog program as an AST to an ASP file
        
        Parameters
        ----------
        type : str, optional
            Used to determine what operator names are to be used (default is gst)
            gst: Golog operators
            fst: logical operators
        """
        f = open(self.asp_file, 'w')

        queue = []

        node = self.get_ast()[0]
        queue.append(node)

        f.write("%*\n{}\n*%\n".format(self.re))

        i = 0
        j = 0
        while len(queue) > 0:
            node = queue.pop(0)
            el = node[1]

            if el == "nil":
                continue
            # atom?
            if not (el in self.names[type]):
                head, body = self.extract_clause(node[1])

                if head != None:
                    f.write(self.gst_template["atom variables"].format(i, head, body))
                else:
                    # fluent formula?
                    try:
                        fre_ast = self.get_ast(type="fst", exp=self.formulas[int(el)])

                        self.print_formula_to_asp(f, fre_ast, i)
                    except:
                        f.write(self.gst_template["atom"].format(i, el))
            else: # operator!
                if el == "star" or el == "test":
                    index = j+1
                    j = index
                    f.write(self.gst_template["node single"].format(i, el, index))
                else:
                    index1 = j+1
                    index2 = index1+1
                    j = index2
                    f.write(self.gst_template["node double"].format(i, el, index1, index2))
            
            if node[0] != None:
                queue.append(node[0])
            if node[2] != None:
                queue.append(node[2])

            i += 1

        f.close()

    def print_to_dot(self, type="gst"):
        """
        Generates a DOT file (and PNG) representing the Golog program as an AST
        
        Parameters
        ----------
        type : str, optional
            Used to determine the operator names and the output depth;
            fluent formulas are printed as is inside one single node
            (default is gst)
        """
        f = open(self.dot_file, 'w')
        queue = []

        node = self.get_ast()[0]
        queue.append(node)

        f.write(self.dot_template["start"])

        i = 0
        j = 0
        while len(queue) > 0:
            node = queue.pop(0)
            el = node[1]

            if el == "nil":
                continue
            # atom?
            if not (el in self.names[type]):
                try:
                    el = self.formulas[int(el)]

                    head, body = self.extract_clause(el)
                    if head == None:
                        head = el

                    if head[0] == "[":
                        head = head[1:]
                    if head[-1] == "]":
                        head = head[:-1]
                except:
                    head, body = self.extract_clause(node[1])

                if head != None:
                    f.write(self.dot_template["leaf"].format(i, i, head, i))
                else:
                    f.write(self.dot_template["leaf"].format(i, i, el, i))
            else: # operator!
                if el == "star" or el == "test":
                    index = j+1
                    j = index

                    f.write(self.dot_template["node"].format(i, i, el.upper(), i, index))
                else:
                    index1 = j+1
                    index2 = index1+1
                    j = index2

                    f.write(self.dot_template["node"].format(i, i, el.upper(), i, index1))
                    f.write(self.dot_template["node"].format(i, i, el.upper(), i, index2))
            
            if node[0] != None:
                queue.append(node[0])
            if node[2] != None:
                queue.append(node[2])

            i += 1

        f.write(self.dot_template["end"])

        f.close()

        call(["dot", "-Tpng", self.dot_file, "-O"])
    
def main():
    if len(argv) < 2:
        raise RuntimeError("No Golog expression specified. Syntax is: Python3 golog-to-asp.py \"[GOLOG_PROGRAM]\"")
    else:
        encoder = GOLOGToASP(argv[1])
        encoder.print_to_asp()
        encoder.print_to_dot()

if __name__ == "__main__":
    main()