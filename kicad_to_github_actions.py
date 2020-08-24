#!/usr/bin/env python3

import argparse
import json
import re

class Violation:
    def __init__(self, num):
        self.num = num
        self.title = ""
        self.details = ""
        self.extra = ""

class Part:
    def __init__(self, type, name):
        self.name = name
        self.type = type
        self.errors = []

    @classmethod
    def from_line(cls, line):
        pattern_part = re.compile("Checking (symbol|footprint) '(.*)'.*")
        pattern_newsym = re.compile(("New '.*\.lib:(.*)'"))

        test_match = pattern_part.match(line)
        if test_match is not None:
            type, name = test_match.groups()
            return cls(type, name)

        test_match = pattern_newsym.match(line)
        if test_match is not None:
            type = "symbol"
            name = test_match.groups()[0]
            return cls(type, name)


def analyse_output(file_path):

    pattern_violating = re.compile("  Violating ([GSFM]\d\d?.\d\d?)")
    pattern_details = re.compile("    (.*)")
    pattern_extra = re.compile("     - (.*)")

    parts = []

    with open(file_path) as f:
        current_part = None
        for line in f.readlines():

            test_part = Part.from_line(line)
            if test_part is not None:
                # New part, so save the old one
                if current_part is not None:
                    parts.append(current_part)
                current_part = test_part
            elif pattern_violating.match(line):
                # Rule violation
                current_part.errors.append(Violation(pattern_violating.match(line).groups()[0]))
            elif pattern_extra.match(line):
                # Try matching this before pattern_details
                # Add to existing violation
                if len(current_part.errors) != 0:
                    v = current_part.errors[-1]
                    if v.extra != "":
                        v.extra += "\n"
                    v.extra += " - " + (pattern_extra.match(line).groups()[0])
            elif pattern_details.match(line):
                # Add to existing violation
                if len(current_part.errors) != 0:
                    v = current_part.errors[-1]
                    if v.title == "":
                        v.title = pattern_details.match(line).groups()[0]
                    else:
                        if v.details != "":
                            v.details += "\n"
                        v.details += (pattern_details.match(line).groups()[0])

        if current_part is not None:
            # End of file, save last part
            parts.append(current_part)

    return parts

def create_output_command(output_name, l):
    j = json.dumps({"include":l})
    command = f"::set-output name={output_name}::" + j
    # Command should be picked up by Github Actions
    return command

def run(file_path):

    parts = analyse_output(file_path)

    for part in parts:
        print(part.name)
        for v in part.errors:
            print("Violating {rule}: {title}".format(rule=v.num,title=v.title))
            print(v.details)
            print(v.extra)
            print("***")

    # Must have at least one string for matrix
    success_strings = [{"name":"Part parser"}]

    failure_strings = []
    for p in parts:
        if len(p.errors) == 0:
            success_strings.append({"name": f"Check {p.type} {p.name}"})
        else:
            for v in p.errors:
                name = f"{p.type.capitalize()} {p.name} -"
                desc = f"{v.num} - {v.title}"
                url = f"https://kicad-pcb.org/libraries/klc/{v.num.upper()}"
                det = f"\n{v.details}\n{v.extra}\n\nRule URL:\n{url}\n\n"
                failure_strings.append({"name":name, "description":desc, "details":det})

    # Must have at least one string for matrix
    if len(failure_strings) == 0:
        failure_strings = [{"name":"Rule", "description":"checks", "details":""}]

    print(create_output_command("parts", success_strings))
    print(create_output_command("rules", failure_strings))

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Analyse kicad-lib-check output and convert to JSON Workflow commands for Github Actions")
    parser.add_argument("input", help="Path to input file containing output from lib checkers")
    args = parser.parse_args()

    run(args.input)
