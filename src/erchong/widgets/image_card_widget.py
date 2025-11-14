"""图片卡片组件"""

import os
import time
from typing import (
    TYPE_CHECKING,
)
from src.erchong.common.config import (
    cfg,
)

import win32gui
from PyQt5.QtCore import (
    Qt,
    QEasingCurve,
)
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

import gas.util.img_util as img_util
import gas.util.screenshot_util as screenshot_util
from qfluentwidgets import (
    ImageLabel,
    MSFluentTitleBar,
    PrimaryPushButton,
    SmoothScrollArea,
    ScrollArea,
    isDarkTheme,
)

from ..config.settings import (
    QT_QSS_DIR,
    RESOURCE_DIR,
)
from ..utils.platform import (
    is_win11,
)

if TYPE_CHECKING:
    from qframelesswindow import (
        AcrylicWindow,
        FramelessWindow,
    )

    Window = AcrylicWindow  # type: ignore
else:
    if is_win11():
        from qframelesswindow import (
            AcrylicWindow as Window,
        )
    else:
        from qframelesswindow import (
            FramelessWindow as Window,
        )

from ..utils.logger import (
    get_logger,
)

log = get_logger()


class MicaWindow(Window):
    """Mica 效果窗口基类"""

    def __init__(
        self,
    ):
        super().__init__()
        self.setTitleBar(MSFluentTitleBar(self))
        if is_win11():
            self.windowEffect.setMicaEffect(
                self.winId(),
                isDarkTheme(),
            )


class ImageCardWidget(MicaWindow):
    """图片卡片窗口"""

    def __init__(
        self,
        parent=None,
    ):
        super().__init__()

        self.imageLabel = ImageLabel(
            str(RESOURCE_DIR / "shoko1.jpg"),
            self,
        )
        self.gifLabel = ImageLabel(
            str(RESOURCE_DIR / "shoko2.jpg"),
            self,
        )
        self.vBoxLayout = QVBoxLayout(self)
        self.setWindowTitle("image")

        self.vBoxLayout.setContentsMargins(
            10,
            30,
            10,
            10,
        )

        # 竖直方向有很多组件
        view = QWidget()
        self.viewLayout = QVBoxLayout(view)

        self.viewLayout.addWidget(self.imageLabel)
        self.viewLayout.addWidget(self.gifLabel)

        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidget(view)
        self.scrollArea.resize(
            1200,
            800,
        )

        btn = PrimaryPushButton("截图")
        btn.clicked.connect(self.capture)

        self.vBoxLayout.addWidget(self.scrollArea)
        self.vBoxLayout.addWidget(btn)
        # 设置样式
        cfg.themeChanged.connect(self.setQss)

    def setQss(
        self,
    ):
        self.setStyleSheet(cfg.getQssFile("image_card_widget"))

    def capture(
        self,
    ):
        """截图功能"""
        screenshot = screenshot_util.screenshot_bitblt(
            win32gui.GetDesktopWindow(),
            (
                500,
                500,
                700,
                700,
            ),
        )
        f = f"{int(time.time())}.png"
        img_util.save_img(
            screenshot,
            f,
        )
        label = ImageLabel(f)
        self.viewLayout.addWidget(label)
        os.remove(f)
