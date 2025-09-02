from PyQt5.QtCore import QObject, pyqtSignal, QByteArray
from PyQt5.QtBluetooth import (QBluetoothDeviceDiscoveryAgent,
                               QBluetoothSocket, QBluetoothServiceInfo,
                               QBluetoothAddress, QBluetoothUuid)


class BluetoothWorker(QObject):
    device_discovered = pyqtSignal(str, str, str)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.discovery_agent = QBluetoothDeviceDiscoveryAgent()
        self.discovery_agent.deviceDiscovered.connect(
            self.handle_device_discovered)
        self.socket = QBluetoothSocket(
            QBluetoothServiceInfo.Protocol.RfcommProtocol)
        self.socket.connected.connect(self.handle_connected)
        self.socket.disconnected.connect(self.handle_disconnected)
        self.socket.readyRead.connect(self.handle_data_received)
        self.buffer = QByteArray()
        self.devices = {}

    def scan_devices(self):
        self.devices.clear()
        self.discovery_agent.start()

    def connect_device(self, device_name):
        if device_name not in self.devices:
            self.error_occurred.emit(f"设备 {device_name} 未找到")
            return
        if self.socket.isOpen():
            self.socket.close()
        _, address = self.devices[device_name]
        uuid = QBluetoothUuid(QBluetoothUuid.SerialPort)
        self.socket.connectToService(QBluetoothAddress(address), uuid)

    def disconnect_device(self):
        if self.socket.isOpen():
            self.socket.close()

    def send_data(self, data):
        if self.socket.isOpen():
            self.socket.write(data.encode() + b"\r\n")
        else:
            self.error_occurred.emit("未连接到蓝牙设备")

    def handle_device_discovered(self, device_info):
        name = device_info.name()
        uuid = device_info.deviceUuid().toString()
        address = device_info.address().toString()
        self.devices[name] = [uuid, address]
        self.device_discovered.emit(name, uuid, address)

    def handle_connected(self):
        self.connected.emit()

    def handle_disconnected(self):
        self.disconnected.emit()

    def handle_data_received(self):
        data = self.socket.readAll().data()
        self.data_received.emit(data)

    def handle_discovery_error(self, error):
        self.error_occurred.emit(f"扫描错误: {error}")

    def handle_socket_error(self, error):
        self.error_occurred.emit(f"连接错误: {error}")
