from enum import Enum

import qfluentwidgets as qf
import PyQt5.QtCore as qc
import PyQt5.QtGui as qg
from src.erchong.config.settings import QT_QSS_DIR, RESOURCE_DIR


class Language(Enum):
    """Language enumeration"""

    CHINESE_SIMPLIFIED = qc.QLocale(qc.QLocale.Chinese, qc.QLocale.China)
    CHINESE_TRADITIONAL = qc.QLocale(qc.QLocale.Chinese, qc.QLocale.HongKong)
    ENGLISH = qc.QLocale(qc.QLocale.English)
    AUTO = qc.QLocale()


class LanguageSerializer(qf.ConfigSerializer):
    """Language serializer"""

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(qc.QLocale(value)) if value != "Auto" else Language.AUTO


class Config(qf.QConfig):
    # main windows
    # main_windows_theme = qf.ConfigItem(
    #     group="MainWindow",
    #     name="Theme",
    #     default=Theme.Light,
    #     validator=qf.OptionsValidator([Theme.Light, Theme.Dark, Theme.Auto]),
    #     serializer=qf.EnumSerializer(qf.Theme),
    #     restart=False,
    # )

    # home interface
    hwndWindowsTitle = qf.ConfigItem(group="HomeInterface", name="hwndWindowsTitle", default="")
    hwndClassname = qf.ConfigItem(group="HomeInterface", name="hwndClassname", default="")


cfg = Config()
qf.qconfig.load(str(RESOURCE_DIR / "config_params.json"), cfg)


def create_app_icon():
    """创建应用程序图标"""
    pixmap = qg.QPixmap(16, 16)
    pixmap.fill(qg.QColor(70, 130, 180))  # 钢蓝色
    return qg.QIcon(pixmap)
