# 项目结构说明

## 重构后的项目结构

```
erchong/
├── src/                          # 源代码目录
│   └── erchong/                  # 主包
│       ├── __init__.py           # 包初始化
│       ├── app.py                # 应用入口和配置
│       ├── config/               # 配置模块
│       │   ├── __init__.py
│       │   └── settings.py       # 应用配置常量
│       ├── utils/                 # 工具函数模块
│       │   ├── __init__.py
│       │   └── platform.py       # 平台相关工具
│       ├── widgets/               # UI 组件
│       │   ├── __init__.py
│       │   ├── home_widget.py           # 主页组件
│       │   ├── gallery_card_widget.py   # 画廊卡片组件
│       │   ├── image_card_widget.py     # 图片卡片窗口
│       │   └── settings_widget.py       # 设置页面组件
│       └── windows/               # 窗口类
│           ├── __init__.py
│           └── main_window.py    # 主窗口
├── resource/                     # 资源文件目录
│   ├── shoko1.jpg
│   ├── shoko2.jpg
│   ├── shoko3.jpg
│   └── shoko4.jpg
├── logs/                         # 日志文件目录
├── main.py                       # 应用入口点
├── pyproject.toml                # 项目配置
├── pyrightconfig.json            # 类型检查配置
├── logging_config.json           # 日志配置
├── README.md                     # 项目说明
└── .gitignore                    # Git 忽略文件
```

## 模块说明

### `src/erchong/app.py`
应用入口点，负责创建和配置 QApplication。

### `src/erchong/config/settings.py`
存放应用配置常量，如窗口大小、标题、资源路径等。

### `src/erchong/utils/platform.py`
平台相关工具函数，如检测 Windows 11。

### `src/erchong/widgets/`
所有 UI 组件的集合：
- `home_widget.py`: 主页组件
- `gallery_card_widget.py`: 画廊卡片组件
- `image_card_widget.py`: 图片查看窗口（包含截图功能）
- `settings_widget.py`: 设置页面组件

### `src/erchong/windows/main_window.py`
主窗口类，负责窗口布局和导航。

## 导入路径

重构后，所有导入都使用相对路径：

```python
# 从配置模块导入
from ..config.settings import RESOURCE_DIR

# 从工具模块导入
from ..utils.platform import is_win11

# 从组件模块导入
from .image_card_widget import ImageCardWidget
```

## 运行方式

1. 直接运行：
   ```bash
   python main.py
   ```

2. 使用 uv：
   ```bash
   uv run erchong
   ```

3. 作为模块运行：
   ```bash
   python -m src.erchong.app
   ```

