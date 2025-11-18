"""主页组件"""

import os
import time
from typing import TYPE_CHECKING

import win32gui
from PyQt5.QtCore import Qt, QEasingCurve, QSize, QRectF
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QDialog, QLabel
from PyQt5.QtGui import QPainter, QPainterPath, QLinearGradient, QColor, QBrush

from gas.util.hwnd_util import get_hwnd_by_class_and_title, WindowInfo, get_window_wh
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
    LineEdit,
    InfoBar,
)

from src.erchong.config.settings import RESOURCE_DIR
from src.erchong.utils.platform import is_win11
from src.erchong.widgets.image_card_widget import ImageCardWidget
from src.erchong.widgets.hwnd_list_widget import HwndListWidget
from src.erchong.common.style_sheet import StyleSheet
from src.erchong.common.config import cfg


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

        self.find_hwnd_btn = PrimaryPushButton("运行")
        self.find_hwnd_btn.setFixedWidth(100)
        self.set_group_card.addGroup(
            icon=FluentIcon.ERASE_TOOL,
            title="句柄管理",
            content="用于获取句柄.测试截取等功能",
            widget=self.find_hwnd_btn,
        )

        self.capture_btn = PrimaryPushButton("运行")
        self.capture_btn.setFixedWidth(100)
        self.set_group_card.addGroup(
            icon=FluentIcon.ERASE_TOOL,
            title="捕获窗口",
            content="根据下面的窗口标题与类名,捕获窗口",
            widget=self.capture_btn,
        )

        self.hwnd_title_edit = LineEdit()
        self.hwnd_title_edit.setText(cfg.get(cfg.hwndWindowsTitle))
        self.hwnd_title_edit.setFixedWidth(300)
        self.set_group_card.addGroup(
            icon=FluentIcon.FONT, title="窗口标题", content="用于获取句柄的窗口标题", widget=self.hwnd_title_edit
        )

        self.hwnd_classname_edit = LineEdit()
        self.hwnd_classname_edit.setText(cfg.get(cfg.hwndClassname))
        self.hwnd_classname_edit.setFixedWidth(300)
        self.set_group_card.addGroup(
            icon=FluentIcon.DICTIONARY,
            title="窗口类名",
            content="用于获取句柄的窗口类名",
            widget=self.hwnd_classname_edit,
        )

        self.run_group_card = GroupHeaderCardWidget()
        self.run_group_card.setTitle("执行脚本")
        self.run_group_card.setBorderRadius(8)

        self.run_btn = PrimaryPushButton("开始")
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
        self.find_hwnd_btn.clicked.connect(self.openHwnd)
        self.hwnd_title_edit.textChanged.connect(lambda: cfg.set(cfg.hwndWindowsTitle, self.hwnd_title_edit.text()))
        self.hwnd_classname_edit.textChanged.connect(
            lambda: cfg.set(cfg.hwndClassname, self.hwnd_classname_edit.text())
        )
        self.capture_btn.clicked.connect(self._capture)

    def udpate_cfg(self):
        self.hwnd_classname_edit.setText(cfg.get(cfg.hwndClassname))
        self.hwnd_title_edit.setText(cfg.get(cfg.hwndWindowsTitle))

    def openHwnd(self):
        widget = HwndListWidget()
        widget.show()
        widget.cfgUpdated.connect(self.udpate_cfg)

    def _capture(self):
        hwnd_list = get_hwnd_by_class_and_title(
            class_name=cfg.get(cfg.hwndClassname),
            titles=cfg.get(cfg.hwndWindowsTitle),
        )
        if hwnd_list is None or len(hwnd_list) == 0:
            InfoBar.warning(title="警告", content="未能找到对应窗口句柄", parent=self, duration=3000)
            return

        hwnd = hwnd_list[0]
        win = WindowInfo(
            hwnd=hwnd,
            size=get_window_wh(hwnd),
            title=win32gui.GetWindowText(hwnd),
            class_name=win32gui.GetClassName(hwnd),
            position=[0, 0],
        )
        widget = ImageCardWidget(windows=win)
        widget.show()
