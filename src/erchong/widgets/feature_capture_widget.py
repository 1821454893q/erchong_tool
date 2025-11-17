"""窗口特征捕获和匹配工具"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QProgressBar,
)

from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    BodyLabel,
    CaptionLabel,
    ComboBox,
    LineEdit,
    DoubleSpinBox,
    SpinBox,
    InfoBar,
    InfoBarPosition,
    FluentIcon,
    ExpandGroupSettingCard,
)

from gas.util.hwnd_util import get_hwnd_by_class_and_title
from gas.util.screenshot_util import screenshot
from src.erchong.common.style_sheet import StyleSheet
from src.erchong.common.config import cfg
from src.erchong.config.settings import PROJECT_ROOT


@dataclass
class WindowConfig:
    """窗口配置"""

    class_name: str
    titles: List[str]
    description: str = ""


@dataclass
class FeatureTemplate:
    """特征模板"""

    name: str
    image: np.ndarray
    hwnd: int
    position: Dict[str, int]  # x, y, width, height
    confidence_threshold: float = 0.8


class WindowFeatureCaptureWidget(QWidget):
    """窗口特征捕获和匹配工具"""

    # 信号 - 使用兼容的类型
    templateCaptured = pyqtSignal(object)  # FeatureTemplate 对象
    matchFound = pyqtSignal(str, object, float)  # 模板名, 位置字典, 置信度

    def __init__(self, objectName: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(objectName)

        # 窗口配置
        self.window_configs = self._load_window_configs()
        self.current_hwnd = None
        self.current_window_image = None
        self.feature_templates = {}  # Dict[str, FeatureTemplate]

        # 匹配器
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.orb = cv2.ORB_create(nfeatures=1000)

        self._setup_ui()
        self._set_connections()

        StyleSheet.FEATURE_CAPTURE_WIDGET.apply(self)

        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_window_list)
        self.refresh_timer.start(2000)  # 2秒刷新一次

    def _load_window_configs(self):
        """加载窗口配置"""
        # 这里可以从配置文件加载，先写几个示例
        return [
            WindowConfig(
                class_name=cfg.get(cfg.hwndClassname),
                titles=[cfg.get(cfg.hwndWindowsTitle)],
                description="缓存配置窗口",
            ),
            WindowConfig(class_name="UnityWndClass", titles=["原神", "Genshin Impact"], description="原神游戏窗口"),
        ]

    def _setup_ui(self):
        """设置界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 左侧 - 窗口控制和特征管理
        left_widget = QWidget()
        left_widget.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_widget)

        # 窗口选择组
        window_group = QGroupBox("窗口选择")
        window_layout = QVBoxLayout(window_group)

        # 窗口配置选择
        config_layout = QHBoxLayout()
        config_layout.addWidget(BodyLabel("窗口配置:"))
        self.config_combo = ComboBox()
        for config in self.window_configs:
            self.config_combo.addItem(config.description, config)
        config_layout.addWidget(self.config_combo)
        window_layout.addLayout(config_layout)

        # 刷新和连接按钮
        button_layout = QHBoxLayout()
        self.refresh_btn = PushButton("刷新窗口")
        self.connect_btn = PrimaryPushButton("连接窗口")
        button_layout.addWidget(self.refresh_btn)
        button_layout.addWidget(self.connect_btn)
        window_layout.addLayout(button_layout)

        # 窗口列表
        self.window_list = QListWidget()
        self.window_list.setMaximumHeight(150)
        window_layout.addWidget(self.window_list)

        # 窗口状态
        self.window_status_label = CaptionLabel("未连接任何窗口")
        window_layout.addWidget(self.window_status_label)

        left_layout.addWidget(window_group)

        # 特征模板管理组
        template_group = QGroupBox("特征模板管理")
        template_layout = QVBoxLayout(template_group)

        # 模板名称输入
        name_layout = QHBoxLayout()
        name_layout.addWidget(BodyLabel("模板名称:"))
        self.template_name_edit = LineEdit()
        self.template_name_edit.setPlaceholderText("输入模板名称")
        name_layout.addWidget(self.template_name_edit)
        template_layout.addLayout(name_layout)

        # 捕获按钮
        self.capture_btn = PrimaryPushButton("捕获特征区域")
        self.capture_btn.setEnabled(False)
        template_layout.addWidget(self.capture_btn)

        # 模板列表
        self.template_list = QListWidget()
        template_layout.addWidget(self.template_list)

        # 模板操作按钮
        template_btn_layout = QHBoxLayout()
        self.delete_template_btn = PushButton("删除模板")
        self.export_templates_btn = PushButton("导出模板")
        self.import_templates_btn = PushButton("导入模板")

        template_btn_layout.addWidget(self.delete_template_btn)
        template_btn_layout.addWidget(self.export_templates_btn)
        template_btn_layout.addWidget(self.import_templates_btn)
        template_layout.addLayout(template_btn_layout)

        left_layout.addWidget(template_group)

        # 匹配设置组
        match_group = QGroupBox("匹配设置")
        match_layout = QVBoxLayout(match_group)

        # 匹配阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(BodyLabel("匹配阈值:"))
        self.threshold_spin = DoubleSpinBox()
        self.threshold_spin.setRange(0.1, 1.0)
        self.threshold_spin.setValue(0.7)
        self.threshold_spin.setSingleStep(0.05)
        threshold_layout.addWidget(self.threshold_spin)
        match_layout.addLayout(threshold_layout)

        # 自动匹配
        auto_layout = QHBoxLayout()
        self.auto_match_check = QCheckBox("自动匹配")
        self.auto_match_check.setChecked(True)
        auto_layout.addWidget(self.auto_match_check)

        self.match_interval_spin = SpinBox()
        self.match_interval_spin.setRange(100, 5000)
        self.match_interval_spin.setValue(1000)
        self.match_interval_spin.setSuffix(" ms")
        auto_layout.addWidget(BodyLabel("间隔:"))
        auto_layout.addWidget(self.match_interval_spin)
        match_layout.addLayout(auto_layout)

        # 开始匹配按钮
        self.start_match_btn = PrimaryPushButton("开始匹配")
        match_layout.addWidget(self.start_match_btn)

        left_layout.addWidget(match_group)
        left_layout.addStretch()

        # 右侧 - 预览和结果
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 窗口预览组
        preview_group = QGroupBox("窗口预览")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("border: 1px solid gray; background-color: #1a1a1a;")
        self.preview_label.setText("窗口预览区域")
        preview_layout.addWidget(self.preview_label)

        # 预览控制
        preview_control_layout = QHBoxLayout()
        self.refresh_preview_btn = PushButton("刷新预览")
        self.auto_preview_check = QCheckBox("自动刷新预览")
        self.auto_preview_check.setChecked(True)

        preview_control_layout.addWidget(self.refresh_preview_btn)
        preview_control_layout.addStretch()
        preview_control_layout.addWidget(self.auto_preview_check)
        preview_layout.addLayout(preview_control_layout)

        right_layout.addWidget(preview_group)

        # 匹配结果组
        result_group = QGroupBox("匹配结果")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        result_layout.addWidget(self.result_text)

        # 匹配进度
        self.match_progress = QProgressBar()
        self.match_progress.setVisible(False)
        result_layout.addWidget(self.match_progress)

        right_layout.addWidget(result_group)

        # 添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # 自动预览定时器
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self._update_preview)

        # 自动匹配定时器
        self.auto_match_timer = QTimer()
        self.auto_match_timer.timeout.connect(self._auto_match_templates)

    def _set_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.refresh_btn.clicked.connect(self._refresh_window_list)
        self.connect_btn.clicked.connect(self._connect_to_window)
        self.capture_btn.clicked.connect(self._capture_feature_template)
        self.refresh_preview_btn.clicked.connect(self._update_preview)
        self.start_match_btn.clicked.connect(self._toggle_auto_match)

        # 列表连接
        self.window_list.itemClicked.connect(self._on_window_selected)
        self.template_list.itemClicked.connect(self._on_template_selected)

        # 删除模板按钮
        self.delete_template_btn.clicked.connect(self._delete_template)
        self.export_templates_btn.clicked.connect(self._export_templates)
        self.import_templates_btn.clicked.connect(self._import_templates)

        # 复选框连接
        self.auto_preview_check.toggled.connect(self._toggle_auto_preview)
        self.auto_match_check.toggled.connect(self._on_auto_match_changed)

    def _refresh_window_list(self):
        """刷新窗口列表"""
        self.window_list.clear()

        current_config = self.config_combo.currentData()
        if not current_config:
            return

        # 获取匹配的窗口
        hwnds = get_hwnd_by_class_and_title(current_config.class_name, current_config.titles)

        for hwnd in hwnds:
            # 获取窗口标题
            try:
                import win32gui

                title = win32gui.GetWindowText(hwnd)
                item_text = f"{title} (0x{hwnd:X})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, hwnd)
                self.window_list.addItem(item)
            except Exception as e:
                print(f"获取窗口信息失败: {e}")

    def _on_window_selected(self, item):
        """窗口选择变化"""
        hwnd = item.data(Qt.UserRole)
        self.current_hwnd = hwnd
        self.window_status_label.setText(f"已选择窗口: 0x{hwnd:X}")
        self.capture_btn.setEnabled(True)
        self._update_preview()

    def _connect_to_window(self):
        """连接到选中的窗口"""
        if self.window_list.currentItem():
            self._on_window_selected(self.window_list.currentItem())
        else:
            InfoBar.warning(title="警告", content="请先选择一个窗口", parent=self)

    def _update_preview(self):
        """更新窗口预览"""
        if not self.current_hwnd:
            return

        try:
            # 捕获窗口图像
            screenshot_img = screenshot(self.current_hwnd)
            if screenshot_img is not None:
                # 转换为 QImage 并显示
                height, width, channel = screenshot_img.shape
                bytes_per_line = 3 * width
                q_img = QImage(screenshot_img.data, width, height, bytes_per_line, QImage.Format_RGB888)

                # 缩放以适应预览区域
                scaled_pixmap = QPixmap.fromImage(q_img).scaled(
                    self.preview_label.width(), self.preview_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.current_window_image = screenshot_img

        except Exception as e:
            print(f"更新预览失败: {e}")

    def _toggle_auto_preview(self, checked):
        """切换自动预览"""
        if checked and self.current_hwnd:
            self.preview_timer.start(500)  # 0.5秒刷新一次
        else:
            self.preview_timer.stop()

    def _capture_feature_template(self):
        """捕获特征模板"""
        if not self.current_window_image or not self.template_name_edit.text():
            InfoBar.warning(title="警告", content="请先连接窗口并输入模板名称", parent=self)
            return

        template_name = self.template_name_edit.text().strip()
        if template_name in self.feature_templates:
            InfoBar.warning(title="警告", content="模板名称已存在", parent=self)
            return

        # 这里可以添加区域选择功能
        # 暂时使用整个窗口作为模板
        template = FeatureTemplate(
            name=template_name,
            image=self.current_window_image.copy(),
            hwnd=self.current_hwnd,
            position={
                "x": 0,
                "y": 0,
                "width": self.current_window_image.shape[1],
                "height": self.current_window_image.shape[0],
            },
            confidence_threshold=self.threshold_spin.value(),
        )

        # 提取特征
        keypoints, descriptors = self.orb.detectAndCompute(template.image, None)
        if descriptors is not None:
            self.feature_templates[template_name] = template
            self.template_list.addItem(template_name)
            self.template_name_edit.clear()

            InfoBar.success(title="成功", content=f"已捕获模板: {template_name}", parent=self)

            self.templateCaptured.emit(template)
        else:
            InfoBar.error(title="错误", content="无法提取图像特征", parent=self)

    def _on_template_selected(self, item):
        """模板选择变化"""
        # 可以在这里显示模板详情
        pass

    def _delete_template(self):
        """删除选中的模板"""
        current_item = self.template_list.currentItem()
        if current_item:
            template_name = current_item.text()
            del self.feature_templates[template_name]
            self.template_list.takeItem(self.template_list.row(current_item))

    def _toggle_auto_match(self):
        """切换自动匹配"""
        if self.auto_match_timer.isActive():
            self.auto_match_timer.stop()
            self.start_match_btn.setText("开始匹配")
            self.match_progress.setVisible(False)
        else:
            interval = self.match_interval_spin.value()
            self.auto_match_timer.start(interval)
            self.start_match_btn.setText("停止匹配")
            self.match_progress.setVisible(True)

    def _on_auto_match_changed(self, checked):
        """自动匹配设置变化"""
        if checked and self.auto_match_timer.isActive():
            interval = self.match_interval_spin.value()
            self.auto_match_timer.setInterval(interval)

    def _auto_match_templates(self):
        """自动匹配模板"""
        if not self.current_hwnd or not self.feature_templates:
            return

        try:
            # 捕获当前窗口图像
            current_image = screenshot(self.current_hwnd)
            if current_image is None:
                return

            results = []

            for template_name, template in self.feature_templates.items():
                # 特征匹配
                kp1, des1 = self.orb.detectAndCompute(template.image, None)
                kp2, des2 = self.orb.detectAndCompute(current_image, None)

                if des1 is not None and des2 is not None:
                    matches = self.matcher.match(des1, des2)
                    matches = sorted(matches, key=lambda x: x.distance)

                    # 计算匹配度
                    if len(matches) > 10:
                        good_matches = [m for m in matches if m.distance < 50]
                        confidence = len(good_matches) / len(matches)

                        if confidence >= template.confidence_threshold:
                            results.append(
                                {"template": template_name, "confidence": confidence, "matches": len(good_matches)}
                            )

            # 显示结果
            self._display_match_results(results)

        except Exception as e:
            print(f"匹配失败: {e}")

    def _display_match_results(self, results):
        """显示匹配结果"""
        if not results:
            self.result_text.setText("未找到匹配的模板")
            return

        result_text = "匹配结果:\n"
        for result in sorted(results, key=lambda x: x["confidence"], reverse=True):
            result_text += (
                f"✅ {result['template']}: 置信度 {result['confidence']:.3f} ({result['matches']} 个匹配点)\n"
            )

        self.result_text.setText(result_text)

    def _export_templates(self):
        """导出模板"""
        if not self.feature_templates:
            InfoBar.warning("没有模板可导出", parent=self)
            return

        # 实现模板导出逻辑
        pass

    def _import_templates(self):
        """导入模板"""
        # 实现模板导入逻辑
        pass

    def closeEvent(self, event):
        """关闭事件"""
        self.refresh_timer.stop()
        self.preview_timer.stop()
        self.auto_match_timer.stop()
        super().closeEvent(event)
