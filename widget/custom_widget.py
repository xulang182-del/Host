import sys

from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QEnterEvent, QPainter, QColor, QPen
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtWidgets import QWidget

# 枚举左上右下以及四个定点
Left, Top, Right, Bottom, LeftTop, RightTop, LeftBottom, RightBottom = range(8)


class TitleBar(QWidget):
    # 窗口最小化信号
    windowMinimized = pyqtSignal()
    # 窗口最大化信号
    windowMaximized = pyqtSignal()
    # 窗口还原信号
    windowNormalized = pyqtSignal()
    # 窗口关闭信号
    windowClosed = pyqtSignal()
    # 窗口移动
    windowMoved = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super(TitleBar, self).__init__(parent)
        # 初始高度
        self.setHeight()

    def connect_max_signal(self, maximizeButton):
        maximizeButton.clicked.connect(self.windowMaximized.emit)

    def connect_min_signal(self, minimizeButton):
        minimizeButton.clicked.connect(self.windowMinimized.emit)

    def connect_close_signal(self, closeButton):
        closeButton.clicked.connect(self.windowClosed.emit)

    def setHeight(self, height=20):
        """设置标题栏高度"""
        self.setMinimumHeight(height)
        self.setMaximumHeight(height)

    def setIconSize(self, size):
        """设置图标大小"""
        self.iconSize = size

    def enterEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super(TitleBar, self).enterEvent(event)

    def mouseDoubleClickEvent(self, event):
        super(TitleBar, self).mouseDoubleClickEvent(event)
        self.showMaximized()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.mPos = event.pos()
        event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标弹起事件"""
        self.mPos = None
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mPos:
            self.windowMoved.emit(self.mapToGlobal(event.pos() - self.mPos))
        event.accept()

    def setTitle(self, title):
        if hasattr(self, "title"):
            self.title.setText(title)
        else:
            QMessageBox.warning(self, "Attribute error", "no attribute: title")

    def setIcon(self):
        if hasattr(self, "icon"):
            self.icon.setIcon()
        else:
            QMessageBox.warning(self, "Attribute error", "no attribute: icon")


class FramelessWindow(QWidget):
    Margins = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mpos = None
        self.resize(500, 500)
        self._pressed = False
        self.Direction = None
        # 鼠标跟踪
        self.setMouseTracking(True)
        self.setWindowFlags(Qt.FramelessWindowHint)

    def connect_title_bar(self, titleBar):
        titleBar.windowMinimized.connect(self.showMinimized)
        titleBar.windowMaximized.connect(self.showMaximized)
        titleBar.windowNormalized.connect(self.showNormal)
        titleBar.windowClosed.connect(self.close)
        titleBar.windowMoved.connect(self.move)
        self.windowTitleChanged.connect(titleBar.setTitle)
        self.windowIconChanged.connect(titleBar.setIcon)

    def move(self, *pos):
        if self.windowState() == Qt.WindowMaximized or self.windowState() == Qt.WindowFullScreen:
            return
        super(FramelessWindow, self).move(*pos)

    def showMaximized(self):
        super(FramelessWindow, self).showMaximized()
        self.layout().setContentsMargins(0, 0, 0, 0)

    def showNormal(self):
        super(FramelessWindow, self).showNormal()
        self.layout().setContentsMargins(
            self.Margins, self.Margins, self.Margins, self.Margins)

    def eventFilter(self, obj, event):
        if isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)
        return super(FramelessWindow, self).eventFilter(obj, event)

    def paintEvent(self, event):
        super(FramelessWindow, self).paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(QColor(255, 255, 255, 1), 2 * 5))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        super(FramelessWindow, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._mpos = event.pos()
            self._pressed = True

    def mouseReleaseEvent(self, event):
        super(FramelessWindow, self).mouseReleaseEvent(event)
        self._pressed = False
        self.Direction = None

    def mouseMoveEvent(self, event):
        super(FramelessWindow, self).mouseMoveEvent(event)
        pos = event.pos()
        xPos, yPos = pos.x(), pos.y()
        wm, hm = self.width() - self.Margins, self.height() - self.Margins
        if self.isMaximized() or self.isFullScreen():
            self.Direction = None
            self.setCursor(Qt.ArrowCursor)
            return
        if event.buttons() == Qt.LeftButton and self._pressed:
            self._resizeWidget(pos)
            return
        if xPos <= self.Margins and yPos <= self.Margins:
            self.Direction = LeftTop
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= xPos <= self.width() and hm <= yPos <= self.height():
            self.Direction = RightBottom
            self.setCursor(Qt.SizeFDiagCursor)
        elif wm <= xPos and yPos <= self.Margins:
            self.Direction = RightTop
            self.setCursor(Qt.SizeBDiagCursor)
        elif xPos <= self.Margins and hm <= yPos:
            self.Direction = LeftBottom
            self.setCursor(Qt.SizeBDiagCursor)
        elif 0 <= xPos <= self.Margins <= yPos <= hm:
            self.Direction = Left
            self.setCursor(Qt.SizeHorCursor)
        elif wm <= xPos <= self.width() and self.Margins <= yPos <= hm:
            self.Direction = Right
            self.setCursor(Qt.SizeHorCursor)
        elif wm >= xPos >= self.Margins >= yPos >= 0:
            self.Direction = Top
            self.setCursor(Qt.SizeVerCursor)
        elif self.Margins <= xPos <= wm and hm <= yPos <= self.height():
            self.Direction = Bottom
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.CustomCursor)

    def _resizeWidget(self, pos):
        if self.Direction is None:
            return
        mpos = pos - self._mpos
        xPos, yPos = mpos.x(), mpos.y()
        geometry = self.geometry()
        x, y, w, h = geometry.x(), geometry.y(), geometry.width(), geometry.height()
        if self.Direction == LeftTop:  
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
        elif self.Direction == RightBottom: 
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos = pos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos = pos
        elif self.Direction == RightTop:
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos.setX(pos.x())
        elif self.Direction == LeftBottom: 
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos.setY(pos.y())
        elif self.Direction == Left: 
            if w - xPos > self.minimumWidth():
                x += xPos
                w -= xPos
            else:
                return
        elif self.Direction == Right: 
            if w + xPos > self.minimumWidth():
                w += xPos
                self._mpos = pos
            else:
                return
        elif self.Direction == Top:
            if h - yPos > self.minimumHeight():
                y += yPos
                h -= yPos
            else:
                return
        elif self.Direction == Bottom: 
            if h + yPos > self.minimumHeight():
                h += yPos
                self._mpos = pos
            else:
                return
        self.setGeometry(x, y, w, h)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = FramelessWindow()
    main.show()
    sys.exit(app.exec_())
