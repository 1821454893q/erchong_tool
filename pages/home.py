import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QTextEdit,
)
from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    LineEdit,
    CheckBox,
    setThemeColor,
)


class HomeWidget(QFrame):
    def __init__(self, objectName: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(objectName)
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        # 主布局
        main_layout = QVBoxLayout(self)

        # 第一行
        one_layout = QVBoxLayout(self)
        one_layout.setAlignment()

        label = QLabel("窗口名称")
        one_layout.addWidget(label)

        text_edit = QTextEdit()
        one_layout.addWidget(text_edit)

        main_layout.addLayout(one_layout)

        # 第二行
        two_layout = QVBoxLayout(self)

        button = PushButton("测试截图")
        two_layout.addWidget(button)

        main_layout.addLayout(two_layout)
