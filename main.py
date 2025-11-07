import sys

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices, QColor
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import (
    NavigationItemPosition,
    MessageBox,
    setTheme,
    Theme,
    MSFluentWindow,
    NavigationAvatarWidget,
    qrouter,
    SubtitleLabel,
    setFont,
    isDarkTheme,
)
from qfluentwidgets import FluentIcon as FIF

from pages.home import HomeWidget


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(" ", "-"))


class Window(MSFluentWindow):

    def __init__(self):
        super().__init__()

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        # create sub interface
        self.homeInterface = HomeWidget("Home Interface", self)
        self.SettingInterface = Widget("Setting Interface", self)

        self.addSubInterface(self.homeInterface, FIF.HOME, "主页", FIF.HOME_FILL)

        self.navigationInterface.addItem(
            routeKey="theme",
            icon=FIF.BRIGHTNESS,
            text="主题",
            onClick=self.switchTheme,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(
            self.SettingInterface,
            FIF.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(800, 600)
        self.setWindowIcon(QIcon(":/qfluentwidgets/images/logo.png"))
        self.setWindowTitle("工具")

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def switchTheme(self):
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)


if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    app.exec_()
