import PyQt5.QtGui
from PyQt5.QtCore import (QIODevice, QByteArray, QObject, QThread, pyqtSignal,
                          pyqtSlot, QMutex, QTimer)
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPixmap
from ui.ui_camera import Ui_CameraWidget
from utils.camera_thread import CameraWorker
from utils.serial_thread import SerialWorker
from calc_pos.get_mov_xy import CoordinateTransformer
import math


def position_distance_calc(point1, point2):
    distance = math.sqrt((point1[0] - point2[0])**2 +
                         (point1[1] - point2[1])**2)
    return distance


class GetPosThread(QThread):
    serial_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.point1 = []
        self.point2 = []
        self.camera_opened = False

    def set_points(self, point):
        if not self.point1:
            self.point1 = point
            return
        if position_distance_calc(self.point1, point) > 20:
            self.point2 = self.point1
            self.point1 = point

    def run(self):
        while not self.camera_opened:
            pass
        # open laser
        self.serial_signal.emit("open laser")

        while not self.point1:
            pass
        print(f"get point1: {self.point1}")
        self.serial_signal.emit("SLD_VA 1.25")
        while not self.point2:
            pass
        print(f"get point2: {self.point2}")
        delta_mov_x, delta_mov_y = CoordinateTransformer().calculate_movement(
            self.point2[0], self.point2[1], self.point1[0], self.point1[1])
        self.serial_signal.emit(f"FMX {delta_mov_x:.2f}")
        QThread.msleep(20)
        self.serial_signal.emit(f"FMY {delta_mov_y:.2f}")
        while True:
            pass


class CameraWidget(QWidget):
    recognize_points = []

    def __init__(self, serial_thread: SerialWorker) -> None:
        super().__init__()
        self.ui = Ui_CameraWidget()
        self.ui.setupUi(self)
        self.camera_worker = CameraWorker(self)
        self.camera_worker.image_processed.connect(self.update_img)
        self.camera_worker.points_detected.connect(self.process_points)
        self.ui.startButton.clicked.connect(self.start_camera)
        self.serial_thread = serial_thread
        self.get_pos_thread = GetPosThread()
        self.get_pos_thread.serial_signal.connect(self.serial_write)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.is_camera_opened)
        self.timer.start(1000)

    def is_camera_opened(self):
        if not self.camera_worker.camera:
            return
        if self.camera_worker.camera.isOpened():
            self.get_pos_thread.camera_opened = True

    def serial_write(self, string):
        self.serial_thread.serial.write(
            bytes(string + '\r\n', 'utf-8', 'ignore'))

    def start_camera(self):
        if not self.camera_worker.stop:
            self.camera_worker.stop = True
            self.ui.startButton.setText("Start")
            return
        self.camera_worker.stop = False
        self.ui.startButton.setText("Stop")
        if self.camera_worker.isRunning():
            return
        self.camera_worker.start()
        self.get_pos_thread.start()

    def update_img(self, img: QImage):
        pixmap = QPixmap(img)
        self.ui.imgLabel.setPixmap(pixmap)

    def process_points(self, points_list):
        if not points_list:
            return
        print(points_list)
        point = points_list[0]
        self.ui.xEdit.setText(f"{point[0]}")
        self.ui.yEdit.setText(f"{point[1]}")
        self.get_pos_thread.set_points(point)

    def __del__(self):
        print("del camera worker")
        self.camera_worker.stop = True
        self.camera_worker.deleteLater()
        if self.camera_worker.camera:
            self.camera_worker.camera.release()
