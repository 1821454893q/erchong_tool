"""画廊卡片组件"""
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QWidget

from qfluentwidgets import (
    FluentIcon,
    HeaderCardWidget,
    HorizontalFlipView,
    TransparentToolButton,
)

from ..config.settings import RESOURCE_DIR


class GalleryCard(HeaderCardWidget):
    """画廊卡片"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle("屏幕截图")
        self.setBorderRadius(50)

        self.flipView = HorizontalFlipView(self)
        self.expandButton = TransparentToolButton(
            FluentIcon.CHEVRON_RIGHT_MED, self
        )

        self.expandButton.setFixedSize(32, 32)
        self.expandButton.setIconSize(QSize(12, 12))

        image_files = [
            "shoko1.jpg",
            "shoko2.jpg",
            "shoko3.jpg",
            "shoko4.jpg",
        ]
        self.flipView.addImages([str(RESOURCE_DIR / img) for img in image_files])
        self.flipView.setBorderRadius(30)
        self.flipView.setSpacing(10)
        self.flipView.setAutoScroll(True)

        self.setObjectName("gallery-card")
        self.headerLayout.addWidget(self.expandButton, 0, Qt.AlignmentFlag.AlignRight)
        self.viewLayout.addWidget(self.flipView)

