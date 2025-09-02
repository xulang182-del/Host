import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QDial, QLabel, QGroupBox, QPushButton, QSlider, 
                             QHBoxLayout, QCheckBox)
from PyQt5.QtCore import Qt, QPoint, QRectF, QPropertyAnimation, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QConicalGradient

class FixedDial(QDial):
    """修复版Dial控件，确保所有位置可拖动"""
    def __init__(self, size=200, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        
        # 配置固定范围和初始值
        self.setRange(0, 360)  # 使用360度范围更直观
        self.setValue(0)
        
        # 优化设置确保所有位置可达
        self.setNotchesVisible(True)
        self.setWrapping(True)  # 启用循环模式
        self.setSingleStep(1)   # 最小步长为1度
        self.setPageStep(30)    # 翻页步长为30度
        self.setTracking(True)  # 确保实时跟踪位置

    def paintEvent(self, event):
        """自定义绘制方法提供更好的视觉反馈"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        size = min(self.width(), self.height())
        radius = size // 2 - 15
        
        # 绘制外环
        outer_rect = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )
        
        # 创建渐变效果
        gradient = QConicalGradient(center, -self.value())
        gradient.setColorAt(0.0, QColor(100, 150, 200, 220))
        gradient.setColorAt(0.5, QColor(255, 140, 50, 240))
        gradient.setColorAt(1.0, QColor(100, 150, 200, 220))
        
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.setBrush(gradient)
        painter.drawEllipse(outer_rect)
        
        # 绘制内环
        inner_radius = radius - 20
        inner_rect = QRectF(
            center.x() - inner_radius,
            center.y() - inner_radius,
            inner_radius * 2,
            inner_radius * 2
        )
        
        painter.setPen(QPen(QColor(70, 70, 70), 2))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(inner_rect)
        
        # 绘制手柄
        handle_radius = 12
        angle = self.value() * 16  # QDial角度值（每度16个单位）
        handle_x = center.x() + radius * 0.8 * math.cos(math.radians(self.value()))
        handle_y = center.y() - radius * 0.8 * math.sin(math.radians(self.value()))
        
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        painter.setBrush(QBrush(QColor(230, 80, 60)))
        painter.drawEllipse(QPointF(handle_x, handle_y), handle_radius, handle_radius)
        
        # 绘制指示线和指针
        painter.setPen(QPen(QColor(30, 30, 30), 3))
        painter.drawLine(center, QPointF(handle_x, handle_y))
        
        # 绘制中心点
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(center, 5, 5)
        
        # 绘制刻度
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        for i in range(0, 360, 30):
            angle_rad = math.radians(i)
            x1 = center.x() + (radius - 5) * math.cos(angle_rad)
            y1 = center.y() - (radius - 5) * math.sin(angle_rad)
            x2 = center.x() + radius * math.cos(angle_rad)
            y2 = center.y() - radius * math.sin(angle_rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            # 添加刻度标签
            if i % 90 == 0:
                x = center.x() + (radius - 25) * math.cos(angle_rad)
                y = center.y() - (radius - 25) * math.sin(angle_rad)
                painter.setFont(QFont("Arial", 10, QFont.Bold))
                painter.drawText(QPointF(x - 10, y + 4), f"{i}°")

class DialFixDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dial 位置修复演示")
        self.setGeometry(300, 300, 600, 600)
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("Dial 所有位置可达性修复")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding: 15px; background: #eef5ff; border-radius: 10px;")
        
        # 创建修复版Dial控件
        dial_size = 280
        self.dial = FixedDial(dial_size)
        
        # 原始Dial控件（用于对比）
        self.original_dial = self.create_original_dial()
        
        # 值显示
        self.value_label = QLabel("当前值: 0°")
        self.value_label.setFont(QFont("Arial", 16))
        self.value_label.setStyleSheet("""
            background: #f0f8ff; 
            padding: 12px; 
            border-radius: 8px;
            border: 1px solid #3498db;
        """)
        
        # 角度指示器
        self.angle_indicator = QLabel()
        self.angle_indicator.setFixedSize(60, 60)
        self.update_angle_indicator(0)
        
        # 参数控制面板
        control_group = QGroupBox("控制参数")
        control_layout = QVBoxLayout()
        
        # 最小值设置
        min_layout = QHBoxLayout()
        min_label = QLabel("最小值:")
        min_label.setFixedWidth(80)
        self.min_slider = QSlider(Qt.Horizontal)
        self.min_slider.setRange(0, 360)
        self.min_slider.setValue(0)
        self.min_slider.valueChanged.connect(self.update_min)
        min_layout.addWidget(min_label)
        min_layout.addWidget(self.min_slider)
        
        # 最大值设置
        max_layout = QHBoxLayout()
        max_label = QLabel("最大值:")
        max_label.setFixedWidth(80)
        self.max_slider = QSlider(Qt.Horizontal)
        self.max_slider.setRange(10, 360)
        self.max_slider.setValue(360)
        self.max_slider.valueChanged.connect(self.update_max)
        max_layout.addWidget(max_label)
        max_layout.addWidget(self.max_slider)
        
        # 步长设置
        step_layout = QHBoxLayout()
        step_label = QLabel("步长:")
        step_label.setFixedWidth(80)
        self.step_slider = QSlider(Qt.Horizontal)
        self.step_slider.setRange(1, 30)
        self.step_slider.setValue(1)
        self.step_slider.valueChanged.connect(self.update_step)
        step_layout.addWidget(step_label)
        step_layout.addWidget(self.step_slider)
        
        # 高级选项
        self.wrapping_check = QCheckBox("启用循环 (Wrapping)")
        self.wrapping_check.setChecked(True)
        self.wrapping_check.stateChanged.connect(self.update_wrapping)
        
        self.notch_check = QCheckBox("显示刻度 (Notches)")
        self.notch_check.setChecked(True)
        self.notch_check.stateChanged.connect(self.update_notches)
        
        # 添加到控制布局
        control_layout.addLayout(min_layout)
        control_layout.addLayout(max_layout)
        control_layout.addLayout(step_layout)
        control_layout.addWidget(self.wrapping_check)
        control_layout.addWidget(self.notch_check)
        control_group.setLayout(control_layout)
        
        # 测试按钮
        btn_layout = QHBoxLayout()
        
        test_positions = [0, 90, 180, 270, 360]
        for pos in test_positions:
            btn = QPushButton(f"{pos}°")
            btn.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
            btn.clicked.connect(lambda checked, pos=pos: self.set_dial_position(pos))
            btn_layout.addWidget(btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        reset_btn.clicked.connect(self.reset_dial)
        btn_layout.addWidget(reset_btn)
        
        # 显示区域布局
        display_layout = QHBoxLayout()
        dial_group = self.create_dial_group("修复版Dial", self.dial)
        original_dial_group = self.create_dial_group("原始QDial", self.original_dial)
        
        display_layout.addWidget(dial_group)
        display_layout.addWidget(original_dial_group)
        
        # 添加到主布局
        main_layout.addWidget(title_label)
        main_layout.addLayout(display_layout)
        main_layout.addWidget(self.value_label, alignment=Qt.AlignCenter)
        
        # 角度指示器布局
        indicator_layout = QHBoxLayout()
        indicator_layout.addStretch()
        indicator_layout.addWidget(self.angle_indicator)
        indicator_layout.addStretch()
        
        main_layout.addLayout(indicator_layout)
        main_layout.addWidget(control_group)
        main_layout.addLayout(btn_layout)
        
        # 连接信号
        self.dial.valueChanged.connect(self.update_value)
        self.original_dial.valueChanged.connect(self.update_value)
    
    def create_dial_group(self, title, dial):
        """创建包含Dial的分组"""
        group = QGroupBox(title)
        layout = QVBoxLayout()
        
        layout.addWidget(dial, alignment=Qt.AlignCenter)
        group.setLayout(layout)
        
        group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #dce4ec;
                border-radius: 10px;
                margin: 5px;
                padding: 15px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background: white;
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        return group
    
    def create_original_dial(self):
        """创建原始QDial用于对比"""
        dial = QDial()
        dial.setFixedSize(250, 250)
        dial.setRange(0, 360)
        dial.setValue(0)
        dial.setNotchesVisible(True)
        dial.setWrapping(True)
        return dial
    
    def update_value(self, value):
        """更新值显示"""
        self.value_label.setText(f"当前值: {value}°")
        self.update_angle_indicator(value)
        
        # 根据位置设置背景色
        r = min(255, int(value * 255 / 360))
        g = 100
        b = max(50, int(255 - value * 255 / 360))
        
        self.value_label.setStyleSheet(f"""
            background: rgb({r}, {g}, {b}, 220); 
            color: {"white" if value > 200 else "black"};
            padding: 12px; 
            border-radius: 8px;
            border: 1px solid #3498db;
            font-weight: bold;
        """)
    
    def update_angle_indicator(self, angle):
        """更新角度指示器"""
        size = 60
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = QPoint(size//2, size//2)
        radius = size//2 - 5
        
        # 绘制外部圆弧
        painter.setPen(QPen(QColor(100, 100, 200), 3))
        painter.drawArc(5, 5, size-10, size-10, 0, 360 * 16)
        
        # 绘制内部指示线
        painter.setPen(QPen(QColor(230, 80, 60), 2))
        rad = math.radians(angle)
        x = center.x() + (radius - 5) * math.cos(rad)
        y = center.y() - (radius - 5) * math.sin(rad)
        painter.drawLine(center.x(), center.y(), int(x), int(y))
        
        # 绘制中心点
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(center, 3, 3)
        
        # 绘制角度值
        painter.setPen(Qt.black)
        painter.setFont(QFont("Arial", 8))
        painter.drawText(0, 0, size, size, Qt.AlignCenter, f"{angle}°")
        
        painter.end()
        
        self.angle_indicator.setPixmap(pixmap)
    
    def update_min(self, value):
        """更新最小值"""
        if value >= self.dial.maximum():
            self.max_slider.setValue(value + 10)
            return
            
        self.dial.setMinimum(value)
        self.original_dial.setMinimum(value)
    
    def update_max(self, value):
        """更新最大值"""
        if value <= self.dial.minimum():
            self.min_slider.setValue(value - 10)
            return
            
        self.dial.setMaximum(value)
        self.original_dial.setMaximum(value)
    
    def update_step(self, value):
        """更新步长"""
        self.dial.setSingleStep(value)
        self.dial.setPageStep(value * 10)
        self.original_dial.setSingleStep(value)
        self.original_dial.setPageStep(value * 10)
    
    def update_wrapping(self, state):
        """更新循环模式"""
        wrap = state == Qt.Checked
        self.dial.setWrapping(wrap)
        self.original_dial.setWrapping(wrap)
    
    def update_notches(self, state):
        """更新刻度显示"""
        show = state == Qt.Checked
        self.dial.setNotchesVisible(show)
        self.original_dial.setNotchesVisible(show)
    
    def set_dial_position(self, angle):
        """设置Dial到指定角度"""
        # 添加动画效果
        anim = QPropertyAnimation(self.dial, b"value")
        anim.setDuration(800)
        anim.setStartValue(self.dial.value())
        anim.setEndValue(angle)
        anim.setEasingCurve(QEasingCurve.OutElastic)
        anim.start()
        
        # 同时设置原始Dial（无动画）
        self.original_dial.setValue(angle)
    
    def reset_dial(self):
        """重置Dial状态"""
        self.set_dial_position(0)
        self.min_slider.setValue(0)
        self.max_slider.setValue(360)
        self.step_slider.setValue(1)
        self.wrapping_check.setChecked(True)
        self.notch_check.setChecked(True)

if __name__ == "__main__":
    import math
    from PyQt5.QtGui import QPixmap, QRadialGradient
    
    app = QApplication(sys.argv)
    
    # 设置全局样式
    app.setStyleSheet("""
        QWidget {
            background-color: #f5f7fa;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }
        QGroupBox {
            border: 1px solid #dce4ec;
            border-radius: 8px;
            margin: 8px 0;
            padding: 10px 15px;
            background-color: white;
        }
        QSlider::groove:horizontal {
            height: 8px;
            background: #d0d0d0;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: #3498db;
            border: 1px solid #2980b9;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        QSlider::sub-page:horizontal {
            background: #3498db;
            border-radius: 4px;
        }
    """)
    
    window = DialFixDemo()
    window.show()
    sys.exit(app.exec_())