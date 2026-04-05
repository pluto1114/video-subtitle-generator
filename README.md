# 🎬 Video Subtitle Generator

<div align="center">

**A professional AI-powered video subtitle generation tool**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[English](README.md) | [简体中文](README_zh_CN.md)

</div>

---

## 📖 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [System Requirements](#-system-requirements)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Introduction

Video Subtitle Generator is a professional tool for automatically generating subtitles for videos using advanced AI speech recognition technology. Built on the state-of-the-art [faster-whisper](https://github.com/guillaumekln/faster-whisper) engine, it provides high-accuracy transcription with an intuitive interface for both beginners and professionals.

### Why Choose This Tool?

- 🚀 **Lightning Fast**: GPU-accelerated processing with optimized performance
- 🎯 **High Accuracy**: Powered by Whisper models for superior recognition
- 🛠️ **Professional Features**: Advanced audio enhancement and VAD support
- 💻 **Dual Interface**: Both CLI and GUI for different workflows
- 🌍 **Multilingual**: Supports multiple languages with auto-detection

---

## 🎯 Features

### Core Capabilities

- **⚡ High-Efficiency Processing**: Batch process multiple video files with a single command
- **🎙️ Advanced ASR Engine**: Powered by faster-whisper for exceptional accuracy
- **📝 Multiple Formats**: Export to SRT (universal) or ASS (styled subtitles)
- **🎨 Quality Presets**: Four optimization modes (pro, quality, balanced, speed)
- **🔊 Audio Enhancement**: Voice optimization and noise reduction profiles
- **🎚️ VAD Support**: Voice Activity Detection for cleaner subtitles
- **🖥️ Dual Interface**: Command-line and graphical interfaces
- **🌐 Multi-language**: Automatic language detection and support

### Quality Modes

| Mode | Use Case | Description |
|------|----------|-------------|
| `pro` | Professional Editing | Highest accuracy + advanced post-processing |
| `quality` | Final Production | High-quality recognition + strict deduplication |
| `balanced` | Default | Optimal balance between quality and speed |
| `speed` | Quick Drafts | Faster processing with acceptable accuracy |

### Supported Formats

- **SRT**: Universal compatibility, simple format
- **ASS**: Advanced styling, positioning, and effects

---

## 📦 Installation

### Prerequisites

- **Python 3.9 or higher**
- **FFmpeg** (required for audio extraction)
- **CUDA 11.8+** (optional, for GPU acceleration)

### Step 1: Install FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
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

### Step 2: Install the Package

**Basic Installation:**
```bash
pip install -e .
```

**Development Installation (includes GUI and dev tools):**
```bash
pip install -e ".[dev,gui]"
```

### Step 3: Verify Installation

```bash
# Check CLI
video-subtitle --help

# Launch GUI (if installed)
video-subtitle-gui
```

---

## 🚀 Quick Start

### CLI (Command Line Interface)

```bash
# Basic usage - process a single video
video-subtitle video.mp4

# Specify output format (SRT or ASS)
video-subtitle video.mp4 -f ass

# Use high-quality mode with voice enhancement
video-subtitle video.mp4 -q pro --audio-enhance strong

# Batch process multiple videos
video-subtitle video1.mp4 video2.mp4 video3.mp4 -o ./subtitles

# Use voice priority template (recommended for dialogue)
video-subtitle video.mp4 -q pro --audio-enhance strong --vad-profile voice_focus
```

### GUI (Graphical User Interface)

```bash
# Launch the graphical interface
video-subtitle-gui
```

The GUI provides:
- 📁 Drag-and-drop file management
- ⚙️ Visual configuration panel
- ▶️ Real-time processing progress
- 📊 Step-by-step timing statistics

---

## 📖 Usage

### Command Line Options

```
video-subtitle <video_files> [options]

Positional Arguments:
  video_files          One or more video files to process

Options:
  -h, --help           Show help message and exit
  -f, --format FORMAT  Subtitle format: srt, ass (default: srt)
  -o, --output DIR     Output directory (default: same as video)
  -q, --quality MODE   Quality mode: pro, quality, balanced, speed (default: balanced)
  --audio-enhance MODE Audio enhancement: off, voice, strong (default: off)
  --vad-profile PROFILE VAD profile: voice_focus, balanced, noise_robust, fast
  --overwrite          Overwrite existing subtitle files
  --device DEVICE      Processing device: cuda, cpu (default: auto-detect)
  --language LANG      Source language: auto-detect, en, zh, ja, ko, etc.
  --model MODEL        Model size: large_v3_turbo, large_v3, medium, small, base, tiny
```

### Examples

**1. Process with default settings:**
```bash
video-subtitle my_video.mp4
```

**2. Generate ASS format with styling:**
```bash
video-subtitle lecture.mp4 -f ass -o ./subtitles
```

**3. Maximum quality for professional use:**
```bash
video-subtitle documentary.mp4 -q pro --audio-enhance strong
```

**4. Fast processing for quick preview:**
```bash
video-subtitle webinar.mp4 -q speed
```

**5. Process entire directory:**
```bash
video-subtitle *.mp4 -o ./output
```

---

## ⚙️ Configuration

### Quality Mode Details

| Mode | Accuracy | Speed | Best For |
|------|----------|-------|----------|
| `pro` | ★★★★★ | ★★☆☆☆ | Professional subtitles, final releases |
| `quality` | ★★★★☆ | ★★★☆☆ | High-quality productions |
| `balanced` | ★★★☆☆ | ★★★★☆ | General use (recommended default) |
| `speed` | ★★☆☆☆ | ★★★★★ | Quick drafts, long videos |

### Audio Enhancement Profiles

- **`off`**: No enhancement (fastest)
- **`voice`**: Voice optimization (light processing)
- **`strong`**: Aggressive voice enhancement (best for noisy audio)

### VAD (Voice Activity Detection) Profiles

- **`voice_focus`**: High sensitivity, prioritizes human voice
- **`balanced`**: Standard detection (default)
- **`noise_robust`**: Low sensitivity, filters background noise
- **`fast`**: Quick detection for real-time processing

### Model Selection

| Model | Size | Speed | Accuracy | VRAM Usage |
|-------|------|-------|----------|------------|
| `large_v3_turbo` | 1.5 GB | ⚡⚡⚡ | ★★★★★ | ~8 GB |
| `large_v3` | 3.1 GB | ⚡⚡ | ★★★★★+ | ~12 GB |
| `medium` | 1.5 GB | ⚡⚡⚡ | ★★★★☆ | ~6 GB |
| `small` | 480 MB | ⚡⚡⚡⚡ | ★★★☆☆ | ~3 GB |
| `base` | 140 MB | ⚡⚡⚡⚡⚡ | ★★☆☆☆ | ~1 GB |
| `tiny` | 75 MB | ⚡⚡⚡⚡⚡ | ★☆☆☆☆ | ~500 MB |

**Recommendation**: Use `large_v3_turbo` for the best balance of speed and accuracy.

---

## 📁 Project Structure

```
video-subtitle-generator/
├── src/
│   └── video_subtitle/
│       ├── __init__.py           # Package initialization
│       ├── config.py             # Configuration definitions
│       ├── asr.py                # ASR engine wrapper
│       ├── subtitle.py           # Subtitle generation logic
│       ├── audio.py              # Audio extraction/enhancement
│       ├── processor.py          # Main processing pipeline
│       ├── cache.py              # Model caching utilities
│       ├── config_manager.py     # Configuration persistence
│       ├── cli.py                # Command-line interface
│       ├── gui.py                # Graphical user interface
│       ├── i18n.py               # Internationalization system
│       └── locales/
│           ├── en_US.json        # English translations
│           └── zh_CN.json        # Chinese translations
├── tests/
│   ├── test_config.py
│   ├── test_subtitle.py
│   ├── test_asr.py
│   ├── test_audio.py
│   ├── test_processor.py
│   ├── test_cli.py
│   └── test_integration.py
├── docs/                         # Documentation
├── pyproject.toml                # Project configuration
├── requirements.txt              # Dependencies
├── start.bat                     # Windows launcher
└── README.md                     # This file
```

---

## 👨‍💻 Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/video-subtitle-generator.git
cd video-subtitle-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,gui]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/video_subtitle --cov-report=html

