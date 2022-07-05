from statistics import mean
import subprocess 
import json
import sys
import os
import threading
import json

from statusWindow import Window, QApplication
from throttle import throttle

app = QApplication(sys.argv)
window = Window()
window.show()

countSubprocess = 300
# try:
#     countSubprocess = int(sys.argv[len(sys.argv)-1])
# except:
#     pass

CMD_PREFIX = ["powershell"]

SYSTEM_ENCODING='cp1251'#'utf-8'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Process:
    def __init__(self, cmd):
            self.process = subprocess.Popen( CMD_PREFIX + cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT
                        )
    def lines(self):
        for line in iter(self.process.stdout.readline, b''):
            decodedLine = line.rstrip()
            try:
                decodedLine = decodedLine.decode(SYSTEM_ENCODING)
            except:
                decodedLine = str(decodedLine)[2:-1]
            # print(decodedLine)
            yield decodedLine
        return

    def printAll(self, prefix):
        for line in self.lines():
            print(bcolors.OKBLUE + prefix + bcolors.ENDC, line)


def genStatus():
    return {
        "failed" : 0,
        "success" : 0,
        "timers" : [],
        "comments" : {},
    }


statuses = {
}

update_prefix = "UPDATE"

# update_state_deb = lambda stageName, stage: window.updateStateSignal.emit(stageName, stage) #debouncer(lambda stageName, stage: window.updateStateSignal.emit(stageName, stage))

update_state_deb_support = {}
def update_state_deb(stageName, stage):
    if stageName not in update_state_deb_support:
         update_state_deb_support[stageName] = throttle(lambda stageName, stage: window.updateStateSignal.emit(stageName, stage), 100)
    
    update_state_deb_support[stageName](stageName, stage)


class User:
    def __init__(self, index):
        self.process = Process(["python", "-u", "process.py", index])
        self.index = index

    def scan(self):
        for line in self.process.lines():
            log(bcolors.HEADER + self.index + bcolors.ENDC, line)

            if line[:len(update_prefix)] == update_prefix:
                parts = line.split(' ')
                stage = parts[1]
                status = parts[2]
                time = float(parts[3])
                comment = ' '.join(parts[4:])

                if stage not in statuses:
                    statuses[stage] = genStatus()

                statuses[stage][status] = statuses[stage].get(status, 0) + 1
                statuses[stage]["timers"].append(time)
                statuses[stage]["comments"][self.index] = comment
                
                update_state_deb(stage, statuses[stage])

                log(bcolors.OKGREEN + stage + bcolors.ENDC, "f:", statuses[stage]["failed"], "; s:", statuses[stage]["success"])
                log(bcolors.OKGREEN + stage + bcolors.ENDC, "timers:", 
                        min(statuses[stage]["timers"]), 
                        mean(statuses[stage]["timers"]), 
                        max(statuses[stage]["timers"]))

                



def thread(index):
    User(index).scan()




with open("log.txt", "w", encoding="utf-8") as logfile:
    def log(*args, sep=' ', end='\n', **params):
                    line = sep.join(map(str, args))+end
                    print(line, sep='', end='', **params)
                    print(line, sep='', end='', **params, file=logfile)
    def main():
        process = []
        print("пошли старты")
        for i in range(countSubprocess):
            t = threading.Thread(target=lambda: thread(str(i)))
            process.append(t)
            t.start()

        print("пошли джоины")
        [t.join() for t in process]

        for stage in statuses.keys():
            log(bcolors.WARNING, '=' * 30, bcolors.ENDC)
            log(bcolors.WARNING, stage, bcolors.ENDC)
            for status in statuses[stage].keys():
                if status not in ["timers", "comments"]:
                    log(bcolors.HEADER, status, bcolors.ENDC, ':', statuses[stage][status])
            log("timers:", statuses[stage]['timers'])
            log(bcolors.OKGREEN + 'min:' + bcolors.ENDC, min(statuses[stage]['timers']))
            log(bcolors.OKGREEN + 'mean:' + bcolors.ENDC, mean(statuses[stage]['timers']))
            log(bcolors.OKGREEN + 'max:' + bcolors.ENDC, max(statuses[stage]['timers']))
            log(json.dumps(statuses[stage]["comments"], indent=2, ensure_ascii=False))
        print('конец')

    mainThread = threading.Thread(target=main)
    mainThread.start()
    app.exec_()
    mainThread.join()