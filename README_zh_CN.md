# 🎬 Video Subtitle Generator

<div align="center">

**一款专业的 AI 视频字幕自动生成工具**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[English](README.md) | [简体中文](README_zh_CN.md)

</div>

---

## 📖 目录

- [简介](#-简介)
- [功能特性](#-功能特性)
- [安装](#-安装)
- [快速开始](#-快速开始)
- [使用方法](#-使用方法)
- [配置说明](#-配置说明)
- [项目结构](#-项目结构)
- [开发指南](#-开发指南)
- [系统要求](#-系统要求)
- [常见问题](#-常见问题)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## ✨ 简介

Video Subtitle Generator 是一款使用先进 AI 语音识别技术为视频自动生成字幕的专业工具。基于最先进的 [faster-whisper](https://github.com/guillaumekln/faster-whisper) 引擎构建，为初学者和专业人士提供高精度的转录和直观的界面。

### 为什么选择这个工具？

- 🚀 **闪电般快速**: GPU 加速处理，性能优化
- 🎯 **高精度**: 采用 Whisper 模型，识别卓越
- 🛠️ **专业功能**: 高级音频增强和 VAD 支持
- 💻 **双界面**: CLI 和 GUI 满足不同工作流
- 🌍 **多语言**: 支持多种语言，自动检测

---

## 🎯 功能特性

### 核心能力

- **⚡ 高效处理**: 一键批量处理多个视频文件
- **🎙️ 先进 ASR 引擎**: 基于 faster-whisper，识别精准
- **📝 多格式支持**: 导出 SRT（通用）或 ASS（带样式字幕）
- **🎨 质量预设**: 四种优化模式（pro、quality、balanced、speed）
- **🔊 音频增强**: 人声优化和降噪配置
- **🎚️ VAD 支持**: 语音活动检测，字幕更干净
- **🖥️ 双界面**: 命令行和图形界面
- **🌐 多语言**: 自动语言检测和支持

### 质量模式

| 模式 | 使用场景 | 描述 |
|------|----------|------|
| `pro` | 专业精修 | 最高识别精度 + 最强后处理 |
| `quality` | 最终成片 | 高质量识别 + 严格去重复 |
| `balanced` | 默认模式 | 质量与速度平衡 |
| `speed` | 快速草稿 | 降低精度，提升速度 |

### 支持格式

- **SRT**: 通用性强，格式简单
- **ASS**: 支持高级样式、定位和特效

---

## 📦 安装

### 前置要求

- **Python 3.9 或更高版本**
- **FFmpeg**（音频提取必需）
- **CUDA 11.8+**（可选，用于 GPU 加速）

### 步骤 1：安装 FFmpeg

**Windows:**
```bash
# 使用 Chocolatey
choco install ffmpeg

# 或从官网下载 https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg
```

### 步骤 2：安装软件包

**基础安装:**
```bash
pip install -e .
```

**开发安装（包含 GUI 和开发工具）:**
```bash
pip install -e ".[dev,gui]"
```

### 步骤 3：验证安装

```bash
# 检查 CLI
video-subtitle --help

# 启动 GUI（如已安装）
video-subtitle-gui
```

---

## 🚀 快速开始

### CLI（命令行界面）

```bash
# 基本用法 - 处理单个视频
video-subtitle video.mp4

# 指定输出格式（SRT 或 ASS）
video-subtitle video.mp4 -f ass

# 使用高质量模式和语音增强
video-subtitle video.mp4 -q pro --audio-enhance strong

# 批量处理多个视频
video-subtitle video1.mp4 video2.mp4 video3.mp4 -o ./subtitles

# 使用人声优先模板（推荐用于对话）
video-subtitle video.mp4 -q pro --audio-enhance strong --vad-profile voice_focus
```

### GUI（图形用户界面）

```bash
# 启动图形界面
video-subtitle-gui
```

GUI 提供：
- 📁 拖拽文件管理
- ⚙️ 可视化配置面板
- ▶️ 实时处理进度
- 📊 分步耗时统计

---

## 📖 使用方法

### 命令行选项

```
video-subtitle <视频文件> [选项]

位置参数:
  video_files          一个或多个要处理的视频文件

选项:
  -h, --help           显示帮助信息并退出
  -f, --format FORMAT  字幕格式：srt, ass（默认：srt）
  -o, --output DIR     输出目录（默认：与视频同目录）
  -q, --quality MODE   质量模式：pro, quality, balanced, speed（默认：balanced）
  --audio-enhance MODE 音频增强：off, voice, strong（默认：off）
  --vad-profile PROFILE VAD 配置：voice_focus, balanced, noise_robust, fast
  --overwrite          覆盖已存在的字幕文件
  --device DEVICE      处理设备：cuda, cpu（默认：自动检测）
  --language LANG      源语言：auto-detect, en, zh, ja, ko 等
  --model MODEL        模型大小：large_v3_turbo, large_v3, medium, small, base, tiny
```

### 使用示例

**1. 使用默认设置处理:**
```bash
video-subtitle my_video.mp4
```

**2. 生成带样式的 ASS 格式:**
```bash
video-subtitle lecture.mp4 -f ass -o ./subtitles
```

**3. 专业用途最高质量:**
```bash
video-subtitle documentary.mp4 -q pro --audio-enhance strong
```

**4. 快速预览快速处理:**
```bash
video-subtitle webinar.mp4 -q speed
```

**5. 处理整个目录:**
```bash
video-subtitle *.mp4 -o ./output
```

---

## ⚙️ 配置说明

### 质量模式详情

| 模式 | 准确率 | 速度 | 适用场景 |
|------|--------|------|----------|
| `pro` | ★★★★★ | ★★☆☆☆ | 专业字幕，最终发布 |
| `quality` | ★★★★☆ | ★★★☆☆ | 高质量制作 |
| `balanced` | ★★★☆☆ | ★★★★☆ | 日常使用（推荐默认） |
| `speed` | ★★☆☆☆ | ★★★★★ | 快速草稿，长视频 |

### 音频增强配置

- **`off`**: 无增强（最快）
- **`voice`**: 人声优化（轻度处理）
- **`strong`**: 强力人声增强（适合嘈杂音频）

### VAD（语音活动检测）配置

- **`voice_focus`**: 高敏感度，优先人声
- **`balanced`**: 标准检测（默认）
- **`noise_robust`**: 低敏感度，过滤背景噪音
- **`fast`**: 快速检测，适合实时处理

### 模型选择

| 模型 | 大小 | 速度 | 准确率 | 显存占用 |
|------|------|------|--------|----------|
| `large_v3_turbo` | 1.5 GB | ⚡⚡⚡ | ★★★★★ | ~8 GB |
| `large_v3` | 3.1 GB | ⚡⚡ | ★★★★★+ | ~12 GB |
| `medium` | 1.5 GB | ⚡⚡⚡ | ★★★★☆ | ~6 GB |
| `small` | 480 MB | ⚡⚡⚡⚡ | ★★★☆☆ | ~3 GB |
| `base` | 140 MB | ⚡⚡⚡⚡⚡ | ★★☆☆☆ | ~1 GB |
| `tiny` | 75 MB | ⚡⚡⚡⚡⚡ | ★☆☆☆☆ | ~500 MB |

**推荐**: 使用 `large_v3_turbo` 获得速度和准确率的最佳平衡。

---

## 📁 项目结构

```
video-subtitle-generator/
├── src/
│   └── video_subtitle/
│       ├── __init__.py           # 包初始化
│       ├── config.py             # 配置定义
│       ├── asr.py                # ASR 引擎封装
│       ├── subtitle.py           # 字幕生成逻辑
│       ├── audio.py              # 音频提取/增强
│       ├── processor.py          # 主处理流程
│       ├── cache.py              # 模型缓存工具
│       ├── config_manager.py     # 配置持久化
│       ├── cli.py                # 命令行界面
│       ├── gui.py                # 图形用户界面
│       ├── i18n.py               # 国际化系统
│       └── locales/
│           ├── en_US.json        # 英文翻译
│           └── zh_CN.json        # 中文翻译
├── tests/
│   ├── test_config.py
│   ├── test_subtitle.py
│   ├── test_asr.py
│   ├── test_audio.py
│   ├── test_processor.py
│   ├── test_cli.py
│   └── test_integration.py
├── docs/                         # 文档
├── pyproject.toml                # 项目配置
├── requirements.txt              # 依赖
├── start.bat                     # Windows 启动器
└── README.md                     # 本文件
```

---

## 👨‍💻 开发指南

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/yourusername/video-subtitle-generator.git
cd video-subtitle-generator

# 创建虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 安装开发依赖
pip install -e ".[dev,gui]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 生成覆盖率报告
pytest --cov=src/video_subtitle --cov-report=html

# 运行特定测试文件
pytest tests/test_asr.py -v
```

### 代码质量

```bash
# 格式化代码
black src tests

# 代码检查
ruff check src tests

# 类型检查
mypy src/video_subtitle
```

### 构建文档

```bash
# 生成 API 文档
# （添加您偏好的文档工具）
```

---

## 💻 系统要求

### 最低要求

- **操作系统**: Windows 10 / macOS 11 / Linux (Ubuntu 20.04+)
- **CPU**: 双核处理器（推荐四核）
- **内存**: 4 GB（推荐 8 GB）
- **存储**: 2 GB 可用空间
- **Python**: 3.9 或更高版本

### GPU 加速推荐配置

- **GPU**: NVIDIA 显卡，4 GB+ 显存
- **CUDA**: 11.8 或更高版本
- **驱动**: 最新 NVIDIA 驱动

### 可选依赖

- **FFmpeg**: 音频提取必需
- **CUDA Toolkit**: GPU 加速（已包含在 PyTorch 中）

---

## ❓ 常见问题

### Q: 为什么处理速度这么慢？

**A:** 处理速度取决于多个因素：
- **硬件**: GPU 加速可提供 10-50 倍提速
- **模型大小**: 较小模型（tiny、base）更快
- **视频长度**: 长视频自然需要更多时间
- **质量模式**: `speed` 模式明显更快

**解决方案:**
1. 启用 GPU 加速（确保已安装 CUDA）
2. 使用较小模型：`--model base`
3. 切换到 speed 模式：`-q speed`

### Q: 模型下载失败怎么办？

**A:** 这是常见的网络问题。尝试以下解决方案：

**方案 1：手动下载**
```bash
# 从 Hugging Face 下载
# https://huggingface.co/guillaumekln/faster-whisper-large-v3-turbo

# 放置到缓存目录：
# Windows: C:\Users\<用户>\.cache\huggingface\hub\
# macOS/Linux: ~/.cache/huggingface/hub/
```

**方案 2：使用镜像**
```bash
# 设置 HF_ENDPOINT 环境变量
export HF_ENDPOINT=https://hf-mirror.com
```

### Q: 转录准确率如何？

**A:** 准确率因语言和音频质量而异：
- **英文**: ~95%+（使用 `large_v3_turbo`）
- **中文**: ~90%+（设置正确语言）
- **其他语言**: 85-95% 取决于训练数据

获得最佳结果：
1. 使用 `pro` 或 `quality` 模式
2. 对嘈杂音源启用音频增强
3. 如自动检测失败，指定正确语言

### Q: 可以自定义字幕样式吗？

**A:** 可以，使用 ASS 格式时：
- 在文本编辑器中编辑生成的 `.ass` 文件
- 修改 `[V4+ Styles]` 部分
- 使用 Aegisub 等工具进行高级样式设计

### Q: 支持实时处理吗？

**A:** 目前设计为批量处理。实时处理功能计划在 future 版本中实现。

---

## 🤝 贡献指南

我们欢迎社区贡献！以下是您可以帮助的方式：

### 贡献方式

- 🐛 **报告 Bug**: 提交包含复现步骤的 Issue
- 💡 **建议功能**: 分享您的改进想法
- 📝 **修正拼写**: 更正文档或注释
- 🔧 **提交 PR**: 实现功能或修复 Bug
- 🌍 **翻译**: 帮助本地化应用

### 贡献流程

1. **Fork** 仓库
2. **创建** 功能分支（`git checkout -b feature/amazing-feature`）
3. **提交** 更改（`git commit -m 'Add amazing feature'`）
4. **推送** 到分支（`git push origin feature/amazing-feature`）
5. **打开** Pull Request

### 开发标准

- 遵循 PEP 8 代码风格指南
- 为新功能编写测试
- 文档化公共 API
- 保持提交原子化并描述清晰

---

## 📄 许可证

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件。

### 许可说明

- ✅ 可用于个人和商业项目
- ✅ 可修改和分发
- ✅ 不提供担保
- ✅ 分发时需包含许可证声明

---

## 🙏 致谢

- **[faster-whisper](https://github.com/guillaumekln/faster-whisper)**: 高性能 Whisper 推理
- **[OpenAI Whisper](https://github.com/openai/whisper)**: 革命性的语音识别模型
- **[FFmpeg](https://ffmpeg.org/)**: 多媒体处理工具包
- **所有贡献者**: 感谢您的支持！

---

## 📬 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/video-subtitle-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/video-subtitle-generator/discussions)
- **Email**: tech@example.com

---

<div align="center">

**Video Subtitle Generator Team 用心制作 ❤️**

⭐ 如果您觉得这个项目有帮助，请给个星标！

</div>
