import sys

name = "log.txt"
if sys.argv[-2] == '-f':
    name = sys.argv[-1]

with open(name, 'r', encoding="utf-8") as logfile:
    for line in logfile:
        print(line, end='')