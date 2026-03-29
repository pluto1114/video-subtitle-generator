# GPU 要求和依赖配置

## 硬件要求

本应用**仅支持 GPU 加速**，需要以下硬件：

- **NVIDIA 显卡**：支持 CUDA 的 NVIDIA GPU
- **CUDA 驱动**：已安装正确的 NVIDIA CUDA 驱动程序

## 软件依赖

### 核心依赖

```
numpy>=1.26.0,<2.0.0
torch>=2.5.0
torchaudio>=2.5.0
ctranslate2>=4.0.0
faster-whisper>=1.0.0
```

### 版本兼容性

已验证的兼容版本组合：
- NumPy: 1.26.4
- PyTorch: 2.6.0
- ctranslate2: 4.7.1
- faster-whisper: 1.2.1

## 已知问题和解决方案

### NumPy 警告：`_ARRAY_API not found`

**问题描述**：
```
UserWarning: Failed to initialize NumPy: _ARRAY_API not found
```

这是 NumPy 和 PyTorch 之间的兼容性警告，不会影响功能。代码中已经在导入相关库之前设置了警告过滤：

```python
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*_ARRAY_API.*")
    warnings.filterwarnings("ignore", message=".*Failed to initialize NumPy.*")
    
    import numpy as np
    import torch
    from faster_whisper import WhisperModel
```

这样确保在导入 `torch` 时就不会显示该警告。

### GPU 不可用错误

如果看到以下错误：
```
RuntimeError: GPU 不可用。本应用仅支持 GPU 加速，请确保:
1. 已安装 NVIDIA 显卡
2. 已安装正确的 CUDA 驱动
3. 已安装支持 GPU 的 PyTorch 版本
```

**解决方案**：
1. 确认系统有 NVIDIA 显卡
2. 更新 NVIDIA 驱动程序
3. 重新安装支持 GPU 的 PyTorch：
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

### 设备验证

应用会在初始化时验证设备设置，如果尝试使用非 CUDA 设备，会抛出错误：
```
ValueError: 本应用仅支持 GPU 加速，请确保设备设置为 'cuda'
```

## 安装说明

### 重要提示

**必须安装 GPU 版本的 PyTorch！** 默认的 `pip install torch` 会安装 CPU 版本。

### 完整安装

```bash
# 1. 先安装 NumPy (确保版本 <2.0)
pip install "numpy<2.0"

# 2. 安装 GPU 版本的 PyTorch (CUDA 12.1)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. 安装其他依赖
pip install ctranslate2 faster-whisper av tqdm pyyaml

# 或者使用 requirements.txt (但不包括 torch，需要手动安装)
pip install -r requirements.txt
```

### 验证 GPU 支持

```bash
# 验证 PyTorch CUDA 支持
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# 应该输出：CUDA available: True
```

### 验证安装

```bash
python -c "import sys; sys.path.insert(0, 'src'); from video_subtitle.asr import FasterWhisperEngine; engine = FasterWhisperEngine(device='cuda'); print('GPU 支持验证成功')"
```

## 故障排除

### 检查 CUDA 状态

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

### 重新安装依赖

如果遇到问题，尝试重新安装：

```bash
pip uninstall torch torchaudio ctranslate2 faster-whisper numpy
pip install -r requirements.txt
```
