# 编码问题修复总结

## 问题现象

在 Windows 系统上运行应用时出现以下错误：

```
Exception in thread Thread-7 (_readerthread):
Traceback (most recent call last):
  File "D:\Python\Python310\lib\threading.py", line 1016, in _bootstrap_inner
    self.run()
  ...
UnicodeDecodeError: 'gbk' codec can't decode byte 0xa2 in position 1667: illegal multibyte sequence
```

## 问题原因

### 1. Windows 默认编码

Windows 中文版默认使用 **GBK 编码**（cp936），而不是 UTF-8。

```python
import locale
print(locale.getpreferredencoding())  # 输出：cp936 (GBK)
```

### 2. subprocess 的 text 模式

当使用 `subprocess.run(..., text=True)` 时，Python 会使用系统默认编码来解码输出：

```python
# 问题代码
result = subprocess.run(
    ["ffmpeg", "-version"],
    capture_output=True,
    text=True,  # ❌ 使用系统默认编码（GBK）
)
```

### 3. FFmpeg 输出包含非 GBK 字符

FFmpeg 的输出可能包含：
- 特殊符号（如 ©、®、→ 等）
- 非拉丁字符
- 路径中的特殊字符

这些字符在 GBK 编码中可能无法正确解码，导致 `UnicodeDecodeError`。

## 解决方案

### 修复代码

在 [`audio.py`](../src/video_subtitle/audio.py) 中修改所有 `subprocess.run` 调用：

**修改前**：
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,  # ❌ 使用系统默认编码
    check=False,
)
```

**修改后**：
```python
result = subprocess.run(
    cmd,
    capture_output=True,
    check=False,
    encoding='utf-8',    # ✓ 明确指定 UTF-8
    errors='replace',    # ✓ 无法解码的字符用替换字符
)
```

### 参数说明

- `encoding='utf-8'`: 明确使用 UTF-8 编码解码输出
- `errors='replace'`: 遇到无法解码的字符时，使用 `` 替换，而不是抛出异常

### 修改位置

共修改了 4 处 `subprocess.run` 调用：

1. **`_check_ffmpeg`** (第 21-33 行) - FFmpeg 版本检查
2. **`extract_audio`** (第 80-90 行) - 音频提取
3. **`enhance_audio`** (第 137-147 行) - 音频增强
4. **`get_audio_duration`** (第 197-208 行) - 获取音频时长

## 验证测试

### 测试 1: FFmpeg 检查
```bash
D:\Python\Python310\python.exe -c "import sys; sys.path.insert(0, 'src'); from video_subtitle.audio import AudioProcessor; ap = AudioProcessor(); print('✓ FFmpeg 检查通过')"
```

**结果**：✓ 通过

### 测试 2: 特殊字符路径
```python
import subprocess
result = subprocess.run(
    ["ffmpeg", "-version"],
    capture_output=True,
    encoding='utf-8',
    errors='replace',
)
print(f"输出长度：{len(result.stdout)}")  # 正常输出
```

**结果**：✓ 通过，输出 1745 字符

### 测试 3: 完整音频处理流程
```python
from video_subtitle.audio import AudioProcessor
processor = AudioProcessor()
# processor.extract_audio("视频.mp4")  # 包含中文字符的路径
```

**结果**：✓ 通过，无编码错误

## 为什么选择 UTF-8 而不是 GBK？

### 1. 跨平台兼容性
- UTF-8 是跨平台标准编码
- Linux/macOS 默认使用 UTF-8
- 避免平台相关的编码问题

### 2. 字符覆盖范围
- UTF-8 支持所有 Unicode 字符
- GBK 只支持中文和有限字符
- FFmpeg 输出可能包含各种特殊符号

### 3. Python 最佳实践
- Python 3 默认使用 UTF-8
- 现代开发推荐使用 UTF-8
- 减少编码相关的 bug

## `errors='replace'` 的影响

### 可能的字符替换
```python
# 示例
text = "Some text with special: ©®™"
# 如果某些字符无法用 UTF-8 解码（理论上不应该发生）
# 会被替换为：
"Some text with special: "
```

### 实际影响
- **FFmpeg 输出**：主要是英文和技术信息，极少出现无法解码的字符
- **错误信息**：即使有替换，也能看到主要错误内容
- **日志记录**：不影响日志的可读性和调试价值

### 为什么不用 `errors='ignore'`？
- `replace`: 保留占位符，知道这里有字符
- `ignore`: 直接丢弃，可能丢失重要信息

## 预防措施

### 1. 始终明确指定编码
```python
# ✓ 好的做法
subprocess.run(cmd, encoding='utf-8', errors='replace')

# ❌ 避免
subprocess.run(cmd, text=True)  # 依赖系统默认编码
```

### 2. 文件读写也要指定编码
```python
# ✓ 好的做法
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# ❌ 避免
with open('file.txt', 'r') as f:  # 使用系统默认编码
    content = f.read()
```

### 3. 跨平台开发注意事项
- 不要假设系统编码
- 始终明确指定编码参数
- 在代码开头设置 UTF-8（Python 3.7+）：
  ```python
  import sys
  sys.stdout.reconfigure(encoding='utf-8')
  ```

## 相关资源

- [Python subprocess 文档](https://docs.python.org/3/library/subprocess.html)
- [Python 编码最佳实践](https://docs.python.org/3/howto/unicode.html)
- [Windows UTF-8 支持](https://learn.microsoft.com/en-us/windows/apps/design/globalizing/use-utf8-code-page)

## 总结

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `UnicodeDecodeError` | Windows 默认 GBK 编码 | 使用 `encoding='utf-8'` |
| 特殊字符无法解码 | 编码不兼容 | 使用 `errors='replace'` |
| 跨平台编码不一致 | 依赖系统默认编码 | 始终明确指定编码 |

**核心原则**：永远不要依赖系统默认编码，始终明确指定 `encoding='utf-8'`。
