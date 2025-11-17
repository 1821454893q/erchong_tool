"""主页组件"""

import os
import time
from typing import TYPE_CHECKING

import win32gui
from PyQt5.QtCore import Qt, QEasingCurve, QSize, QRectF
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QDialog, QLabel
from PyQt5.QtGui import QPainter, QPainterPath, QLinearGradient, QColor, QBrush

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
    SingleDirectionScrollArea,
)

from src.erchong.config.settings import RESOURCE_DIR
from src.erchong.utils.platform import is_win11
from src.erchong.widgets.image_card_widget import ImageCardWidget
from src.erchong.widgets.hwnd_list_widget import HwndListWidget
from src.erchong.common.style_sheet import StyleSheet


class HomeWidget(SingleDirectionScrollArea):
    """主页组件"""

    def __init__(self, objectName: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(objectName)
        self._setup_ui()
        self._set_connections()

        StyleSheet.HOME_WIDGET.apply(self)

    def _setup_ui(self):
        """设置界面 - 直接继承滚动区域版本"""

        # 设置滚动区域属性
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        # 创建内容窗口
        content_widget = QWidget()
        content_widget.setObjectName("sourceWidget")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)

        # 创建各种组件
        self.set_group_card = GroupHeaderCardWidget()
        self.set_group_card.setTitle("基本设置")
        self.set_group_card.setBorderRadius(8)

        self.capture_btn = PrimaryPushButton("测试")
        self.set_group_card.addGroup(
            icon=FluentIcon.ERASE_TOOL, title="测试截图", content="用于测试截图功能是否正常", widget=self.capture_btn
        )

        self.run_group_card = GroupHeaderCardWidget()
        self.run_group_card.setTitle("执行脚本")
        self.run_group_card.setBorderRadius(8)

        self.run_btn = PrimaryPushButton("开始")
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)
        self.run_group_card.addGroup(icon=FluentIcon.ERASE_TOOL, title="脚本1", content="测试开发", widget=self.run_btn)

        self.detail_label = BodyLabel("开发者: jian 邮箱: 不说了")

        # 将组件添加到内容布局
        self.content_layout.addWidget(self.set_group_card)
        self.content_layout.addWidget(self.run_group_card)
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.detail_label)

        # 设置内容窗口
        self.setWidget(content_widget)

    def _set_connections(self):
        self.capture_btn.clicked.connect(self.openHwnd)

    def openHwnd(self):
        widget = HwndListWidget()
        widget.show()
