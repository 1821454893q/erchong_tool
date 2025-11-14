"""主页组件"""

import os
import time
from typing import TYPE_CHECKING

import win32gui
from PyQt5.QtCore import Qt, QEasingCurve, QSize
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QDialog, QLabel

import gas.util.img_util as img_util
import gas.util.screenshot_util as screenshot_util
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    FluentIcon,
    GroupHeaderCardWidget,
    IconWidget,
    ImageLabel,
    InfoBarIcon,
    MSFluentTitleBar,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    SmoothScrollArea,
    isDarkTheme,
)

from src.erchong.config.settings import RESOURCE_DIR
from src.erchong.utils.platform import is_win11
from src.erchong.widgets.image_card_widget import ImageCardWidget
from src.erchong.widgets.hwnd_list_widget import HwndListWidget


class HomeWidget(QWidget):
    """主页组件"""

    def __init__(self, objectName: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(objectName)
        self._setup_ui()
        self._set_connections()

    def _setup_ui(self):
        """设置界面"""
        self.main_layout = QVBoxLayout(self)

        self.set_group_card = GroupHeaderCardWidget()
        self.set_group_card.setTitle("基本设置")
        self.set_group_card.setBorderRadius(8)

        self.capture_btn = PrimaryPushButton("测试")
        self.set_group_card.addGroup(
            icon=FluentIcon.ERASE_TOOL, title="测试截图", content="用于测试截图功能是否正常", widget=self.capture_btn
        )

        self.detail_label = BodyLabel("开发者: jian 邮箱: 不说了")

        self.main_layout.addWidget(self.set_group_card)
        self.main_layout.addStretch(1)
        # self.main_layout.addWidget(self.detail_label)
        self.setLayout(self.main_layout)

    def _set_connections(self):
        self.capture_btn.clicked.connect(self.openHwnd)

    def openHwnd(self):
        widget = HwndListWidget()
        widget.show()
