from pathlib import Path
import threading
import time
import cv2
from erchong.config.settings import RESOURCE_DIR
from src.erchong.common.style_sheet import StyleSheet
from enum import IntEnum

import qframelesswindow as qfr
import qfluentwidgets as qf
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from gas.util.hwnd_util import WindowInfo
from gas.util.screenshot_util import screenshot, screenshot_bitblt
from gas.util.img_util import save_img

from src.erchong.utils.logger import get_logger

log = get_logger()


class ScreenshotMode(IntEnum):
    PrintWindow = 0
    Bitblt = 1

    def __str__(self):
        return self.name


class ImageCardWidget(qfr.FramelessWindow):
    """根据hwnd显示窗口"""

    def __init__(self, windows: WindowInfo = None, parent=None):
        super().__init__(parent)

        self.windows = windows
        self.setContentsMargins(10, 20, 10, 10)

        # 添加暂停状态控制
        self.is_paused = False
        self.is_save = False

        self._setup_ui()
        self._set_connections()

        # 启动一个线程专门更新image_label
        self.sereenshot_thread = threading.Thread(target=self.update_frame)
        self.sereenshot_thread.daemon = True
        self.sereenshot_thread.start()

        StyleSheet.IMAGE_CARD_WIDGET.apply(self)

    def _setup_ui(self):
        self.main_layout = qtw.QVBoxLayout()

        # 第一行：截图方式说明 + 选择框 + 暂停/继续按钮
        first_row_layout = qtw.QHBoxLayout()

        # 截图方式说明标签
        self.mode_label = qf.BodyLabel("截图方式:", self)

        # 截图方式选择框
        self.screenshot_mode_combo = qf.ComboBox(self)
        self.screenshot_mode_combo.addItem(ScreenshotMode.PrintWindow.name, userData=ScreenshotMode.PrintWindow)
        self.screenshot_mode_combo.addItem(ScreenshotMode.Bitblt.name, userData=ScreenshotMode.Bitblt)

        # 暂停/继续按钮
        self.pause_button = qf.PushButton("暂停", self)
        self.pause_button.setFixedWidth(100)

        # 获取图像 以供标注训练
        self.capture_btn = qf.PushButton("开始保存图像", self)
        self.capture_btn.setFixedWidth(100)

        first_row_layout.addWidget(self.mode_label)
        first_row_layout.addWidget(self.screenshot_mode_combo)
        first_row_layout.addStretch(1)  # 添加弹性空间
        first_row_layout.addWidget(self.pause_button)
        first_row_layout.addWidget(self.capture_btn)

        # 第二行：状态标签
        self.status_label = qf.BodyLabel(self)
        self.status_label.setWordWrap(True)  # 允许自动换行

        # 图像显示
        self.image_label = qf.ImageLabel(self)
        w, h = self.windows.size
        self.image_label.setFixedSize(w, h)

        # 添加到主布局
        self.main_layout.addLayout(first_row_layout)
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.image_label)
        self.setLayout(self.main_layout)

    def _set_connections(self):
        self.pause_button.clicked.connect(self.toggle_pause)
        self.capture_btn.clicked.connect(self.toggle_save)

    def toggle_pause(self):
        """切换暂停/继续状态"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.setText("继续")
        else:
            self.pause_button.setText("暂停")

    def toggle_save(self):
        """切换暂停/继续状态"""
        self.is_save = not self.is_save
        if self.is_save:
            self.capture_btn.setText("停止保存图像")
        else:
            self.capture_btn.setText("开始保存图像")

    def update_frame(self):
        """更新image_label帧"""
        while True:
            # 如果暂停，等待一段时间后继续检查
            if self.is_paused:
                time.sleep(0.1)
                continue

            old_time = time.time_ns() // 1_000_000  # 当前毫秒
            if not hasattr(self, "last_fps_time"):
                self.last_fps_time = old_time
                self.frame_count = 0
                self.current_fps = 0

            combo_data = self.screenshot_mode_combo.currentData()
            scr = None
            if combo_data == ScreenshotMode.PrintWindow:
                scr = screenshot(self.windows.hwnd)
            elif combo_data == ScreenshotMode.Bitblt:
                scr = screenshot_bitblt(self.windows.hwnd)

            if scr is None:
                time.sleep(1)
                continue

            self.image_label.setImage(self.numpy_array_to_qpixmap(scr))

            # 计算帧数
            self.frame_count += 1
            time_elapsed = old_time - self.last_fps_time
            if time_elapsed > 1000:
                self.current_fps = self.frame_count / (time_elapsed / 1000.0)
                self.frame_count = 0
                self.last_fps_time = old_time

                if self.is_save:
                    # 保存图像
                    window_title = "".join(
                        c for c in self.windows.title if c.isalnum() or c in (" ", "-", "_")
                    ).rstrip()
                    if not window_title:
                        window_title = "templates"

                    try:
                        img_name = f"{self.windows.title}_{int(time.time())}.png"
                        save_path = Path(RESOURCE_DIR) / "screenshot" / window_title
                        save_path.mkdir(parents=True, exist_ok=True)
                        save_img(scr, save_path / img_name)
                    except Exception as e:
                        log.error(e)

            # 使用换行符替换 | 符号
            status_text = f"HWND: {self.windows.hwnd} | Title: {self.windows.title} | Capture method: {combo_data} | FPS: {self.current_fps:.1f}"
            self.status_label.setText(status_text)

            # 控制帧率，避免占用过多CPU
            # time.sleep(0.03)  # 大约30fps

    def numpy_array_to_qpixmap(self, img_array) -> qtg.QPixmap:
        """
        将numpy数组(BGR格式)转换为QPixmap

        Args:
            img_array: numpy数组，BGR格式，形状为 (height, width, 3)

        Returns:
            QPixmap对象
        """
        if img_array is None or img_array.size == 0:
            return None

        try:
            # 获取图像尺寸
            height, width, channel = img_array.shape

            # 确保是3通道图像
            if channel != 3:
                return None

            # 将BGR转换为RGB
            rgb_image = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)

            # 创建QImage
            bytes_per_line = 3 * width
            q_image = qtg.QImage(rgb_image.data, width, height, bytes_per_line, qtg.QImage.Format.Format_RGB888)

            # 转换为QPixmap
            return qtg.QPixmap.fromImage(q_image)

        except Exception as e:
            log.error(f"图像转换失败: {e}")
            return None
