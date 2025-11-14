"""设置页面组件"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    SubtitleLabel,
    setFont,
    PushButton,
    ComboBox,
    InfoBarIcon,
    SearchLineEdit,
    IconWidget,
    InfoBarIcon,
    BodyLabel,
    PrimaryPushButton,
    FluentIcon,
    GroupHeaderCardWidget,
)


class SettingsWidget(GroupHeaderCardWidget):
    """设置页面组件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName(text)
        self.setTitle("基本设置")
        self.setBorderRadius(8)
        self.vBoxLayout = QVBoxLayout()

        self.chooseButton = PushButton("选择")
        self.comboBox = ComboBox()
        self.lineEdit = SearchLineEdit()

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION)
        self.hintLabel = BodyLabel("点击编译按钮以开始打包 👉")
        self.compileButton = PrimaryPushButton(FluentIcon.PLAY_SOLID, "编译")
        self.openButton = PushButton(FluentIcon.VIEW, "打开")
        self.bottomLayout = QHBoxLayout()

        self.chooseButton.setFixedWidth(120)
        self.lineEdit.setFixedWidth(320)
        self.comboBox.setFixedWidth(320)
        self.comboBox.addItems(["始终显示（首次打包时建议启用）", "始终隐藏"])
        self.lineEdit.setPlaceholderText("输入入口脚本的路径")

        # 设置底部工具栏布局
        self.hintIcon.setFixedSize(16, 16)
        self.bottomLayout.setSpacing(10)
        self.bottomLayout.setContentsMargins(24, 15, 24, 20)
        self.bottomLayout.addWidget(self.hintIcon, 0, Qt.AlignLeft)
        self.bottomLayout.addWidget(self.hintLabel, 0, Qt.AlignLeft)
        self.bottomLayout.addStretch(1)
        self.bottomLayout.addWidget(self.openButton, 0, Qt.AlignRight)
        self.bottomLayout.addWidget(self.compileButton, 0, Qt.AlignRight)
        self.bottomLayout.setAlignment(Qt.AlignVCenter)

        # 添加组件到分组中
        self.addGroup("resource/Rocket.svg", "构建目录", "选择 Nuitka 的输出目录", self.chooseButton)
        self.addGroup("resource/Joystick.svg", "运行终端", "设置是否显示命令行终端", self.comboBox)
        group = self.addGroup("resource/Python.svg", "入口脚本", "选择软件的入口脚本", self.lineEdit)
        group.setSeparatorVisible(True)

        # 添加底部工具栏
        self.vBoxLayout.addLayout(self.bottomLayout)
        self.setLayout(self.vBoxLayout)
