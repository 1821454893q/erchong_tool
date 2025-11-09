import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QPoint, QSize, QUrl, QRect, QPropertyAnimation
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGraphicsOpacityEffect,
)

from qfluentwidgets import (
    CardWidget,
    setTheme,
    Theme,
    IconWidget,
    BodyLabel,
    CaptionLabel,
    PushButton,
    TransparentToolButton,
    FluentIcon,
    RoundMenu,
    Action,
    ElevatedCardWidget,
    ImageLabel,
    isDarkTheme,
    FlowLayout,
    MSFluentTitleBar,
    SimpleCardWidget,
    HeaderCardWidget,
    InfoBarIcon,
    HyperlinkLabel,
    HorizontalFlipView,
    PrimaryPushButton,
    TitleLabel,
    PillPushButton,
    setFont,
    ScrollArea,
    VerticalSeparator,
    MSFluentWindow,
    NavigationItemPosition,
    GroupHeaderCardWidget,
    ComboBox,
    SearchLineEdit,
)

from qfluentwidgets.components.widgets.acrylic_label import AcrylicBrush


class GalleryCard(HeaderCardWidget):
    """Gallery card"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("屏幕截图")
        self.setBorderRadius(8)

        self.flipView = HorizontalFlipView(self)
        self.expandButton = TransparentToolButton(FluentIcon.CHEVRON_RIGHT_MED, self)

        self.expandButton.setFixedSize(32, 32)
        self.expandButton.setIconSize(QSize(12, 12))

        self.flipView.addImages(
            [
                "resource/shoko1.jpg",
                "resource/shoko2.jpg",
                "resource/shoko3.jpg",
                "resource/shoko4.jpg",
            ]
        )
        self.flipView.setBorderRadius(8)
        self.flipView.setSpacing(10)
        self.flipView.setAutoScroll(True)

        self.setObjectName("asdasdsad")
        self.headerLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        self.viewLayout.addWidget(self.flipView)
