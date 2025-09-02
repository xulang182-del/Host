import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QSizePolicy, QHBoxLayout
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

class DraggableBallWidget(QWidget):
    """自定义可拖动小球控件"""
    
    positionChanged = pyqtSignal(float, float)  # 位置变化信号(X, Y)
    
    def __init__(self, size=300, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(size, size)
        
        # 控件参数设置
        self.ball_radius = 18
        self.border_width = 4
        self.border_color = QColor(100, 150, 200)
        self.ball_color = QColor(220, 80, 80)
        self.highlight_color = QColor(255, 190, 80)
        
        # 小球初始位置在中心
        self.ball_pos = QPoint(self.width() // 2, self.height() // 2)
        self.is_dragging = False
        
        # 坐标显示文字
        self.position_text = "X: 0.5, Y: 0.5"
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制边框
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(
            self.border_width // 2, 
            self.border_width // 2,
            -self.border_width // 2,
            -self.border_width // 2
        ))
        
        # 绘制背景网格
        pen.setColor(QColor(230, 230, 230, 150))
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 绘制网格线
        grid_size = 20
        for i in range(grid_size, self.width(), grid_size):
            painter.drawLine(i, 0, i, self.height())
        for i in range(grid_size, self.height(), grid_size):
            painter.drawLine(0, i, self.width(), i)
        
        # 绘制坐标原点
        painter.setBrush(QBrush(QColor(120, 200, 150)))
        painter.drawEllipse(QPoint(self.border_width*2, self.border_width*2), 4, 4)
        
        # 绘制小球
        painter.setPen(Qt.NoPen)
        
        # 如果正在拖动，使用高亮颜色
        if self.is_dragging:
            painter.setBrush(self.highlight_color)
        else:
            painter.setBrush(self.ball_color)
            
        painter.drawEllipse(self.ball_pos, self.ball_radius, self.ball_radius)
        
        # 绘制小球内高光
        painter.setBrush(Qt.white)
        painter.drawEllipse(self.ball_pos.x()-self.ball_radius//3, 
                          self.ball_pos.y()-self.ball_radius//3, 
                          self.ball_radius//2, 
                          self.ball_radius//2)
        
        # 绘制坐标系信息
        painter.setPen(QColor(50, 50, 50))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, self.height() - 20, f"({self.ball_pos.x()-self.border_width}, {self.ball_pos.y()-self.border_width})")
        
        # 绘制标准化坐标
        painter.setPen(QColor(80, 80, 80))
        norm_x = (self.ball_pos.x() - self.border_width) / (self.width() - self.border_width * 2)
        norm_y = (self.ball_pos.y() - self.border_width) / (self.height() - self.border_width * 2)
        norm_text = f"X: {norm_x:.2f}, Y: {norm_y:.2f}"
        painter.drawText(self.width() - 150, self.height() - 20, norm_text)
        
    def mousePressEvent(self, event):
        # 检查是否点在球上
        if (event.pos() - self.ball_pos).manhattanLength() <= self.ball_radius:
            self.is_dragging = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            # 限制小球在边界内（考虑边框和球半径）
            new_x = max(self.border_width + self.ball_radius, 
                      min(self.width() - self.border_width - self.ball_radius, 
                      event.x()))
            new_y = max(self.border_width + self.ball_radius, 
                      min(self.height() - self.border_width - self.ball_radius, 
                      event.y()))
            
            self.ball_pos = QPoint(new_x, new_y)
            
            # 计算并发出标准化坐标信号
            norm_x = (self.ball_pos.x() - self.border_width - self.ball_radius) / (self.width() - 2*(self.border_width + self.ball_radius))
            norm_y = (self.ball_pos.y() - self.border_width - self.ball_radius) / (self.height() - 2*(self.border_width + self.ball_radius))
            self.position_text = f"X: {norm_x:.2f}, Y: {norm_y:.2f}"
            self.positionChanged.emit(norm_x, norm_y)
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            self.update()
    
    def resizeEvent(self, event):
        # 当控件大小改变时，更新小球位置保持比例
        norm_x = (self.ball_pos.x() - self.border_width - self.ball_radius) / max(1, self.width() - 2*(self.border_width + self.ball_radius))
        norm_y = (self.ball_pos.y() - self.border_width - self.ball_radius) / max(1, self.height() - 2*(self.border_width + self.ball_radius))
        
        self.ball_pos = QPoint(
            int(self.border_width + self.ball_radius + norm_x * (self.width() - 2*(self.border_width + self.ball_radius))),
            int(self.border_width + self.ball_radius + norm_y * (self.height() - 2*(self.border_width + self.ball_radius)))
        )
        self.update()

class PositionControlPanel(QWidget):
    """包含小球控件和位置信息的控制面板"""
    
    def __init__(self, size=400):
        super().__init__()
        self.setWindowTitle("可拖动小球位置控件")
        self.setGeometry(300, 300, 500, 600)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("方框内拖动小球控件")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # 信息面板
        info_group = QGroupBox("位置信息")
        info_layout = QVBoxLayout()
        self.pos_label = QLabel("当前位置: X: 0.50, Y: 0.50")
        self.pos_label.setStyleSheet("font-size: 14px;")
        self.raw_pos_label = QLabel("绝对坐标: (0, 0)")
        self.raw_pos_label.setStyleSheet("color: gray; font-size: 12px;")
        
        info_layout.addWidget(self.pos_label)
        info_layout.addWidget(self.raw_pos_label)
        info_group.setLayout(info_layout)
        
        # 创建小球控件
        self.ball_widget = DraggableBallWidget(size)
        self.ball_widget.positionChanged.connect(self.update_position_info)
        
        # 设置小球初始位置在左下角
        self.ball_widget.ball_pos = QPoint(
            self.ball_widget.border_width + self.ball_widget.ball_radius,
            self.ball_widget.height() - self.ball_widget.border_width - self.ball_widget.ball_radius
        )
        
        # 添加说明文字
        instruction = QLabel("← 拖动红色小球到任意位置")
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #555555; font-style: italic;")
        
        # 添加控件到布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(info_group)
        main_layout.addWidget(self.ball_widget)
        main_layout.addWidget(instruction)
        
        self.setLayout(main_layout)
    
    def update_position_info(self, x, y):
        """更新位置信息显示"""
        # 更新坐标标签
        self.pos_label.setText(f"当前位置: X: {x:.2f}, Y: {y:.2f}")
        
        # 计算并显示绝对坐标
        abs_x = self.ball_widget.ball_pos.x()
        abs_y = self.ball_widget.ball_pos.y()
        self.raw_pos_label.setText(f"绝对坐标: ({abs_x}, {abs_y})")
        
        # 简单的位置状态信息
        if x < 0.2 or x > 0.8 or y < 0.2 or y > 0.8:
            self.raw_pos_label.setStyleSheet("color: #FF5500; font-size: 12px;")
        elif abs(x - 0.5) < 0.2 and abs(y - 0.5) < 0.2:
            self.raw_pos_label.setStyleSheet("color: #008800; font-size: 12px;")
        else:
            self.raw_pos_label.setStyleSheet("color: gray; font-size: 12px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    app.setStyleSheet("""
        QWidget {
            background-color: #f5f5f5;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QGroupBox {
            border: 1px solid #d0d0d0;
            border-radius: 5px;
            margin-top: 1ex;
            padding: 10px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px;
            color: #404040;
        }
        QLabel {
            padding: 5px;
        }
    """)
    
    window = PositionControlPanel(400)
    window.show()
    sys.exit(app.exec_())