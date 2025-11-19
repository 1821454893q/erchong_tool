"""图片标注工具组件 - 修复图片切换问题"""

import datetime
import os
import json
from pathlib import Path
import shutil
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QApplication,
    QDialog,
)

from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    BodyLabel,
    CaptionLabel,
    ComboBox,
    LineEdit,
    TextEdit,
    InfoBar,
    InfoBarPosition,
    FluentIcon,
    CheckBox,
    SpinBox,
    DoubleSpinBox,
    SimpleCardWidget,
    ScrollArea,
    setTheme,
    Theme,
    CheckableMenu,
    CheckBox,
)

from src.erchong.common.style_sheet import StyleSheet
from src.erchong.config.settings import PROJECT_ROOT
from src.erchong.utils.logger import get_logger

log = get_logger()


class AnnotationCanvas(QLabel):
    """标注画布 - 支持预设比例"""

    bboxDrawn = pyqtSignal(list, str)  # 发送标注框和类别
    imageLoaded = pyqtSignal()  # 图片加载完成信号

    # 预设比例
    ASPECT_RATIOS = {
        "自由比例": (0, 0),
        "16:9": (16, 9),
        "4:3": (4, 3),
        "1:1": (1, 1),
        "21:9": (21, 9),
        "3:2": (3, 2),
        "16:10": (16, 10),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px solid gray; background-color: #f0f0f0;")
        self.setMinimumSize(400, 300)

        self.original_pixmap = None
        self.current_pixmap = None
        self.scale_factor = 1.0
        self.image_offset = QPoint(0, 0)  # 图片在画布中的偏移量

        # 标注状态
        self.is_drawing = False
        self.start_pos = QPoint()
        self.current_pos = QPoint()
        self.current_bbox = None
        self.current_class = "object"

        # 存储所有标注（存储原始图片坐标）
        self.annotations = []  # 每个元素: [x1, y1, x2, y2, class_name]

        # 绘制样式
        self.bbox_pen = QPen(QColor(0, 255, 0), 2)
        self.drawing_pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)

        # 比例设置
        self.aspect_ratio = "自由比例"  # 默认自由比例
        self.fixed_width = 600  # 固定宽度
        self.fixed_height = 450  # 固定高度

    def set_aspect_ratio(self, ratio_name):
        """设置画布比例"""
        if ratio_name in self.ASPECT_RATIOS:
            self.aspect_ratio = ratio_name
            self._update_canvas_size()

    def set_fixed_size(self, width, height):
        """设置固定尺寸"""
        self.fixed_width = width
        self.fixed_height = height
        self._update_canvas_size()

    def _update_canvas_size(self):
        """根据比例更新画布尺寸"""
        if self.aspect_ratio == "自由比例":
            # 自由比例，使用固定尺寸
            self.setFixedSize(self.fixed_width, self.fixed_height)
        else:
            # 计算基于比例的尺寸
            width_ratio, height_ratio = self.ASPECT_RATIOS[self.aspect_ratio]

            # 以高度为基准计算宽度
            base_height = self.fixed_height
            calculated_width = int(base_height * width_ratio / height_ratio)

            # 确保不超过最大尺寸
            max_width = 1200
            if calculated_width > max_width:
                calculated_width = max_width
                base_height = int(calculated_width * height_ratio / width_ratio)

            self.setFixedSize(calculated_width, base_height)

        # 重新加载当前图片以适应新尺寸
        if self.original_pixmap:
            self._resize_pixmap()
            self.setPixmap(self.current_pixmap)
            self.update()

    def load_image(self, image_path):
        """加载图片"""
        try:
            # 先清空当前显示
            self.clear()
            self.annotations.clear()

            QApplication.processEvents()

            self.original_pixmap = QPixmap(str(image_path))
            if self.original_pixmap.isNull():
                log.error(f"无法加载图片: {image_path}")
                return False

            self.setText("加载中...")
            QApplication.processEvents()

            # 缩放图片并计算偏移量
            self._resize_pixmap()

            self.setPixmap(self.current_pixmap)
            self.update()

            self.imageLoaded.emit()
            return True

        except Exception as e:
            log.error(f"加载图片失败 {image_path}: {e}")
            self.setText(f"加载失败: {e}")
            return False

    def _resize_pixmap(self):
        """调整图片大小并计算偏移量"""
        if not self.original_pixmap:
            return

        # 获取画布的实际可用大小
        canvas_width = self.width() - 4
        canvas_height = self.height() - 4

        if canvas_width <= 0 or canvas_height <= 0:
            return

        # 保持宽高比缩放
        self.current_pixmap = self.original_pixmap.scaled(
            canvas_width, canvas_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # 计算图片在画布中的偏移量（居中显示）
        self.image_offset.setX((canvas_width - self.current_pixmap.width()) // 2)
        self.image_offset.setY((canvas_height - self.current_pixmap.height()) // 2)

        # 计算缩放因子
        if self.current_pixmap.width() > 0:
            self.scale_factor = self.original_pixmap.width() / self.current_pixmap.width()
        else:
            self.scale_factor = 1.0

    def _display_to_original_coords(self, display_point):
        """显示坐标转换为原始图片坐标"""
        # 减去图片偏移量，然后应用缩放因子
        x = (display_point.x() - self.image_offset.x()) * self.scale_factor
        y = (display_point.y() - self.image_offset.y()) * self.scale_factor
        return QPoint(int(x), int(y))

    def _original_to_display_coords(self, original_point):
        """原始图片坐标转换为显示坐标"""
        if not self.current_pixmap or not self.original_pixmap:
            return original_point

        # 应用缩放因子，然后加上图片偏移量
        x = (original_point.x() / self.scale_factor) + self.image_offset.x()
        y = (original_point.y() / self.scale_factor) + self.image_offset.y()
        return QPoint(int(x), int(y))

    def _original_to_display_rect(self, x1, y1, x2, y2):
        """原始图片矩形转换为显示矩形"""
        top_left = self._original_to_display_coords(QPoint(x1, y1))
        bottom_right = self._original_to_display_coords(QPoint(x2, y2))
        return top_left, bottom_right

    def set_current_class(self, class_name):
        """设置当前标注类别"""
        self.current_class = class_name

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下开始绘制"""
        if event.button() == Qt.LeftButton and self.current_pixmap:
            # 检查点击位置是否在图片范围内
            click_pos = event.pos()
            if (
                self.image_offset.x() <= click_pos.x() <= self.image_offset.x() + self.current_pixmap.width()
                and self.image_offset.y() <= click_pos.y() <= self.image_offset.y() + self.current_pixmap.height()
            ):

                self.is_drawing = True
                self.start_pos = event.pos()
                self.current_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动更新绘制"""
        if self.is_drawing:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放完成绘制"""
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.current_pos = event.pos()

            # 检查释放位置是否在图片范围内
            release_pos = event.pos()
            if (
                self.image_offset.x() <= release_pos.x() <= self.image_offset.x() + self.current_pixmap.width()
                and self.image_offset.y() <= release_pos.y() <= self.image_offset.y() + self.current_pixmap.height()
            ):

                # 确保坐标有效
                x1, y1 = self.start_pos.x(), self.start_pos.y()
                x2, y2 = self.current_pos.x(), self.current_pos.y()

                # 标准化坐标 (确保 x1<=x2, y1<=y2)
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)

                # 检查标注框大小
                if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                    # 转换为原始图片坐标
                    orig_start = self._display_to_original_coords(QPoint(x1, y1))
                    orig_end = self._display_to_original_coords(QPoint(x2, y2))

                    # 确保坐标在图片范围内
                    orig_x1 = max(0, min(orig_start.x(), self.original_pixmap.width() - 1))
                    orig_y1 = max(0, min(orig_start.y(), self.original_pixmap.height() - 1))
                    orig_x2 = max(0, min(orig_end.x(), self.original_pixmap.width() - 1))
                    orig_y2 = max(0, min(orig_end.y(), self.original_pixmap.height() - 1))

                    bbox = [orig_x1, orig_y1, orig_x2, orig_y2, self.current_class]
                    self.annotations.append(bbox)
                    self.bboxDrawn.emit(bbox, self.current_class)

            self.update()

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)

        if not self.current_pixmap:
            return

        painter = QPainter(self)

        # 绘制已有标注框
        for bbox in self.annotations:
            x1, y1, x2, y2, class_name = bbox

            # 转换为显示坐标
            disp_top_left, disp_bottom_right = self._original_to_display_rect(x1, y1, x2, y2)
            disp_x1, disp_y1 = disp_top_left.x(), disp_top_left.y()
            disp_x2, disp_y2 = disp_bottom_right.x(), disp_bottom_right.y()

            # 只绘制在图片范围内的标注
            if (
                self.image_offset.x() <= disp_x1 <= self.image_offset.x() + self.current_pixmap.width()
                and self.image_offset.y() <= disp_y1 <= self.image_offset.y() + self.current_pixmap.height()
            ):

                painter.setPen(self.bbox_pen)
                painter.drawRect(disp_x1, disp_y1, disp_x2 - disp_x1, disp_y2 - disp_y1)

                # 绘制类别标签背景
                label_width = len(class_name) * 8 + 4
                painter.fillRect(disp_x1, disp_y1 - 20, label_width, 15, QColor(0, 255, 0, 200))

                # 绘制类别标签文字
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(disp_x1 + 2, disp_y1 - 5, class_name)

        # 绘制当前正在绘制的框
        if self.is_drawing:
            painter.setPen(self.drawing_pen)
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = self.current_pos.x(), self.current_pos.y()

            # 确保绘制在图片范围内
            if (
                self.image_offset.x() <= x1 <= self.image_offset.x() + self.current_pixmap.width()
                and self.image_offset.y() <= y1 <= self.image_offset.y() + self.current_pixmap.height()
            ):
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)

    def clear_annotations(self):
        """清空所有标注"""
        self.annotations.clear()
        self.update()

    def remove_last_annotation(self):
        """移除最后一个标注"""
        if self.annotations:
            self.annotations.pop()
            self.update()

    def resizeEvent(self, event):
        """调整大小事件 - 关键修复"""
        super().resizeEvent(event)

        # 保存当前标注
        saved_annotations = self.annotations.copy()

        # 重新计算图片显示
        if self.original_pixmap:
            self._resize_pixmap()
            if self.current_pixmap:
                self.setPixmap(self.current_pixmap)

            # 恢复标注
            self.annotations = saved_annotations
            self.update()

    def get_image_display_rect(self):
        """获取图片在画布中的显示区域"""
        return QRect(self.image_offset, self.current_pixmap.size())


class AnnotationWidget(QWidget):
    """标注工具主界面"""

    def __init__(self, objectName: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(objectName)

        self.current_image_path = None
        self.image_files = []
        self.current_index = 0
        self.classes = ["ui_quit", "ui_menu", "ui_lv"]  # 默认类别

        self._setup_ui()
        self._set_connections()

        StyleSheet.ANNOTATION_WIDGET.apply(self)

    def _setup_ui(self):
        """设置界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 左侧 - 图片和标注区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 图片信息和画布控制
        info_group = QGroupBox("图片信息和画布设置")
        info_layout = QVBoxLayout(info_group)

        # 第一行：图片信息
        image_info_layout = QHBoxLayout()
        self.image_info_label = BodyLabel("未选择图片")
        self.progress_label = CaptionLabel("0/0")

        image_info_layout.addWidget(self.image_info_label)
        image_info_layout.addStretch()
        image_info_layout.addWidget(self.progress_label)

        info_layout.addLayout(image_info_layout)

        # 第二行：画布比例设置
        canvas_control_layout = QHBoxLayout()
        canvas_control_layout.addWidget(BodyLabel("画布比例:"))

        # 比例选择
        self.canvas = AnnotationCanvas()
        self.aspect_combo = ComboBox()
        for ratio_name in self.canvas.ASPECT_RATIOS.keys():
            self.aspect_combo.addItem(ratio_name)
        self.aspect_combo.setCurrentText("自由比例")

        # 尺寸设置
        canvas_control_layout.addWidget(self.aspect_combo)
        canvas_control_layout.addWidget(BodyLabel("宽度:"))

        self.width_spin = SpinBox()
        self.width_spin.setRange(400, 2000)
        self.width_spin.setValue(600)
        self.width_spin.setSuffix(" px")

        canvas_control_layout.addWidget(self.width_spin)
        canvas_control_layout.addWidget(BodyLabel("高度:"))

        self.height_spin = SpinBox()
        self.height_spin.setRange(300, 1500)
        self.height_spin.setValue(450)
        self.height_spin.setSuffix(" px")

        canvas_control_layout.addWidget(self.height_spin)

        # 应用按钮
        self.apply_size_btn = PushButton("应用尺寸")
        canvas_control_layout.addWidget(self.apply_size_btn)

        canvas_control_layout.addStretch()
        info_layout.addLayout(canvas_control_layout)

        left_layout.addWidget(info_group)

        # 标注画布
        left_layout.addWidget(self.canvas, 1)

        # 画布控制按钮
        control_layout = QHBoxLayout()
        self.prev_btn = PushButton("上一张")
        self.next_btn = PushButton("下一张")
        self.clear_btn = PushButton("清空标注")
        self.undo_btn = PushButton("撤销")

        control_layout.addWidget(self.prev_btn)
        control_layout.addWidget(self.next_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.undo_btn)
        control_layout.addWidget(self.clear_btn)

        left_layout.addLayout(control_layout)

        # 右侧 - 控制面板（保持不变）
        right_widget = QWidget()
        right_widget.setMaximumWidth(300)
        right_layout = QVBoxLayout(right_widget)

        # 数据集管理
        dataset_group = QGroupBox("数据集管理")
        dataset_layout = QVBoxLayout(dataset_group)

        self.load_dataset_btn = PrimaryPushButton("加载图片文件夹")
        self.dataset_path_label = CaptionLabel("未选择文件夹")

        dataset_layout.addWidget(self.load_dataset_btn)
        dataset_layout.addWidget(self.dataset_path_label)

        right_layout.addWidget(dataset_group)

        # 类别管理
        class_group = QGroupBox("类别管理")
        class_layout = QVBoxLayout(class_group)

        # 类别列表
        self.class_list = QListWidget()
        self.class_list.addItems(self.classes)
        if self.classes:
            self.class_list.setCurrentRow(0)
        class_layout.addWidget(self.class_list)

        # 类别编辑
        class_edit_layout = QHBoxLayout()
        self.class_edit = LineEdit()
        self.class_edit.setPlaceholderText("输入新类别")
        self.add_class_btn = PushButton("添加")

        class_edit_layout.addWidget(self.class_edit)
        class_edit_layout.addWidget(self.add_class_btn)
        class_layout.addLayout(class_edit_layout)

        right_layout.addWidget(class_group)

        # 标注列表
        annotation_group = QGroupBox("当前标注")
        annotation_layout = QVBoxLayout(annotation_group)

        self.annotation_list = QListWidget()
        annotation_layout.addWidget(self.annotation_list)

        right_layout.addWidget(annotation_group)

        # 导出设置
        export_group = QGroupBox("导出设置")
        export_layout = QVBoxLayout(export_group)

        self.auto_export_check = CheckBox("自动保存标注")
        self.auto_export_check.setChecked(True)
        export_layout.addWidget(self.auto_export_check)

        self.export_btn = PrimaryPushButton("导出 YOLO 格式")
        export_layout.addWidget(self.export_btn)

        self.advanced_organize_btn = PushButton("高级整理选项")
        export_layout.addWidget(self.advanced_organize_btn)

        right_layout.addWidget(export_group)

        right_layout.addStretch()

        # 添加到主布局
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget)

    def _set_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.load_dataset_btn.clicked.connect(self._load_dataset)
        self.prev_btn.clicked.connect(self._prev_image)
        self.next_btn.clicked.connect(self._next_image)
        self.clear_btn.clicked.connect(self._clear_annotations)
        self.undo_btn.clicked.connect(self._undo_annotation)
        self.add_class_btn.clicked.connect(self._add_class)
        self.export_btn.clicked.connect(self._export_yolo)
        self.apply_size_btn.clicked.connect(self._apply_canvas_size)
        self.advanced_organize_btn.clicked.connect(self._organize_dataset)

        # 画布信号
        self.canvas.bboxDrawn.connect(self._on_bbox_drawn)
        self.canvas.imageLoaded.connect(self._on_image_loaded)

        # 列表信号
        self.class_list.currentTextChanged.connect(self._on_class_selected)
        # 比例选择信号
        self.aspect_combo.currentTextChanged.connect(self._on_aspect_ratio_changed)

    def _on_aspect_ratio_changed(self, ratio_name):
        """比例选择变化"""
        self.canvas.set_aspect_ratio(ratio_name)

        # 如果是自由比例，启用尺寸输入
        is_free_ratio = ratio_name == "自由比例"
        self.width_spin.setEnabled(is_free_ratio)
        self.height_spin.setEnabled(is_free_ratio)

    def _apply_canvas_size(self):
        """应用自定义尺寸"""
        width = self.width_spin.value()
        height = self.height_spin.value()
        self.canvas.set_fixed_size(width, height)

    def _load_dataset(self):
        """加载数据集 - 推荐版本"""
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹", str(PROJECT_ROOT))
        if folder:
            self.dataset_path = Path(folder)
            self.dataset_path_label.setText(str(self.dataset_path))
            # 加载类别
            classes_path = Path(folder) / "classes.txt"
            if classes_path.exists():
                with open(classes_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines is None or len(lines) == 0:
                        return
                    lines = [s.strip() for s in lines]
                    log.debug(f"加载类别 {lines}")
                    self.class_list.clear()
                    self.classes.clear()
                    for line in lines:
                        self.classes.append(line)
                        self.class_list.addItem(line)

            self.load_dataset_btn.setEnabled(False)
            self.load_dataset_btn.setText("加载中...")
            QApplication.processEvents()

            try:
                # 支持的图片格式
                valid_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
                self.image_files = []

                # 扫描目录中的图片文件
                for item in self.dataset_path.iterdir():
                    if item.is_file():
                        # 统一转换为小写比较，避免重复
                        ext = item.suffix.lower()
                        if ext in valid_extensions:
                            self.image_files.append(item)

                # 按文件名排序
                self.image_files.sort(key=lambda x: x.name.lower())
                self.current_index = 0

                log.debug(f"扫描完成，找到 {len(self.image_files)} 个图片文件:")

            except Exception as e:
                log.error(f"扫描图片时出错: {e}")
                self.image_files = []

            finally:
                self.load_dataset_btn.setEnabled(True)
                self.load_dataset_btn.setText("加载图片文件夹")

            if self.image_files:
                self._load_current_image()
                InfoBar.success(title="加载成功", content=f"找到 {len(self.image_files)} 张图片", parent=self)
            else:
                InfoBar.warning(title="警告", content="未找到支持的图片文件 (.jpg, .jpeg, .png, .bmp)", parent=self)

    def _load_current_image(self):
        """加载当前图片"""
        if not self.image_files or self.current_index < 0 or self.current_index >= len(self.image_files):
            return

        # 更新界面状态
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_files) - 1)

        image_path = self.image_files[self.current_index]
        self.current_image_path = image_path

        # 立即更新界面信息
        self.image_info_label.setText(f"当前: {image_path.name}")
        self.progress_label.setText(f"{self.current_index + 1}/{len(self.image_files)}")

        # 强制界面更新
        QApplication.processEvents()

        # 加载图片
        if self.canvas.load_image(image_path):
            # 等待图片完全加载后再加载标注
            QApplication.processEvents()
            self._load_existing_annotations()
        else:
            InfoBar.error(title="错误", content=f"无法加载图片: {image_path.name}", parent=self)

    def _on_image_loaded(self):
        """图片加载完成后的回调"""
        # 可以在这里添加图片加载完成后的额外处理
        pass

    def _load_existing_annotations(self):
        """加载已有的标注文件"""
        if not self.current_image_path:
            return

        # 清空当前标注
        self.canvas.clear_annotations()
        self.annotation_list.clear()

        # 等待画布完全准备好
        if not self.canvas.original_pixmap:
            return

        # 查找对应的 YOLO 标注文件
        txt_path = self.current_image_path.with_suffix(".txt")
        if txt_path.exists():
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    annotation_count = 0

                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) == 5:
                            class_id = int(parts[0])
                            x_center, y_center, width, height = map(float, parts[1:])

                            # 转换为像素坐标
                            img_w = self.canvas.original_pixmap.width()
                            img_h = self.canvas.original_pixmap.height()

                            # 确保坐标在有效范围内
                            x_center = max(0, min(x_center, 1.0))
                            y_center = max(0, min(y_center, 1.0))
                            width = max(0, min(width, 1.0))
                            height = max(0, min(height, 1.0))

                            x1 = int((x_center - width / 2) * img_w)
                            y1 = int((y_center - height / 2) * img_h)
                            x2 = int((x_center + width / 2) * img_w)
                            y2 = int((y_center + height / 2) * img_h)

                            # 确保坐标不超出图片边界
                            x1 = max(0, min(x1, img_w - 1))
                            y1 = max(0, min(y1, img_h - 1))
                            x2 = max(0, min(x2, img_w - 1))
                            y2 = max(0, min(y2, img_h - 1))

                            class_name = self.classes[class_id] if class_id < len(self.classes) else f"class_{class_id}"
                            bbox = [x1, y1, x2, y2, class_name]
                            self.canvas.annotations.append(bbox)
                            self.annotation_list.addItem(f"{class_name}: [{x1}, {y1}, {x2}, {y2}]")
                            annotation_count += 1

                if annotation_count > 0:
                    # 强制更新画布显示
                    self.canvas.update()
                    log.info(f"已加载 {annotation_count} 个标注")

            except Exception as e:
                log.error(f"加载标注文件失败: {e}")

    def _prev_image(self):
        """上一张图片"""
        if self.auto_export_check.isChecked and self.annotation_list.count() > 0:
            self._export_yolo()
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_image()

    def _next_image(self):
        """下一张图片"""
        if self.auto_export_check.isChecked and self.annotation_list.count() > 0:
            self._export_yolo()
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self._load_current_image()

    def _clear_annotations(self):
        """清空所有标注"""
        self.canvas.clear_annotations()
        self.annotation_list.clear()

    def _undo_annotation(self):
        """撤销上一个标注"""
        self.canvas.remove_last_annotation()
        if self.annotation_list.count() > 0:
            self.annotation_list.takeItem(self.annotation_list.count() - 1)

    def _add_class(self):
        """添加新类别"""
        class_name = self.class_edit.text().strip()
        if class_name and class_name not in self.classes:
            self.classes.append(class_name)
            self.class_list.addItem(class_name)
            self.class_edit.clear()

            InfoBar.success(title="成功", content=f"已添加类别: {class_name}", parent=self)

    def _on_class_selected(self, class_name):
        """类别选择变化"""
        if class_name:
            self.canvas.set_current_class(class_name)

    def _on_bbox_drawn(self, bbox, class_name):
        """标注框绘制完成"""
        x1, y1, x2, y2, _ = bbox
        self.annotation_list.addItem(f"{class_name}: [{x1}, {y1}, {x2}, {y2}]")

    def _export_yolo(self):
        """导出为 YOLO 格式"""
        if not hasattr(self, "dataset_path"):
            InfoBar.warning(title="警告", content="请先加载数据集", parent=self)
            return

        # 为数据集中的张图片生成标注
        total_annotations = 0
        for i, image_path in enumerate(self.image_files):
            if i == self.current_index:
                txt_path = image_path.with_suffix(".txt")
                try:
                    with open(txt_path, "w", encoding="utf-8") as f:
                        for bbox in self.canvas.annotations:
                            x1, y1, x2, y2, class_name = bbox

                            # 获取类别 ID
                            if class_name in self.classes:
                                class_id = self.classes.index(class_name)
                            else:
                                # 如果类别不存在，添加到列表
                                self.classes.append(class_name)
                                class_id = len(self.classes) - 1
                                self.class_list.addItem(class_name)

                            # 转换为 YOLO 格式 (归一化坐标)
                            if self.canvas.original_pixmap:
                                img_w = self.canvas.original_pixmap.width()
                                img_h = self.canvas.original_pixmap.height()

                                x_center = ((x1 + x2) / 2) / img_w
                                y_center = ((y1 + y2) / 2) / img_h
                                width = (x2 - x1) / img_w
                                height = (y2 - y1) / img_h

                                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
                                total_annotations += 1

                except Exception as e:
                    log.error(f"导出标注失败 {image_path}: {e}")

        # 保存类别文件
        classes_path = self.dataset_path / "classes.txt"
        try:
            with open(classes_path, "w", encoding="utf-8") as f:
                for class_name in self.classes:
                    f.write(f"{class_name}\n")
        except Exception as e:
            log.error(f"保存类别文件失败: {e}")

        InfoBar.success(title="导出成功", content=f"已导出 {total_annotations} 个标注到 YOLO 格式", parent=self)

    def _organize_dataset(self):
        """整理数据集"""
        if not hasattr(self, "dataset_path"):
            InfoBar.warning(title="警告", content="请先加载数据集", parent=self)
            return

        # 显示配置对话框
        dialog = self._setup_organize_dialog()
        if dialog.exec_() != QDialog.Accepted:
            return

        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", str(self.dataset_path.parent), options=QFileDialog.ShowDirsOnly
        )

        if output_dir:
            # 执行整理
            success = self.organize_yolo_dataset(
                output_dir=output_dir,
                train_ratio=self.train_ratio_spin.value(),
                cleanup_existing=self.cleanup_check.isChecked(),
                filter_annotated=self.filter_check.isChecked(),
            )

    def organize_yolo_dataset(self, output_dir, train_ratio=0.8, cleanup_existing=True, filter_annotated=True):
        """整理为 YOLO 训练集格式 - 增强版本

        Args:
            output_dir: 输出目录
            train_ratio: 训练集比例
            cleanup_existing: 是否清理已存在的输出目录
            filter_annotated: 是否只筛选有标注的图片
        """
        if not hasattr(self, "dataset_path"):
            InfoBar.warning(title="警告", content="请先加载数据集", parent=self)
            return False

        output_path = Path(output_dir)

        # 清理已存在的输出目录
        if cleanup_existing and output_path.exists():
            try:
                shutil.rmtree(output_path)
                log.info(f"已清理现有目录: {output_path}")
            except Exception as e:
                log.error(f"清理目录失败: {e}")
                InfoBar.error(title="错误", content=f"清理目录失败: {e}", parent=self)
                return False

        # 创建标准 YOLO 目录结构
        directories = ["images/train", "images/val", "labels/train", "labels/val"]

        for directory in directories:
            (output_path / directory).mkdir(parents=True, exist_ok=True)

        # 筛选有标注的图片
        annotated_images = []
        for image_path in self.image_files:
            txt_path = image_path.with_suffix(".txt")

            if filter_annotated:
                # 只选择有标注文件的图片
                if txt_path.exists() and txt_path.stat().st_size > 0:
                    annotated_images.append(image_path)
            else:
                # 包含所有图片
                annotated_images.append(image_path)

        if not annotated_images:
            InfoBar.warning(
                title="警告", content="未找到有标注的图片" if filter_annotated else "未找到图片", parent=self
            )
            return False

        # 按文件名排序确保一致性
        annotated_images.sort(key=lambda x: x.name.lower())

        # 分割训练集和验证集
        total_count = len(annotated_images)
        train_count = int(total_count * train_ratio)

        train_images = annotated_images[:train_count]
        val_images = annotated_images[train_count:]

        success_count = 0
        failed_count = 0

        # 处理训练集
        for image_path in train_images:
            if self._copy_image_and_label(image_path, output_path, "train"):
                success_count += 1
            else:
                failed_count += 1

        # 处理验证集
        for image_path in val_images:
            if self._copy_image_and_label(image_path, output_path, "val"):
                success_count += 1
            else:
                failed_count += 1

        # 创建 dataset.yaml 配置文件
        self._create_yolo_config(output_path, output_path.name)

        # 创建类别文件
        self._create_classes_file(output_path)

        # 生成数据集统计信息
        stats = self._generate_dataset_stats(output_path, len(train_images), len(val_images))

        # 显示结果
        if failed_count == 0:
            InfoBar.success(
                title="整理完成",
                content=f"成功整理 {success_count} 个样本 ({len(train_images)}训练/{len(val_images)}验证)\n{stats}",
                parent=self,
            )
        else:
            InfoBar.warning(
                title="部分完成", content=f"成功: {success_count}, 失败: {failed_count}\n{stats}", parent=self
            )

        return failed_count == 0

    def _copy_image_and_label(self, image_path, output_path, split):
        """复制图片和标注文件到指定分割集"""
        try:
            # 复制图片文件
            image_dest = output_path / "images" / split / image_path.name
            shutil.copy2(image_path, image_dest)

            # 复制对应的标注文件
            txt_src = image_path.with_suffix(".txt")
            if txt_src.exists() and txt_src.stat().st_size > 0:
                txt_dest = output_path / "labels" / split / txt_src.name
                shutil.copy2(txt_src, txt_dest)
            else:
                # 如果没有标注文件，创建一个空的
                txt_dest = output_path / "labels" / split / txt_src.name
                txt_dest.touch()

            return True

        except Exception as e:
            log.error(f"复制文件失败 {image_path}: {e}")
            return False

    def _create_classes_file(self, output_path):
        """创建类别文件"""
        classes_file = output_path / "classes.txt"
        try:
            with open(classes_file, "w", encoding="utf-8") as f:
                for class_name in self.classes:
                    f.write(f"{class_name}\n")
            log.info(f"已创建类别文件: {classes_file}")
        except Exception as e:
            log.error(f"创建类别文件失败: {e}")

    def _generate_dataset_stats(self, dataset_path, train_count, val_count):
        """生成数据集统计信息"""
        total_count = train_count + val_count
        train_annotations = 0
        val_annotations = 0

        # 统计训练集标注数量
        train_labels_dir = dataset_path / "labels" / "train"
        if train_labels_dir.exists():
            for txt_file in train_labels_dir.glob("*.txt"):
                if txt_file.stat().st_size > 0:
                    train_annotations += 1

        # 统计验证集标注数量
        val_labels_dir = dataset_path / "labels" / "val"
        if val_labels_dir.exists():
            for txt_file in val_labels_dir.glob("*.txt"):
                if txt_file.stat().st_size > 0:
                    val_annotations += 1

        stats = f"""
    数据集统计:
    - 总样本数: {total_count}
    - 训练集: {train_count} (有标注: {train_annotations})
    - 验证集: {val_count} (有标注: {val_annotations})
    - 类别数: {len(self.classes)}
    - 标注率: {(train_annotations + val_annotations) / total_count * 100:.1f}%
    """
        return stats

    def _create_yolo_config(self, output_path, dataset_name):
        """创建 YOLO 数据集配置文件"""
        # 获取绝对路径
        abs_path = output_path.absolute()

        config_content = f"""# YOLO 数据集配置文件
    # 数据集路径
    path: {abs_path}  # 数据集根目录
    train: images/train  # 训练图片目录
    val: images/val      # 验证图片目录
    test:                # 测试集目录（可选）

    # 类别数量
    nc: {len(self.classes)}

    # 类别名称
    names: {self.classes}

    # 数据集信息
    # 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    # 总类别: {len(self.classes)}
    # 类别列表: {', '.join(self.classes)}
    """

        config_file = output_path / f"{dataset_name}.yaml"
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(config_content)
            log.info(f"已创建配置文件: {config_file}")
        except Exception as e:
            log.error(f"创建配置文件失败: {e}")

    def _setup_organize_dialog(self):
        """创建数据集整理配置对话框"""
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("YOLO 数据集配置")
        dialog.setMinimumWidth(400)

        layout = QFormLayout(dialog)

        # 训练集比例
        self.train_ratio_spin = DoubleSpinBox()
        self.train_ratio_spin.setRange(0.1, 0.9)
        self.train_ratio_spin.setValue(0.8)
        self.train_ratio_spin.setSingleStep(0.1)
        layout.addRow("训练集比例:", self.train_ratio_spin)

        # 清理选项
        self.cleanup_check = CheckBox("清理已存在的输出目录")
        self.cleanup_check.setChecked(True)
        layout.addRow(self.cleanup_check)

        # 筛选选项
        self.filter_check = CheckBox("只导出有标注的图片")
        self.filter_check.setChecked(True)
        layout.addRow(self.filter_check)

        # 统计信息
        total_images = len(self.image_files)
        annotated_images = len([img for img in self.image_files if img.with_suffix(".txt").exists()])

        stats_label = CaptionLabel(
            f"当前数据集: {total_images} 张图片, {annotated_images} 张有标注 ({annotated_images/total_images*100:.1f}%)"
        )
        layout.addRow("统计:", stats_label)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        return dialog
