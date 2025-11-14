from src.erchong.common.config import cfg

import qframelesswindow as qfr
import qfluentwidgets as qf
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from gas.util.hwnd_util import WindowInfo, list_all_windows

from src.erchong.utils.logger import get_logger

log = get_logger()


class HwndListWidget(qfr.FramelessWindow):
    """窗口句柄列表窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hwnd List")
        self.resize(800, 600)
        self.setContentsMargins(10, 40, 10, 10)

        self._setup_ui()
        self._set_connections()

    def _setup_ui(self):
        self.main_layout = qtw.QVBoxLayout()

        t_h_box = qtw.QHBoxLayout()
        self.search_edit = qf.LineEdit(self)
        self.search_edit.setPlaceholderText("输出窗口标题过滤")

        self.search_btn = qf.PrimaryPushButton("搜索", self)
        self.search_btn.setMinimumSize(100, 0)

        self.tree_view = qf.TreeView(self)
        self.tree_model = WindowModel(list_all_windows())
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(False)
        # 最后一列固定宽度

        self.tree_view.setColumnWidth(1, 200)
        self.tree_view.header().setSectionResizeMode(0, qtw.QHeaderView.ResizeMode.ResizeToContents)
        self.tree_view.header().setSectionResizeMode(1, qtw.QHeaderView.ResizeMode.Interactive)
        self.tree_view.header().setSectionResizeMode(2, qtw.QHeaderView.ResizeMode.ResizeToContents)

        t_h_box.addWidget(self.search_edit)
        t_h_box.addWidget(self.search_btn)

        self.main_layout.addLayout(t_h_box)
        self.main_layout.addWidget(self.tree_view)

        self.setLayout(self.main_layout)

    def _set_connections(self):
        cfg.themeChanged.connect(self._set_qss)

        self.tree_view.clicked.connect(self._on_tree_view_clicked)
        self.search_btn.clicked.connect(self._on_search_clicked)

    def _set_qss(self):
        self.setStyleSheet(cfg.getQssFile("hwnd_list_widget"))

    def _on_tree_view_clicked(self, index: qtc.QModelIndex):
        node: WindowInfo = index.internalPointer()
        info = f"Hwnd: {node.hwnd}\nTitle: {node.title}\nClass: {node.class_name}\nVisible: {node.is_visible}\nRect: {node.position} {node.size} \n"
        qf.MessageBox("窗口信息", info, self)

    def _on_search_clicked(self):
        filter_text = self.search_edit.text().strip().lower()
        if not filter_text:
            self.tree_model = WindowModel(list_all_windows())
        else:
            all_windows = list_all_windows()
            filtered_windows = [w for w in all_windows if filter_text in (w.title or "").lower()]
            self.tree_model = WindowModel(filtered_windows)
        self.tree_view.setModel(self.tree_model)


class WindowModel(qtc.QAbstractItemModel):
    """窗口模型"""

    def __init__(self, windowsList: list[WindowInfo] = None):
        super().__init__()
        self.root_node_list = windowsList if windowsList else []

        # 过滤一下 不可见窗口
        self.root_node_list = [node for node in self.root_node_list if node.is_visible]

        log.debug(f"WindowModel initialized with {len(self.root_node_list)} root nodes.")

    def index(self, row, column, parent=qtc.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return qtc.QModelIndex()

        if not parent.isValid():
            # 根节点的子节点
            if row < len(self.root_node_list):
                child_node = self.root_node_list[row]
                return self.createIndex(row, column, child_node)
        else:
            # 其他节点的子节点
            parent_node = parent.internalPointer()
            if row < len(parent_node.children):
                child_node = parent_node.children[row]
                return self.createIndex(row, column, child_node)

        return qtc.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return qtc.QModelIndex()

        child_node = index.internalPointer()
        parent_node = child_node.parent

        if parent_node is None:
            return qtc.QModelIndex()

        grandparent_node = parent_node.parent
        if grandparent_node is None:
            for row, node in enumerate(self.root_node_list):
                if node == parent_node:
                    return self.createIndex(row, 0, parent_node)
        else:
            for row, node in enumerate(grandparent_node.children):
                if node == parent_node:
                    return self.createIndex(row, 0, parent_node)

        return qtc.QModelIndex()

    def rowCount(self, parent=qtc.QModelIndex()):
        if not parent.isValid():
            return len(self.root_node_list)
        return len(parent.internalPointer().children)

    def columnCount(self, parent=...):
        return 3

    def data(self, index, role: int = ...):
        if not index.isValid():
            return None
        node = index.internalPointer()
        column = index.column()

        if role == qtc.Qt.ItemDataRole.DisplayRole:
            if column == 0:
                # 第一列：窗口名称
                title = node.title if hasattr(node, "title") and node.title else "无标题"
                return title
            elif column == 1:
                # 第二列：类名
                class_name = node.class_name if hasattr(node, "class_name") else "未知类"
                return class_name
            elif column == 2:
                # 第三列：窗口大小
                if hasattr(node, "size") and node.size:
                    width, height = node.size
                    return f"{width} x {height}"
                else:
                    return "未知大小"

        elif role == qtc.Qt.ItemDataRole.ToolTipRole:
            # 工具提示显示完整信息
            title = node.title if hasattr(node, "title") and node.title else "无标题"
            class_name = node.class_name if hasattr(node, "class_name") else "未知类"
            hwnd = node.hwnd if hasattr(node, "hwnd") else "未知"
            if hasattr(node, "size") and node.size:
                width, height = node.size
                size_info = f"{width} x {height}"
            else:
                size_info = "未知大小"

            return f"窗口: {title}\n类名: {class_name}\n大小: {size_info}\nHWND: {hwnd}"

        elif role == qtc.Qt.ItemDataRole.UserRole:
            # 返回节点对象用于其他用途
            return node

        elif role == qtc.Qt.ItemDataRole.TextAlignmentRole:
            return qtc.Qt.AlignmentFlag.AlignLeft | qtc.Qt.AlignmentFlag.AlignVCenter

        return None

    def headerData(self, section, orientation, role=qtc.Qt.ItemDataRole.DisplayRole):
        """设置表头"""
        if orientation == qtc.Qt.Orientation.Horizontal and role == qtc.Qt.ItemDataRole.DisplayRole:
            headers = ["窗口名称", "类名", "窗口大小"]
            if section < len(headers):
                return headers[section]
        return None
