"""主窗口"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QScreen
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import (
    MSFluentWindow,
    NavigationItemPosition,
    isDarkTheme,
    setTheme,
    Theme,
)
from qfluentwidgets import FluentIcon as FIF

from ..config.settings import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from ..widgets import GalleryCard, HomeWidget, SettingsWidget


class MainWindow(MSFluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        """初始化导航"""
        # 创建子界面
        self.homeInterface = HomeWidget("Home Interface", self)
        self.settingsInterface = SettingsWidget("Setting Interface", self)

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
            self.settingsInterface,
            FIF.SETTING,
            "设置",
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        """初始化窗口"""
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowIcon(QIcon(":/qfluentwidgets/images/logo.png"))
        self.setWindowTitle(WINDOW_TITLE)

        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            w, h = geometry.width(), geometry.height()
            self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def switchTheme(self):
        """切换主题"""
        if isDarkTheme():
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)

