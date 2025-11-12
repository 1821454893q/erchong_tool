import ctypes
from ctypes import wintypes
from src.erchong.common.config import cfg,create_app_icon
import os
import sys
import time
from typing import TYPE_CHECKING, List, Optional

import win32gui
import PyQt5.QtCore as qtCore
import PyQt5.QtWidgets as qtWidget

import gas.util.img_util as img_util
import gas.util.screenshot_util as screenshot_util
import qfluentwidgets as qf
import qframelesswindow as qfr
import gas.util as gasUtil

from ..config.settings import QT_QSS_DIR, RESOURCE_DIR
from ..utils.platform import is_win11
from gas.util.hwnd_util import WindowInfo

from ..utils.logger import get_logger

log = get_logger()


class HwndListWidget(qfr.FramelessWindow):
    def __init__(self):
        super().__init__()
        self._windows : List[WindowInfo] = []
        self._setupUi()
        self._connectSignals()
        self.refresh()

    def _setupUi(self):
        self.resize(800, 600)
        self.setTitleBar(qf.SplitTitleBar(self))
        self.setWindowTitle("句柄查找")

        self.setContentsMargins(10, 50, 10, 10)

        self.filterEdit = qf.LineEdit(self)
        self.filterEdit.setPlaceholderText("Filter by title...")

        self.refreshBtn = qf.PushButton("Refresh", self)

        topLayout = qtWidget.QHBoxLayout()
        topLayout.addWidget(self.filterEdit)
        topLayout.addWidget(self.refreshBtn)

        self.treeWidget = qf.TreeWidget(self)
        self.treeWidget.setSelectionMode(
            qtWidget.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.treeWidget.setSelectionBehavior(
            qtWidget.QAbstractItemView.SelectionBehavior.SelectItems
        )
        # 禁用水平滑动 可能导致卡顿
        self.treeWidget.scrollDelagate.verticalSmoothScroll.setSmoothMode(qf.SmoothMode.NO_SMOOTH)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setContextMenuPolicy(qtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._loaded_items = {}  # 记录已加载的项

        self.statusLabel = qf.label.StrongBodyLabel("", self)
        
        mainLayout = qtWidget.QVBoxLayout(self)
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.treeWidget)
        mainLayout.addWidget(self.statusLabel)

    def _connectSignals(self):
        self.refreshBtn.clicked.connect(self.refresh)
        self.filterEdit.textChanged.connect(self._applyFilter)
        self.treeWidget.itemDoubleClicked.connect(self._onItemActivated)
        self.treeWidget.customContextMenuRequested.connect(self._onContextMenu)
        self.treeWidget.itemExpanded.connect(self._on_item_expanded)
        # 设置样式
        cfg.themeChanged.connect(self.setQss)

    def refresh(self):
        self._windows = self._enumerate_windows()
        self._applyFilter()
        self.statusLabel.setText(f"{len(self._windows)} windows found")

    def _applyFilter(self):
        text = self.filterEdit.text().lower()
        self.treeWidget.clear()
        
        # 递归遍历窗口树
        for window_info in self._windows:
            if window_info.parent is None and window_info.title != "":  # 只处理根窗口
                self._addWindowToTree(window_info, text, None)

    def _on_item_expanded(self, item):
        """当项展开时加载子节点"""
        window_info = item.data(0, qtCore.Qt.ItemDataRole.UserRole)
        if not window_info:
            return
        
        log.debug(f"懒加载了 hwnd:{window_info.hwnd}")
        # 检查是否已经加载过
        if self._loaded_items.get(window_info.hwnd, True):  # 默认True表示已加载
            return
        
        # 移除占位项
        if item.childCount() == 1 and item.child(0).text(0) == '加载中...':
            item.takeChild(0)  # 使用takeChild而不是removeChild
        
        # 加载实际子节点
        if window_info.children:
            for child_window in window_info.children:
                self._addWindowToTree(child_window, "", item)
        
        # 标记为已加载
        self._loaded_items[window_info.hwnd] = True

    def _addWindowToTree(self, window_info: WindowInfo, filter_text: str, parent_item: Optional[qtWidget.QTreeWidgetItem]):
        """递归添加窗口到 tree widget"""
        title_empty = not window_info.title.strip()

        # 统一的过滤逻辑
        should_show = (not filter_text or window_info.is_visible or
                    (not title_empty and filter_text in window_info.title.lower()) or 
                    filter_text in window_info.class_name.lower())

        if should_show:
            # 创建 item
            if parent_item is None:
                # 根节点
                item = qtWidget.QTreeWidgetItem(self.treeWidget, [''])
            else:
                # 子节点
                item = qtWidget.QTreeWidgetItem(parent_item, [''])
            
            # 创建 card 组件
            card = AppCard(
                create_app_icon(),
                title=window_info.title,
                content=f"{window_info.class_name} | {window_info.size[0]}x{window_info.size[1]}",
            )
            
            # 设置 item 大小
            item.setSizeHint(0, card.sizeHint())
            self.treeWidget.setItemWidget(item, 0, card)
            item.setData(0, qtCore.Qt.ItemDataRole.UserRole, window_info)

            # 如果有子窗口，添加一个占位项
            if window_info.children:
                placeholder = qtWidget.QTreeWidgetItem(['加载中...'])
                item.addChild(placeholder)
                # 使用窗口句柄作为key存储加载状态
                self._loaded_items[window_info.hwnd] = False
            
            if parent_item:
                parent_item.setExpanded(True)

    def _onItemActivated(self, item:qtWidget.QTreeWidgetItem,column):
        # 获取存储的 WindowInfo 对象
        window_info = item.data(0, qtCore. Qt.ItemDataRole.UserRole)
        if window_info:
            log.debug(f"双击窗口: {window_info.title}")
            log.debug(f"HWND: {window_info.hwnd}")
            log.debug(f"类名: {window_info.class_name}")
            log.debug(f"位置: {window_info.position}")
            log.debug(f"大小: {window_info.size}")


    def _onContextMenu(self, pos):
        item = self.treeWidget.itemAt(pos)
        if item is None:
            return
        window_info = item.data(0, qtCore. Qt.ItemDataRole.UserRole)
        if window_info is None:
            return
        
        menu = qf.RoundMenu("Action",self)
        copy_action = menu.addAction(qf.Action("Copy HWND"))
        bring_action = menu.addAction(qf.Action("Bring to Front"))
        action = menu.exec_(self.treeWidget.mapToGlobal(pos))
        if action == copy_action:
            clipboard = qtWidget.QApplication.clipboard()
            if clipboard:
                clipboard.setText(hex(window_info.hwnd))
        elif action == bring_action:
            try:
                gasUtil.hwnd_util.window_activate(window_info.hwnd)
            except Exception:
                pass

    def _enumerate_windows(self) -> List[gasUtil.hwnd_util.WindowInfo]:
        windowsTree = []
        try:
            windowsTree = gasUtil.hwnd_util.list_all_windows()
        except Exception:
            # Non-Windows or failure: provide an empty list
            pass
        return windowsTree
    
    def setQss(self):
        self.setStyleSheet(cfg.getQssFile("hwnd_list_widget"))

class AppCard(qf.CardWidget):

    def __init__(self, icon, title, content, parent=None):
        super().__init__(parent)
        
        self.h_box_layout = qtWidget.QHBoxLayout(self)
        self.h_box_layout.setContentsMargins(8, 4, 8, 4)
        self.h_box_layout.setSpacing(6)
        
        # 图标
        self.icon_label = qf.IconWidget(icon)
        self.icon_label.setFixedSize(16, 16)
        self.h_box_layout.addWidget(self.icon_label)
        
        # 标题
        self.title_label = qf.StrongBodyLabel(title)
        self.h_box_layout.addWidget(self.title_label)
        
        # 弹性空间
        self.h_box_layout.addStretch(1)
        
        # 类名
        self.content_label = qf.CaptionLabel(content)
        self.h_box_layout.addWidget(self.content_label)
        
        # 固定高度，宽度自适应
        self.setFixedHeight(30)
        self.setSizePolicy(
            qtWidget.QSizePolicy.Policy.Expanding,
            qtWidget.QSizePolicy.Policy.Fixed
        )