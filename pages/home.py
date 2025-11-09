import sys
import time
import os
from PyQt5.QtCore import Qt, QEasingCurve
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
)

from PyQt5.QtGui import QIcon, QImage

import gas.util.hwnd_util as hwnd_util
import gas.util.screenshot_util as screenshot_util
import gas.util.img_util as img_util
import gas.util.file_util as file_util

import win32gui


from qfluentwidgets import (
    PushButton,
    LineEdit,
    BodyLabel,
    FlowLayout,
    GroupHeaderCardWidget,
    ComboBox,
    SearchLineEdit,
    PrimaryPushButton,
    IconWidget,
    InfoBarIcon,
    FluentIcon,
    CardWidget,
    ImageLabel,
    MSFluentTitleBar,
    ListWidget,
    isDarkTheme,
    SingleDirectionScrollArea,
    SmoothMode,
    SmoothScrollArea,
)
import qfluentwidgets


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class HomeWidget(QWidget):
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
        qfluentwidgets.BodyLabel()
        hintIcon = IconWidget(InfoBarIcon.INFORMATION)
        hintLabel = BodyLabel("点击编译按钮以开始打包 👉")
        compileButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, "编译")
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
            None,
            "构建目录",
            "选择 Nuitka 的输出目录",
            chooseButton,
        )
        settingGroupCard.addGroup(None, "运行终端", "设置是否显示命令行终端", comboBox)
        group = settingGroupCard.addGroup(
            None, "入口脚本", "选择软件的入口脚本", lineEdit
        )
        group.setSeparatorVisible(True)

        # 添加底部工具栏
        settingGroupCard.vBoxLayout.addLayout(bottomLayout)

        layout = QVBoxLayout(self)
        layout.addWidget(settingGroupCard)

    def open(self):
        print("open")
        i = ImageCardWidget(self)
        i.show()


class MicaWindow(Window):

    def __init__(self):
        super().__init__()
        self.setTitleBar(MSFluentTitleBar(self))
        if isWin11():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())


class ImageCardWidget(MicaWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.imageLabel = ImageLabel("resource/shoko1.jpg")
        self.gifLabel = ImageLabel("resource/shoko2.jpg")
        self.vBoxLayout = QVBoxLayout(self)
        self.setWindowTitle("image")

        self.vBoxLayout.setContentsMargins(10, 50, 10, 10)

        # 竖直方向有很多组件
        view = QWidget()
        self.layout = QVBoxLayout(view)

        self.layout.addWidget(self.imageLabel)
        self.layout.addWidget(self.gifLabel)

        scrollArea = SmoothScrollArea(self)
        scrollArea.setWidget(view)
        scrollArea.setScrollAnimation(Qt.Vertical, 400, QEasingCurve.OutQuint)
        scrollArea.setScrollAnimation(Qt.Horizontal, 400, QEasingCurve.OutQuint)
        
        scrollArea.resize(1200, 800)

        btn = PrimaryPushButton("截图")
        btn.clicked.connect(self.capture)

        self.vBoxLayout.addWidget(scrollArea)
        self.vBoxLayout.addWidget(btn)

    def capture(self):
        print("1111")
        screenshot = screenshot_util.screenshot_bitblt(
            win32gui.GetDesktopWindow(), [500, 500, 700, 700]
        )
        f = f"{int(time.time())}.png"
        img_util.save_img(screenshot, f)
        label = ImageLabel(f)
        self.layout.addWidget(label)
        os.remove(f)
