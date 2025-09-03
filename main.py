from PyQt5.QtWidgets import QWidget, QFileDialog, QApplication, QDial
from PyQt5.QtCore import QThread, QMetaObject, Q_ARG, Qt, QTimer
from PyQt5 import QtGui
from utils.serial_thread import SerialWorker
from utils.bluetooth_thread import BluetoothWorker
from ui.ui_main_window import Ui_Form
import math
import time
import typing
from ui.ui_camera import Ui_CameraWidget
from utils.camera_thread import CameraWorker
from widget.camera_widget import CameraWidget


class MainWindow(QWidget, Ui_Form):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.serial_worker = SerialWorker()
        self.setup_bluetooth_thread()
        self.ui.connectButton.clicked.connect(self.connect_com)
        self.ui.sendButton.clicked.connect(self.send_data)
        self.ui.blScanButton.clicked.connect(self.start_bluetooth_scan)
        self.ui.blConnectButton.clicked.connect(
            self.toggle_bluetooth_connection)
        self.ui.blSendButton.clicked.connect(self.send_bluetooth_data)
        self.ui.fileChooseButton.clicked.connect(self.choose_file)
        self.ui.sendFileButton.clicked.connect(self.send_file)
        self.serial_worker.data_received.connect(self.handle_serial_data)
        self.serial_worker.file_progress.connect(self.update_file_progress)
        self.serial_worker.clock_corrected.connect(
            self.handle_clock_correction)
        self.serial_worker.file_completed.connect(self.handle_file_complete)
        self.serial_worker.error_occurred.connect(self.show_error)
        self.serial_worker.refresh_com.connect(self.handle_refresh_com)
        """position"""
        self.ui.posDial.move_signal.connect(self.update_position)
        self.ui.posxDoubleSpinBox.keyPressEvent = self.update_position_from_spinbox_x
        self.ui.posyDoubleSpinBox.keyPressEvent = self.update_position_from_spinbox_y
        self.ui.posDial.setWrapping(True)
        self.pos_x = 0
        self.pos_y = 0
        """camera"""
        self.camera_widget = CameraWidget(self.serial_worker)
        self.ui.cameraButton.clicked.connect(self.start_camera)

        self.setup()
        self.pos_file = open("position.yaml", "w")

    def start_camera(self):
        self.camera_widget.show()

    def serial_write(self, string):
        self.serial_worker.serial.write(
            bytes(string + "\r\n", 'utf-8', 'ignore'))

    def update_position_from_spinbox_x(self,
                                       e: typing.Optional[QtGui.QKeyEvent]):
        if not e or e.key() != 16777220:
            return super(type(self.ui.posxDoubleSpinBox),
                         self.ui.posxDoubleSpinBox).keyPressEvent(e)
        print("enter")
        self.pos_x = float(self.ui.posxDoubleSpinBox.text())
        self.pos_y = float(self.ui.posyDoubleSpinBox.text())

        string = f'FMX {self.pos_x:.2f}'
        self.serial_worker.serial.write(
            bytes(string + "\r\n", 'utf-8', 'ignore'))

        string = f'FMY {self.pos_y:.2f}'
        QTimer.singleShot(15, lambda: self.serial_write(string))

    def update_position_from_spinbox_y(self,
                                       e: typing.Optional[QtGui.QKeyEvent]):
        if not e or e.key() != 16777220:
            return super(type(self.ui.posyDoubleSpinBox),
                         self.ui.posyDoubleSpinBox).keyPressEvent(e)
        print("enter")
        self.pos_x = float(self.ui.posxDoubleSpinBox.text())
        self.pos_y = float(self.ui.posyDoubleSpinBox.text())
        string = f'FMX {self.pos_x:.2f}'
        self.serial_worker.serial.write(
            bytes(string + "\r\n", 'utf-8', 'ignore'))

        string = f'FMY {self.pos_y:.2f}'
        QTimer.singleShot(15, lambda: self.serial_write(string))

    def update_position(self, value):
        self.pos_x += math.cos(math.radians((360 - value) // 18 * 18)) * 0.1
        self.pos_y += math.sin(math.radians((360 - value) // 18 * 18)) * 0.1
        self.ui.posxDoubleSpinBox.setValue(self.pos_x)
        self.ui.posyDoubleSpinBox.setValue(self.pos_y)

        string = f'FMX {self.pos_x:.2f}'
        self.serial_worker.serial.write(
            bytes(string + "\r\n", 'utf-8', 'ignore'))

        string = f'FMY {self.pos_y:.2f}'
        QTimer.singleShot(15, lambda: self.serial_write(string))

    def dialDragEnterEvent(self, a0: QtGui.QDragEnterEvent | None) -> None:
        print("drag")

    def setup(self):
        self.bluetooth_worker.scan_devices()

    def handle_refresh_com(self, com_list):
        self.ui.comBox.clear()
        for com in com_list:
            self.ui.comBox.addItem(com)

    def setup_bluetooth_thread(self):
        self.bluetooth_thread = QThread()
        self.bluetooth_worker = BluetoothWorker()
        self.bluetooth_worker.moveToThread(self.bluetooth_thread)
        self.bluetooth_worker.device_discovered.connect(
            self.add_bluetooth_device)
        self.bluetooth_worker.connected.connect(self.on_bluetooth_connected)
        self.bluetooth_worker.disconnected.connect(
            self.on_bluetooth_disconnected)
        self.bluetooth_worker.data_received.connect(self.handle_bluetooth_data)
        self.bluetooth_worker.error_occurred.connect(self.show_error)
        self.bluetooth_thread.start()

    def start_bluetooth_scan(self):
        self.ui.blBox.clear()
        QMetaObject.invokeMethod(self.bluetooth_worker, "scan_devices")

    def add_bluetooth_device(self, name, uuid, address):
        self.ui.blBox.addItem(name)

    def toggle_bluetooth_connection(self):
        if self.bluetooth_worker.socket.isOpen():
            QMetaObject.invokeMethod(self.bluetooth_worker,
                                     "disconnect_device")
        else:
            device_name = self.ui.blBox.currentText()
            if device_name:
                QMetaObject.invokeMethod(self.bluetooth_worker,
                                         "connect_device",
                                         Qt.ConnectionType.QueuedConnection,
                                         Q_ARG(str, device_name))
                self.ui.blConnectButton.setEnabled(False)

    def on_bluetooth_connected(self):
        self.ui.blConnectButton.setEnabled(True)
        self.ui.blConnectButton.setText("disconnect")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/com/icon/com_open.png"),
                       QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ui.blConnectButton.setIcon(icon)
        print("蓝牙已连接")

    def on_bluetooth_disconnected(self):
        self.ui.blConnectButton.setText("connect")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/com/icon/com_close.png"),
                       QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ui.blConnectButton.setIcon(icon)

    def send_bluetooth_data(self):
        text = self.ui.blSendEdit.toPlainText()
        QMetaObject.invokeMethod(self.bluetooth_worker, "send_data",
                                 Qt.ConnectionType.QueuedConnection,
                                 Q_ARG(str, text))

    def handle_bluetooth_data(self, data):
        self.ui.blRecvBrowser.append(f"[蓝牙] {data.decode('utf-8', 'ignore')}")

    def connect_com(self):
        if self.serial_worker.serial.isOpen():
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port_name = self.ui.comBox.currentText()
        baud_rate = int(self.ui.baudrateBox.currentText())
        self.serial_worker.connect_port(port_name, baud_rate)
        if self.serial_worker.serial.isOpen():
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/com/icon/com_open.png"),
                           QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.ui.connectButton.setIcon(icon)
            self.ui.connectButton.setText("close")
            if not self.serial_worker.isRunning():
                self.serial_worker.start()
            self.serial_worker.correct_clock()
        else:
            self.show_error(f"无法打开串口 {port_name}")

    def disconnect_serial(self):
        self.serial_worker.stop()
        if self.serial_worker.serial.isOpen():
            self.serial_worker.serial.close()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/com/icon/com_close.png"),
                       QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.ui.connectButton.setIcon(icon)
        self.ui.connectButton.setText("connect")

    def handle_serial_data(self, data):
        self.ui.recvBrowser.append(f"[串口] {data}")

    def send_data(self):
        if self.serial_worker.serial.isOpen():
            text = self.ui.sendEdit.toPlainText()
            self.serial_worker.serial.write(
                bytes(text + "\r\n", 'utf-8', 'ignore'))

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*);;文本文件 (*.txt);;图片文件 (*.png *.jpg)")
        if file_path:
            self.ui.filePathEdit.setText(file_path)

    def send_file(self):
        if not self.serial_worker.serial.isOpen():
            self.show_error("串口未连接")
            return
        file_path = self.ui.filePathEdit.text()
        if not file_path:
            self.show_error("请先选择文件")
            return
        self.serial_worker.send_file(file_path)

    def update_file_progress(self, current, total):
        self.ui.recvBrowser.append(
            f"文件传输: {current}/{total} 块 ({current/total*100:.1f}%)")

    def handle_clock_correction(self):
        self.ui.recvBrowser.append("时钟校对完成")

    def handle_file_complete(self):
        self.ui.recvBrowser.append("文件传输完成")

    def show_error(self, message):
        self.ui.recvBrowser.append(f"[错误] {message}")

    def closeEvent(self, event):
        self.serial_worker.stop()
        if self.serial_worker.serial.isOpen():
            self.serial_worker.serial.close()
        if self.bluetooth_worker.socket.isOpen():
            self.bluetooth_worker.socket.close()
        super().closeEvent(event)

    def __del__(self):
        pass


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
