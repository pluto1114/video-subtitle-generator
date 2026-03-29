# Video Subtitle Generator

一款专业的视频字幕自动生成工具，基于最先进的 AI 语音识别技术。

## 功能特性

- **高效处理**: 一键批量处理视频文件
- **精准识别**: 基于 faster-whisper 的高性能 ASR 引擎
- **多格式支持**: 支持 SRT 和 ASS 两种字幕格式
- **质量模式**: 提供 pro/quality/balanced/speed 四种预设
- **音频增强**: 多种音频增强配置文件
- **VAD 支持**: 语音活动检测优化
- **双界面**: 同时提供 GUI 和 CLI 界面

## 安装

### 基础安装

```bash
pip install -e .
```

### 开发环境安装

```bash
pip install -e ".[dev,gui]"
```

## 使用方法

### CLI 命令行

```bash
# 基本用法
video-subtitle video.mp4

# 指定输出格式
video-subtitle video.mp4 -f ass

# 使用高质量模式
video-subtitle video.mp4 -q pro --audio-enhance strong

# 批量处理
video-subtitle video1.mp4 video2.mp4 video3.mp4 -o ./subtitles

# 使用人声优先模板
video-subtitle video.mp4 -q pro --audio-enhance strong --vad-profile voice_focus
```

### GUI 图形界面

```bash
video-subtitle-gui
```

## 配置选项

### 质量模式

| 模式 | 定位 | 特点 |
|------|------|------|
| `pro` | 专业精修 | 最高识别精度 + 最强后处理 |
| `quality` | 最终成片 | 高质量识别 + 严格去重复 |
| `balanced` | 默认模式 | 质量与速度平衡 |
| `speed` | 快速草稿 | 降低精度，提升速度 |

### 字幕格式

- **SRT**: 简单通用，兼容性最佳
- **ASS**: 功能丰富，支持样式定义

### 音频增强

- `off`: 不进行音频增强
- `voice`: 人声优化（轻度）
- `strong`: 人声强化（重度）

### VAD 配置

- `voice_focus`: 人声优先（高敏感度）
- `balanced`: 平衡模式
- `noise_robust`: 抗噪模式（低敏感度）
- `fast`: 快速模式

## 开发

### 运行测试

```bash
pytest
```

### 运行测试并生成覆盖率报告

```bash
pytest --cov=video_subtitle --cov-report=html
```

### 代码格式化

```bash
black src tests
ruff check src tests
```

## 项目结构

```
video-subtitle-generator/
├── src/
│   └── video_subtitle/
│       ├── __init__.py
│       ├── config.py          # 配置模块
│       ├── asr.py             # ASR 引擎
│       ├── subtitle.py        # 字幕处理
│       ├── audio.py           # 音频处理
│       ├── processor.py       # 主处理器
│       ├── cache.py           # 模型缓存
│       ├── config_manager.py  # 配置持久化
│       ├── cli.py             # 命令行界面
│       └── gui.py             # 图形界面
├── tests/
│   ├── test_config.py
│   ├── test_subtitle.py
│   ├── test_asr.py
│   ├── test_cache.py
│   ├── test_processor.py
│   ├── test_cli.py
│   └── test_audio.py
├── pyproject.toml
└── README.md
```

## 系统要求

- Python 3.9+
- FFmpeg
- CUDA 11.8+ (可选，用于 GPU 加速)

## 依赖

- faster-whisper >= 1.0.0
- torch >= 2.0.0
- numpy >= 1.21.0
- pydantic >= 2.0.0
- customtkinter >= 5.2.0 (GUI)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
