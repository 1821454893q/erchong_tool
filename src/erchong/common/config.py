from enum import Enum

import qfluentwidgets as qf
import PyQt5.QtCore as qc
import PyQt5.QtGui as qg
from src.erchong.config.settings import QT_QSS_DIR, RESOURCE_DIR

class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = qc.QLocale(qc.QLocale.Chinese, qc.QLocale.China)
    CHINESE_TRADITIONAL = qc.QLocale(qc.QLocale.Chinese, qc.QLocale.HongKong)
    ENGLISH = qc.QLocale(qc.QLocale.English)
    AUTO = qc.QLocale()

class LanguageSerializer(qf.ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(qc.QLocale(value)) if value != "Auto" else Language.AUTO

class Config(qf.QConfig):
    # main window
    enableAcrylicBackground = qf.ConfigItem(
        "MainWindow", "EnableAcrylicBackground", False, qf.BoolValidator())
    minimizeToTray = qf.ConfigItem(
        "MainWindow", "MinimizeToTray", True, qf.BoolValidator())
    playBarColor = qf.ColorConfigItem("MainWindow", "PlayBarColor", "#225C7F")
    recentPlaysNumber = qf.RangeConfigItem(
        "MainWindow", "RecentPlayNumbers", 300, qf.RangeValidator(10, 300))
    dpiScale = qf.OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", qf.OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = qf.OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, qf.OptionsValidator(Language), LanguageSerializer(), restart=True)
    
    def getQssFile(self,fileName:str) -> str:
        filePath = ""
        if qf.isDarkTheme():
            filePath = f"{QT_QSS_DIR}/dark/{fileName}.qss"
        else:
            filePath = f"{QT_QSS_DIR}/light/{fileName}.qss"
        try:
            with open(filePath) as f:
                return f.read()
        except:
            return ""


cfg = Config()
qf.qconfig.load(str(RESOURCE_DIR/"qt/config.json"), cfg)


def create_app_icon():
    """创建应用程序图标"""
    pixmap = qg.QPixmap(16, 16)
    pixmap.fill(qg.QColor(70, 130, 180))  # 钢蓝色
    return qg.QIcon(pixmap)