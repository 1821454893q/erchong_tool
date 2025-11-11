import ctypes
from ctypes import wintypes
from src.erchong.common.config import cfg
import os
import sys
import time
from typing import TYPE_CHECKING

import win32gui
import PyQt5.QtCore as qtCore
import PyQt5.QtWidgets as qtWidget

import gas.util.img_util as img_util
import gas.util.screenshot_util as screenshot_util
import qfluentwidgets as qf
import qframelesswindow as qfr

from ..config.settings import QT_QSS_DIR, RESOURCE_DIR
from ..utils.platform import is_win11


from ..utils.logger import get_logger

log = get_logger()


class HwndListWidget(qfr.FramelessWindow):
    def __init__(self):
        super().__init__()
        self._windows = []  # list of (hwnd:int, title:str)
        self._setup_ui()
        self._connect_signals()
        self.refresh()

    def _setup_ui(self):
        self.resize(800, 600)
        self.setTitleBar(qf.SplitTitleBar(self))
        self.setWindowTitle("句柄查找")

        self.setContentsMargins(10, 50, 10, 10)

        self.filter_edit = qf.LineEdit(self)
        self.filter_edit.setPlaceholderText("Filter by title...")

        self.refresh_btn = qf.PushButton("Refresh", self)

        top_layout = qtWidget.QHBoxLayout()
        top_layout.addWidget(self.filter_edit)
        top_layout.addWidget(self.refresh_btn)

        self.list_widget = qf.ListWidget(self)
        self.list_widget.setSelectionMode(
            qtWidget.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.setContextMenuPolicy(
            qtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )

        self.status_label = qf.label.BodyLabel("", self)

        main_layout = qtWidget.QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.status_label)

    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh)
        self.filter_edit.textChanged.connect(self._apply_filter)
        self.list_widget.itemDoubleClicked.connect(self._on_item_activated)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        # 设置样式
        cfg.themeChanged.connect(self.setQss)

    def refresh(self):
        self._windows = self._enumerate_windows()
        self._apply_filter()
        self.status_label.setText(f"{len(self._windows)} windows found")

    def _apply_filter(self):
        text = self.filter_edit.text().lower()
        self.list_widget.clear()
        for hwnd, title in self._windows:
            if not text or text in title.lower():
                item = qtWidget.QListWidgetItem(f"{hwnd:#010x}  {title}")
                item.setData(qtCore.Qt.ItemDataRole.UserRole, hwnd)
                self.list_widget.addItem(item)

    def _on_item_activated(self, item:qtWidget.QListWidgetItem):
        # 选项被激活了
        log.debug(item.text())
        log.debug("my go to home. bey~")


    def _on_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if item is None:
            return
        hwnd = item.data(qtCore.Qt.ItemDataRole.UserRole)
        menu = qf.RoundMenu("Action",self)
        copy_action = menu.addAction(qf.Action("Copy HWND"))
        bring_action = menu.addAction(qf.Action("Bring to Front"))
        action = menu.exec_(self.list_widget.mapToGlobal(pos))
        if action == copy_action:
            clipboard = qtWidget.QApplication.clipboard()
            if clipboard:
                clipboard.setText(hex(hwnd))
        elif action == bring_action:
            try:
                ctypes.windll.user32.SetForegroundWindow(wintypes.HWND(hwnd))
            except Exception:
                pass

    def _enumerate_windows(self):
        windows = []
        try:
            EnumWindows = ctypes.windll.user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(
                wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
            )
            GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
            GetWindowText = ctypes.windll.user32.GetWindowTextW
            IsWindowVisible = ctypes.windll.user32.IsWindowVisible

            def _proc(hwnd, lParam):
                try:
                    if IsWindowVisible(hwnd):
                        length = GetWindowTextLength(hwnd)
                        if length > 0:
                            buf = ctypes.create_unicode_buffer(length + 1)
                            GetWindowText(hwnd, buf, length + 1)
                            title = buf.value
                            windows.append((hwnd, title))
                except Exception as e:
                    log.error(e)
                return True

            EnumWindows(EnumWindowsProc(_proc), 0)
        except Exception:
            # Non-Windows or failure: provide an empty list
            pass
        return windows
    
    def setQss(self):
        self.setStyleSheet(cfg.getQssFile("hwnd_list_widget"))