# Run specific test file
pytest tests/test_asr.py -v
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src/video_subtitle
```

### Building Documentation

```bash
# Generate API documentation
# (Add your preferred documentation tool here)
```

---

## 💻 System Requirements

### Minimum Requirements

- **OS**: Windows 10 / macOS 11 / Linux (Ubuntu 20.04+)
- **CPU**: Dual-core processor (Quad-core recommended)
- **RAM**: 4 GB (8 GB recommended)
- **Storage**: 2 GB free space
- **Python**: 3.9 or higher

### Recommended for GPU Acceleration

- **GPU**: NVIDIA GPU with 4 GB+ VRAM
- **CUDA**: 11.8 or higher
- **Driver**: Latest NVIDIA driver

### Optional Dependencies

- **FFmpeg**: Required for audio extraction
- **CUDA Toolkit**: For GPU acceleration (included with PyTorch)

---

## ❓ FAQ

### Q: Why is processing so slow?

**A:** Processing speed depends on several factors:
- **Hardware**: GPU acceleration provides 10-50x speedup
- **Model size**: Smaller models (tiny, base) are faster
- **Video length**: Longer videos naturally take more time
- **Quality mode**: `speed` mode is significantly faster

**Solutions:**
1. Enable GPU acceleration (ensure CUDA is installed)
2. Use a smaller model: `--model base`
3. Switch to speed mode: `-q speed`

### Q: The model download fails. What should I do?

**A:** This is a common network issue. Try these solutions:

**Option 1: Manual Download**
```bash
# Download from Hugging Face
# https://huggingface.co/guillaumekln/faster-whisper-large-v3-turbo

