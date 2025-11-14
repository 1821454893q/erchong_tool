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

import qframelesswindow as qfw
import qfluentwidgets as qf
from ..config.settings import RESOURCE_DIR
from ..utils.platform import is_win11
from .image_card_widget import ImageCardWidget
from .hwnd_list_widget import HwndListWidget

if TYPE_CHECKING:
    from qframelesswindow import AcrylicWindow, FramelessWindow

    Window = AcrylicWindow  # type: ignore
else:
    if is_win11():
        from qframelesswindow import AcrylicWindow as Window
    else:
        from qframelesswindow import FramelessWindow as Window


class HomeWidget(QWidget):
    """主页组件"""

    def __init__(self, objectName: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(objectName)
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        settingGroupCard = GroupHeaderCardWidget()
        settingGroupCard.setTitle("基本设置")
        settingGroupCard.setBorderRadius(8)

        chooseButton = PushButton("选择")
        comboBox = ComboBox()
        lineEdit = SearchLineEdit()
        hintIcon = IconWidget(InfoBarIcon.INFORMATION)
        hintLabel = BodyLabel("点击编译按钮以开始打包 👉")
        compileButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, "编译")
        compileButton.clicked.connect(self.openHwnd)
        openButton = PushButton(FluentIcon.VIEW, "打开")
        openButton.clicked.connect(self.open)
        bottomLayout = QHBoxLayout()

        chooseButton.setFixedWidth(120)
        lineEdit.setFixedWidth(320)
        comboBox.setFixedWidth(320)
        comboBox.addItems(["始终显示（首次打包时建议启用）", "始终隐藏"])
        lineEdit.setPlaceholderText("输入入口脚本的路径")

        # 设置底部工具栏布局
        hintIcon.setFixedSize(16, 16)
        bottomLayout.setSpacing(10)
        bottomLayout.setContentsMargins(24, 15, 24, 20)
        bottomLayout.addWidget(hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        bottomLayout.addWidget(hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        bottomLayout.addStretch(1)
        bottomLayout.addWidget(openButton, 0, Qt.AlignmentFlag.AlignRight)
        bottomLayout.addWidget(compileButton, 0, Qt.AlignmentFlag.AlignRight)
        bottomLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 添加组件到分组中
        settingGroupCard.addGroup(
            "",
            "构建目录",
            "选择 Nuitka 的输出目录",
            chooseButton,
        )
        settingGroupCard.addGroup("", "运行终端", "设置是否显示命令行终端", comboBox)
        group = settingGroupCard.addGroup("", "入口脚本", "选择软件的入口脚本", lineEdit)
        group.setSeparatorVisible(True)

        # 添加底部工具栏
        settingGroupCard.vBoxLayout.addLayout(bottomLayout)

        layout = QVBoxLayout(self)
        layout.addWidget(settingGroupCard)

    def open(self):
        """打开图片卡片窗口"""
        widget = ImageCardWidget(self)
        widget.show()

    def openHwnd(self):
        widget = HwndListWidget()
        widget.show()
