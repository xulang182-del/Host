from PyQt5.QtWidgets import QWidget, QFileDialog, QApplication, QDial
from PyQt5 import QtGui, QtCore


class DragDial(QDial):
    move_signal = QtCore.pyqtSignal(int)
    key_enter_siganl = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_position)
        
        self.sliderPressed.connect(self.handle_drag_start)
        self.sliderMoved.connect(self.handle_drag_move)
        self.sliderReleased.connect(self.handle_drag_end)

    def handle_drag_start(self, *arg):
        self.timer.start(50)
        
    def handle_drag_move(self, *arg):
        pass
        
    def handle_drag_end(self, *arg):
        self.timer.stop()
        
    def update_position(self):
        self.move_signal.emit(self.value())
        
    def keyPressEvent(self, ev: QtGui.QKeyEvent) -> None:
        if ev.key() == QtCore.Qt.Key_Enter:
            self.key_enter_siganl.emit()
        