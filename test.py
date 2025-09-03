from PyQt5.QtWidgets import QWidget, QFileDialog, QApplication, QDial
from PyQt5.QtCore import QThread, QMetaObject, Q_ARG, Qt, QTimer
from PyQt5 import QtGui
from utils.serial_thread import SerialWorker
from utils.bluetooth_thread import BluetoothWorker
import math
import time
import typing

class PositionTest(QWidget):
    def __init__(self):
        super().__init__()
        self.pos_file = open("position.yaml", "r")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_position)
        
    def update_position(self):
        pass
