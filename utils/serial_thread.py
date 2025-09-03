import os
import time
import re
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import (QIODevice, QByteArray, QThread, pyqtSignal, pyqtSlot,
                          QMutex, QTimer)


class SerialWorker(QThread):
    data_received = pyqtSignal(str)
    file_progress = pyqtSignal(int, int)
    file_completed = pyqtSignal(str)
    file_transfer_started = pyqtSignal(str, int)
    error_occurred = pyqtSignal(str)
    refresh_com = pyqtSignal(list)
    clock_corrected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial = QSerialPort()
        self.buffer = QByteArray()
        self.running = True
        self.mutex = QMutex()
        self.file_sending = False
        self.file_path = ""
        self.file_name = ""
        self.file_size = 0
        self.block_size = 1024
        self.total_blocks = 0
        self.blocks_sent = 0
        self.transfer_paused = False
        self.timeout_ms = 3000
        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self.handle_timeout)
        self.retry_count = 0
        self.max_retries = 3
        self.scan_timer = QTimer(self)
        self.scan_timer.timeout.connect(self.scan_com_ports)
        self.scan_timer.start(2000)

    def run(self):
        self.exec_()

    def scan_com_ports(self):
        com_ports = [
            info.portName() for info in QSerialPortInfo.availablePorts()
        ]
        self.refresh_com.emit(com_ports)

    @pyqtSlot(str, int)
    def connect_port(self, port_name, baudrate):
        if self.serial.isOpen():
            self.serial.close()
        self.serial.setPortName(port_name)
        self.serial.setBaudRate(baudrate)
        self.serial.setDataBits(QSerialPort.DataBits.Data8)
        self.serial.setParity(QSerialPort.Parity.NoParity)
        self.serial.setStopBits(QSerialPort.StopBits.OneStop)
        self.serial.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
        if self.serial.open(QIODevice.OpenModeFlag.ReadWrite):
            self.serial.readyRead.connect(self.read_serial_data)
            self.data_received.emit(f"串口 {port_name} 已连接 (波特率: {baudrate})")
        else:
            self.error_occurred.emit(f"串口连接失败: {self.serial.errorString()}")

    @pyqtSlot()
    def disconnect_port(self):
        if self.serial.isOpen():
            self.serial.close()
            self.data_received.emit("串口已断开连接")
        self.file_sending = False

    def read_serial_data(self):
        if not self.serial.isOpen():
            return
        data = self.serial.readAll()
        self.buffer.append(data)
        self.process_received_data()

    def process_received_data(self):
        while self.buffer.contains(b'\r\n'):
            line_end = self.buffer.indexOf(b'\r\n')
            line = self.buffer.left(line_end).data().decode('utf-8',
                                                            errors='ignore')
            self.buffer = self.buffer.mid(line_end + 2)
            self.data_received.emit(f"设备: {line}")
            if self.file_sending and not self.transfer_paused:
                if line == "READY":
                    self.retry_timer.stop()
                    self.retry_count = 0
                    self.send_next_block()
                elif line.startswith("file transfer complete"):
                    self.file_sending = False
                    self.file_completed.emit(self.file_name)
                    self.data_received.emit(f"文件传输完成: {self.file_name}")

    @pyqtSlot(str)
    def send_file(self, file_path):
        if not os.path.exists(file_path):
            self.error_occurred.emit(f"文件不存在: {file_path}")
            return
        if self.file_sending:
            self.error_occurred.emit("已有文件正在传输，请先等待完成")
            return
        try:
            self.file_path = file_path
            self.file_name = os.path.basename(file_path)
            self.file_size = os.path.getsize(file_path)
            self.block_size = 512
            header_cmd = f"FILE_{self.file_name}_{self.block_size} {self.file_size}\r\n"
            self.total_blocks = (self.file_size + self.block_size -
                                 1) // self.block_size
            self.blocks_sent = 0
            self.mutex.lock()
            self.serial.write(header_cmd.encode())
            self.mutex.unlock()
            self.file_sending = True
            self.file_transfer_started.emit(self.file_name, self.file_size)
            self.data_received.emit(
                f"开始传输文件: {self.file_name} (大小: {self.file_size}字节)")
            self.retry_timer.start(self.timeout_ms)
        except Exception as e:
            self.error_occurred.emit(f"文件传输初始化失败: {str(e)}")
            self.file_sending = False

    def send_next_block(self):
        time.sleep(0.001)
        if self.blocks_sent >= self.total_blocks:
            self.file_sending = False
            self.file_completed.emit(self.file_name)
            return
        try:
            with open(self.file_path, 'rb') as f:
                f.seek(self.blocks_sent * self.block_size)
                block_data = f.read(self.block_size)
                self.mutex.lock()
                bytes_written = self.serial.write(block_data)
                self.mutex.unlock()
                if bytes_written != len(block_data):
                    raise Exception(
                        f"数据发送不完整 (发送: {bytes_written}/{len(block_data)})")
                self.blocks_sent += 1
                self.file_progress.emit(self.blocks_sent, self.total_blocks)
                self.data_received.emit(
                    f"发送块 {self.blocks_sent}/{self.total_blocks} (大小: {len(block_data)})"
                )
                self.retry_timer.start(self.timeout_ms)
        except Exception as e:
            self.error_occurred.emit(f"块发送失败: {str(e)}")
            self.handle_timeout()

    def handle_timeout(self):
        self.retry_count += 1
        if self.retry_count > self.max_retries:
            self.file_sending = False
            self.error_occurred.emit(f"传输超时，已超过最大重试次数 ({self.max_retries})")
            return
        self.data_received.emit(
            f"超时重试 {self.retry_count}/{self.max_retries}...")
        self.send_next_block()

    @pyqtSlot()
    def correct_clock(self):
        try:
            timestamp = int(time.time() + 8 * 3600)
            cmd = f"CORRECT_CLOCK {timestamp}\r\n"
            self.mutex.lock()
            self.serial.write(cmd.encode())
            self.mutex.unlock()
            self.data_received.emit(f"发送时钟校准命令: {timestamp}")
            self.clock_corrected.emit()
        except Exception as e:
            self.error_occurred.emit(f"时钟校准失败: {str(e)}")

    @pyqtSlot(str)
    def send_test_command(self):
        cmd = "TEST 0\r\n"
        self.mutex.lock()
        self.serial.write(cmd.encode())
        self.mutex.unlock()
        self.data_received.emit("发送测试命令")

    @pyqtSlot(str)
    def send_custom_command(self, cmd):
        if not cmd.endswith("\r\n"):
            cmd += "\r\n"
        self.mutex.lock()
        self.serial.write(cmd.encode())
        self.mutex.unlock()
        self.data_received.emit(f"发送命令: {cmd.strip()}")

    def stop(self):
        self.running = False
        self.scan_timer.stop()
        self.retry_timer.stop()
        if self.serial.isOpen():
            self.serial.close()
        self.quit()
        self.wait()
