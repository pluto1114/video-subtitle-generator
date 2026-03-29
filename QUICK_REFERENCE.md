# Video Subtitle Generator 快速参考指南

## 安装

```bash
# 基础安装
pip install -e .

# 包含 GUI 和开发工具
pip install -e ".[dev,gui]"
```

## 快速开始

### CLI 命令行

```bash
# 生成 SRT 字幕（默认）
video-subtitle my_video.mp4

# 生成 ASS 字幕
video-subtitle my_video.mp4 -f ass

# 使用高质量模式
video-subtitle my_video.mp4 -q pro

# 人声优先模板（推荐用于复杂音频）
video-subtitle my_video.mp4 -q pro --audio-enhance strong --vad-profile voice_focus

# 批量处理
video-subtitle *.mp4 -o ./subtitles

# 指定模型和语言
video-subtitle my_video.mp4 -m large-v3-turbo -l zh
```

### GUI 图形界面

```bash
video-subtitle-gui
```

### Python API

```python
from video_subtitle import (
    Config,
    QualityMode,
    AudioEnhanceProfile,
    VADProfile,
    SubtitleFormat,
    VideoProcessor
)

# 创建配置
config = Config(
    quality_mode=QualityMode.PRO,
    audio_enhance_profile=AudioEnhanceProfile.STRONG,
    vad_profile=VADProfile.VOICE_FOCUS,
    subtitle_format=SubtitleFormat.ASS,
)

# 或使用预设模板
config = Config.voice_priority_template()

# 处理视频
processor = VideoProcessor(config)
subtitle = processor.process_video("my_video.mp4")

# 保存字幕
processor.save_subtitle(subtitle, "./output", SubtitleFormat.SRT)
```

## 配置选项

### 质量模式 (`-q`)

| 模式 | 适用场景 | 特点 |
|------|---------|------|
| `pro` | 专业精修 | 最高精度 + 最强后处理 |
| `quality` | 最终成片 | 高质量 + 严格去重 |
| `balanced` | 日常使用 | 质量与速度平衡 |
| `speed` | 快速草稿 | 速度优先 |

### 字幕格式 (`-f`)

| 格式 | 特点 | 适用场景 |
|------|------|---------|
| `srt` | 简单通用 | 大多数播放器 |
| `ass` | 样式丰富 | 需要自定义样式 |

### 音频增强 (`--audio-enhance`)

| 配置 | 效果 | 适用场景 |
|------|------|---------|
| `off` | 无增强 | 清晰音频 |
| `voice` | 轻度优化 | 一般音频 |
| `strong` | 强化处理 | 嘈杂音频 |

### VAD 配置 (`--vad-profile`)

| 配置 | 敏感度 | 适用场景 |
|------|-------|---------|
| `voice_focus` | 高 | 人声检测 |
| `balanced` | 中 | 一般场景 |
| `noise_robust` | 低 | 高噪音环境 |
| `fast` | 快速 | 速度优先 |

## 常用命令组合

### 场景 1: YouTube 视频字幕
```bash
video-subtitle video.mp4 -q balanced -f srt
```

### 场景 2: 电影/电视剧字幕
```bash
video-subtitle episode.mp4 -q pro -f ass --audio-enhance voice
```

### 场景 3: 嘈杂环境录音
```bash
video-subtitle recording.mp4 -q pro --audio-enhance strong --vad-profile voice_focus
```

### 场景 4: 快速预览字幕
```bash
video-subtitle video.mp4 -q speed --no-vad
```

### 场景 5: 批量处理多个视频
```bash
video-subtitle *.mp4 -o ./subtitles -f srt -q balanced
```

### 场景 6: 最大对话捕获模式 (推荐用于动漫/日剧)
```bash
video-subtitle video.mp4 --no-vad --audio-enhance off
# 可生成 300+ 个有效对话片段
```

## 输出示例

### SRT 格式
```srt
1
00:00:00,000 --> 00:00:03,000
Hello, welcome to our video

2
00:00:03,000 --> 00:00:06,000
Today we will learn about AI
```

### ASS 格式
```ass
[Script Info]
Title: Video Subtitle
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, ...
Style: Default,Arial,48,&H00FFFFFF,...

[Events]
Format: Layer, Start, End, Style, Name, MarginL, ...
Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,Hello, welcome to our video
```

## 配置文件

### 保存配置
```bash
video-subtitle video.mp4 -q pro -f ass --save-config
```

### 加载配置
```bash
video-subtitle video.mp4 --load-config /path/to/config.json
```

### 配置文件位置
- Windows: `C:\Users\<用户名>\.video_subtitle\default_config.json`
- Linux/Mac: `~/.video_subtitle/default_config.json`

## 故障排除

### 问题：FFmpeg 未找到
```bash
# Windows: 安装 FFmpeg 并添加到 PATH
# Linux: sudo apt install ffmpeg
# Mac: brew install ffmpeg
```

### 问题：CUDA 不可用
```bash
# 使用 CPU 模式（较慢）
video-subtitle video.mp4 --device cpu
```

### 问题：模型下载失败
```bash
# 使用本地模型
video-subtitle video.mp4 -m /path/to/local/model
```

## 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_subtitle.py -v

# 生成覆盖率报告
pytest --cov=video_subtitle --cov-report=html
```

## 性能提示

1. **使用 GPU 加速**: 确保 CUDA 正确配置
2. **选择合适模型**: `large-v3-turbo` 速度与质量平衡
3. **批量处理**: 一次处理多个视频更高效
4. **模型缓存**: 相同配置的模型只加载一次

## 支持的格式

### 输入视频
- MP4, MKV, AVI, MOV, WMV, FLV, WebM

### 输出字幕
- SRT (SubRip)
- ASS (Advanced Substation Alpha)

### 支持语言
- 自动检测 (auto)
- 中文 (zh)
- 英语 (en)
- 日语 (ja)
- 西班牙语 (es)
- 法语 (fr)
- 俄语 (ru)
- 德语 (de)
- 意大利语 (it)
- 葡萄牙语 (pt)

## 获取帮助

```bash
# CLI 帮助
video-subtitle --help

# 查看版本
video-subtitle --version
```

## 项目链接

- 源代码：`d:\AI-dev\video-subtitle-generator`
- 文档：`README.md`
- 实现总结：`IMPLEMENTATION_SUMMARY.md`
- 需求文档：`reqiurement-document.md`