# Place in cache directory:
# Windows: C:\Users\<user>\.cache\huggingface\hub\
# macOS/Linux: ~/.cache/huggingface/hub/
```

**Option 2: Use Mirror**
```bash
# Set HF_ENDPOINT environment variable
export HF_ENDPOINT=https://hf-mirror.com
```

### Q: How accurate is the transcription?

**A:** Accuracy varies by language and audio quality:
- **English**: ~95%+ with `large_v3_turbo`
- **Chinese**: ~90%+ with proper language setting
- **Other languages**: 85-95% depending on training data

For best results:
1. Use `pro` or `quality` mode
2. Enable audio enhancement for noisy sources
3. Specify the correct language if auto-detection fails

### Q: Can I customize the subtitle style?

**A:** Yes, when using ASS format:
- Edit the generated `.ass` file in a text editor
- Modify the `[V4+ Styles]` section
- Use tools like Aegisub for advanced styling

### Q: Does it support real-time processing?

**A:** Currently, it's designed for batch processing. Real-time processing is planned for future releases.

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Report Bugs**: Submit issues with reproduction steps
- 💡 **Suggest Features**: Share your ideas for improvements
- 📝 **Fix Typos**: Correct documentation or comments
- 🔧 **Submit PRs**: Implement features or fix bugs
- 🌍 **Translations**: Help localize the application

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Standards

- Follow PEP 8 style guidelines
- Write tests for new features
- Document public APIs
- Keep commits atomic and well-described

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### What This Means

- ✅ Free to use for personal and commercial projects
- ✅ Modify and distribute
- ✅ No warranty provided
- ✅ Include license notice in distributions

---

## 🙏 Acknowledgments

- **[faster-whisper](https://github.com/guillaumekln/faster-whisper)**: High-performance Whisper inference
- **[OpenAI Whisper](https://github.com/openai/whisper)**: Revolutionary speech recognition model
- **[FFmpeg](https://ffmpeg.org/)**: Multimedia processing toolkit
- **All Contributors**: Thank you for your support!

---

## 📬 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/video-subtitle-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/video-subtitle-generator/discussions)
- **Email**: tech@example.com

---

<div align="center">

**Made with ❤️ by the Video Subtitle Generator Team**

⭐ If you find this project helpful, please give it a star!

</div>
