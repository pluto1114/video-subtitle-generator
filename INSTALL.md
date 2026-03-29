# 安装指南

## 快速开始

本应用**仅支持 GPU 加速**，请确保您的系统满足以下要求：

- NVIDIA 显卡（支持 CUDA）
- NVIDIA CUDA 驱动程序（已更新）
- Python 3.10+（推荐 3.10 或 3.12）

### 重要提示

如果您有多个 Python 环境，请确保在**正确的环境中安装依赖**。

例如：
- Python 3.10: `D:\Python\Python310\python.exe`
- Python 3.12: 通过 conda 或其他管理器安装

**使用对应的 pip 安装**：
```bash
# Python 3.10
D:\Python\Python310\python.exe -m pip install ...

# Python 3.12
python -m pip install ...  # 或 conda install ...
```

## 安装步骤

### 步骤 1：验证 GPU 支持

首先验证您的系统是否支持 CUDA：

```bash
nvidia-smi
```

应该看到类似输出：
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI ...
|-------------------------------+----------------------+----------------------+
| CUDA Version: 12.4            |
+-------------------------------+----------------------+----------------------+
```

### 步骤 2：安装 NumPy

安装兼容的 NumPy 版本（必须 <2.0）：

```bash
pip install "numpy<2.0"
```

### 步骤 3：安装 PyTorch GPU 版本

**重要**：不要使用默认的 `pip install torch`，这会安装 CPU 版本！

根据您的 CUDA 版本选择合适的 PyTorch：

#### CUDA 12.x 用户（推荐）
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### CUDA 11.8 用户
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 步骤 4：验证 PyTorch 安装

```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

**必须输出**：`CUDA available: True`

如果输出 `False`，说明安装的是 CPU 版本，请返回步骤 3。

### 步骤 5：安装其他依赖

```bash
pip install ctranslate2 faster-whisper av tqdm pyyaml
```

或者使用 requirements.txt：

```bash
pip install -r requirements.txt
```

## 完整安装脚本

Windows PowerShell 用户可以使用以下一键安装脚本：

```powershell
# 1. 验证 CUDA
nvidia-smi

# 2. 安装 NumPy
pip install "numpy<2.0"

# 3. 安装 PyTorch GPU 版本
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. 验证安装
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# 5. 安装其他依赖
pip install ctranslate2 faster-whisper av tqdm pyyaml
```

## 验证安装

运行测试脚本验证所有组件是否正常工作：

```bash
python test_fix.py
```

应该看到所有测试通过：
```
测试 1: 导入 ASR 模块 ✓ 通过
测试 2: 创建 CUDA 引擎 ✓ 通过
测试 3: 验证设备检查 ✓ 通过
测试 4: 加载模型 ✓ 通过
```

## 常见问题

### 问题 1：`CUDA available: False`

**原因**：安装了 CPU 版本的 PyTorch

**解决方案**：
```bash
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 问题 2：`Failed to initialize NumPy: _ARRAY_API not found`

**原因**：NumPy 版本不兼容

**解决方案**：
```bash
pip install "numpy<2.0" --force-reinstall
```

### 问题 3：`本应用仅支持 GPU 加速`

**原因**：尝试使用 CPU 设备运行

**解决方案**：确保配置中设备设置为 `cuda`，不要设置为 `cpu`

### 问题 4：无法在线下载模型

**原因**：网络连接问题导致无法从 HuggingFace 下载模型

**解决方案**：手动下载模型并放置到本地目录

1. **从以下任一来源下载模型**：
   - Hugging Face: https://huggingface.co/Systran/faster-whisper-large-v3-turbo
   - ModelScope (国内镜像): https://modelscope.cn/models/OpenAI/whisper
   - GitHub Releases: https://github.com/SYSTRAN/faster-whisper/releases

2. **将模型文件放置到以下目录**：
   ```
   models/faster-whisper-large-v3-turbo/
   ├── config.json
   ├── model.bin (或 model.safetensors)
   ├── preprocessor_config.json
   ├── tokenizer.json
   ├── vocabulary.json
   └── merges.txt
   ```

3. **重新运行程序**，系统将自动从本地加载模型

详细说明请参考：[models/README.md](models/README.md)

## 卸载和重新安装

如果遇到问题，建议完全卸载后重新安装：

```bash
# 卸载所有相关包
pip uninstall torch torchaudio numpy ctranslate2 faster-whisper -y

# 重新安装
pip install "numpy<2.0"
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install ctranslate2 faster-whisper av tqdm pyyaml
```

## 系统要求

### 最低要求
- NVIDIA 显卡（支持 CUDA 11.8+）
- 8GB RAM
- 10GB 可用磁盘空间

### 推荐配置
- NVIDIA RTX 3060 或更高
- 16GB RAM
- 20GB 可用磁盘空间（用于存储模型）

## 获取帮助

如果遇到问题：
1. 查看 [GPU_REQUIREMENTS.md](docs/GPU_REQUIREMENTS.md)
2. 运行 `python test_fix.py` 进行诊断
3. 检查日志文件获取详细错误信息
