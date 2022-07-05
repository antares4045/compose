from statistics import mean
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QStyle, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, pyqtSignal
import json

class Window(QWidget):
    updateStateSignal = pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()

        self.labels = {}
        self.mainLayout = QVBoxLayout()

        self.setLayout(self.mainLayout)

        self.updateStateSignal.connect(self.updateState)
    
    def updateState(self, stateName, state):
        # print("updateState", stateName, state)
        
        if stateName not in self.labels:
            self.labels[stateName] = dict()
            layout = QHBoxLayout()

            namePallette = QPalette() 
            namePallette.setColor(QPalette.Text, Qt.red)
            namePallette.setColor(QPalette.WindowText, Qt.red)

            timingPallette = QPalette() 
            timingPallette.setColor(QPalette.Text, Qt.blue)
            timingPallette.setColor(QPalette.WindowText, Qt.blue)

            self.labels[stateName]['labelName'] = QLabel(stateName)
            self.labels[stateName]['labelTiming'] = QLabel()
            self.labels[stateName]['labelStatus'] = QLabel()

            self.labels[stateName]['labelName'].setPalette(namePallette)
            self.labels[stateName]['labelTiming'].setPalette(timingPallette)


            layout.addWidget(self.labels[stateName]['labelName'])
            layout.addWidget(self.labels[stateName]['labelTiming'])
            layout.addWidget(self.labels[stateName]['labelStatus'])

            self.mainLayout.addLayout(layout) 

        stateLevel = self.labels[stateName]

        stateLevel['labelTiming'].setText(
            f"""
min: {min(state['timers'])}
max: {max(state['timers'])}
mean: {mean(state['timers'])}
            """
        )

        dictRes = {}
        for key in state:
            if key not in ['timers', 'comments']:
                dictRes[key] = state[key]
        
        stateLevel['labelStatus'].setText(json.dumps(dictRes, indent=2, ensure_ascii=False))
        
    
