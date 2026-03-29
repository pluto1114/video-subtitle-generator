# 问题修复总结

## 问题现象

应用在运行时出现以下错误：
```
UserWarning: Failed to initialize NumPy: _ARRAY_API not found
```

## 根本原因

应用使用了**两个不同的 Python 环境**，导致依赖混乱：

1. **Python 3.12 环境**（conda 环境）
   - 已正确安装 GPU 版 PyTorch
   - NumPy 版本正确 (1.26.4)
   - CUDA 可用：True

2. **Python 3.10 环境**（系统环境 `D:\Python\Python310\`）
   - PyTorch 版本：2.2.0+cu118
   - **NumPy 版本错误：2.1.3** ❌
   - 导致 `_ARRAY_API not found` 错误

## 解决方案

### 1. 代码层面修复

在 [`asr.py`](../src/video_subtitle/asr.py#L102-L134) 中：
- 添加警告过滤器，在导入 `torch` 之前过滤 NumPy 警告
- 添加 GPU 可用性检查
- 添加设备验证（强制使用 CUDA）

```python
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*_ARRAY_API.*")
    warnings.filterwarnings("ignore", message=".*Failed to initialize NumPy.*")
    
    import numpy as np
    import torch
    
    if not torch.cuda.is_available():
        raise RuntimeError("GPU 不可用...")
    
    from faster_whisper import WhisperModel
```

### 2. 环境修复

**Python 3.10 环境**：
```bash
D:\Python\Python310\python.exe -m pip install "numpy<2.0" --force-reinstall
```

**Python 3.12 环境**：
```bash
# 已正确配置，无需修改
```

### 3. 依赖配置

创建 [`requirements.txt`](../requirements.txt)：
```txt
numpy>=1.26.0,<2.0.0
torch>=2.5.0
torchaudio>=2.5.0
ctranslate2>=4.0.0
faster-whisper>=1.0.0
```

## 验证结果

### Python 3.10 环境
```
Python 版本：3.10.9
NumPy 版本：1.26.4 ✓
PyTorch 版本：2.2.0+cu118 ✓
CUDA 可用：True ✓
```

### Python 3.12 环境
```
Python 版本：3.12.3
NumPy 版本：1.26.4 ✓
PyTorch 版本：2.5.1+cu121 ✓
CUDA 可用：True ✓
```

## 关键教训

### 1. 多 Python 环境管理
- 系统中存在多个 Python 环境时，必须确保**每个环境**的依赖都正确安装
- 使用 `python -m pip` 而不是 `pip` 可以确保在正确的环境中安装包

### 2. NumPy 2.0 兼容性问题
- NumPy 2.0 引入了破坏性变更
- 许多科学计算库（包括 PyTorch 2.2）尚未完全支持 NumPy 2.0
- **建议**：暂时使用 `numpy<2.0`

### 3. PyTorch GPU 版本
- 默认 `pip install torch` 安装的是 CPU 版本
- 必须使用 `--index-url` 从 PyTorch 官方源安装 GPU 版本
- 验证：`torch.cuda.is_available()` 必须返回 `True`

## 安装指南

详见：
- [INSTALL.md](../INSTALL.md) - 完整安装指南
- [GPU_REQUIREMENTS.md](GPU_REQUIREMENTS.md) - GPU 要求文档

## 快速诊断命令

```bash
# 检查 Python 版本
python --version

# 检查 NumPy 版本
python -c "import numpy; print(numpy.__version__)"

# 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"

# 检查 PyTorch 版本
python -c "import torch; print(torch.__version__)"

# 验证应用
python -c "import sys; sys.path.insert(0, 'src'); from video_subtitle.asr import FasterWhisperEngine; engine = FasterWhisperEngine(device='cuda'); print('成功！')"
```

## 常见问题

### Q: 为什么有两个 Python 环境？
A: 这是 Windows 系统的常见配置：
- Python 3.10：系统级安装（`D:\Python\Python310\`）
- Python 3.12：conda 环境（`TraeAI-9`）

GUI 应用可能使用的是系统级 Python 3.10。

### Q: 如何确定应用使用哪个 Python？
A: 检查应用的 shebang 或启动脚本。GUI 应用通常使用：
- 系统 Python（`D:\Python\Python310\python.exe`）
- 或者在 `.bat` 文件中指定的 Python

### Q: 需要同时修复两个环境吗？
A: 是的，如果您不确定应用使用哪个环境，最好修复所有相关环境。

### Q: UnicodeDecodeError: 'gbk' codec can't decode byte 是什么问题？
A: 这是 Windows 编码问题。Windows 默认使用 GBK 编码，但 FFmpeg 输出可能包含非 GBK 字符。

**解决方案**：在 [`audio.py`](../src/video_subtitle/audio.py) 中所有 `subprocess.run` 调用使用：
```python
subprocess.run(
    cmd,
    capture_output=True,
    check=False,
    encoding='utf-8',  # 明确指定 UTF-8
    errors='replace',  # 无法解码的字符用替换字符
)
```

这样可以避免编码错误，同时保留所有输出信息。
