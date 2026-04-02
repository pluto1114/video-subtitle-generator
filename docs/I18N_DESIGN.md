# 国际化（i18n）设计文档

## 概述

本文档描述了视频字幕生成器项目的国际化（i18n）实现方案，支持多语言界面切换，默认使用操作系统语言。

## 技术架构

### 1. 核心模块：`i18n.py`

**功能：**
- 检测系统默认语言
- 加载翻译文件
- 提供翻译函数 `_()`
- 支持动态语言切换
- 语言枚举定义

### 2. 翻译文件结构

```
src/video_subtitle/locales/
├── zh_CN.json    # 简体中文
├── en_US.json    # 美式英语
└── ja_JP.json    # 日语（可选扩展）
```

### 3. 支持的语言

| 语言代码 | 语言名称 | 说明 |
|---------|---------|------|
| `zh_CN` | 简体中文 | 默认（如果系统是中文） |
| `en_US` | 美式英语 | 默认（如果系统不是中文） |

## 实现细节

### 系统语言检测

使用 `locale` 模块检测操作系统默认语言：
- Windows: 通过 `GetUserDefaultUILanguage` 或 `locale.getdefaultlocale()`
- Unix-like: 通过 `LANG` 环境变量

### 配置持久化

语言设置将保存到配置文件中：
- 配置项: `app.language`
- 默认值: `auto`（检测系统语言）

### 翻译函数使用

```python
from .i18n import _

# 基本翻译
text = _("Hello")

# 带参数的翻译
text = _("Processing file: {filename}").format(filename="video.mp4")
```

## GUI 集成

### 语言切换器

在 GUI 顶部添加语言选择下拉菜单，支持动态切换界面语言。

### 动态更新机制

语言切换后，所有界面元素立即更新，无需重启应用。

## 日志国际化

所有日志输出也支持国际化，确保：
- 调试日志可使用英文
- 用户可见的日志使用当前选择的语言

## 文件修改清单

1. **新增文件：**
   - `src/video_subtitle/i18n.py` - 国际化核心模块
   - `src/video_subtitle/locales/zh_CN.json` - 中文翻译
   - `src/video_subtitle/locales/en_US.json` - 英文翻译

2. **修改文件：**
   - `src/video_subtitle/config.py` - 添加语言配置
   - `src/video_subtitle/config_manager.py` - 保存/加载语言设置
   - `src/video_subtitle/gui.py` - 集成语言切换和翻译
   - `src/video_subtitle/asr.py` - 日志国际化
   - `src/video_subtitle/processor.py` - 日志国际化

## 扩展指南

添加新语言的步骤：
1. 在 `locales/` 目录创建新的 JSON 文件（如 `fr_FR.json`）
2. 复制现有翻译文件内容作为模板
3. 翻译所有字符串
4. 在 `i18n.py` 的 `SUPPORTED_LANGUAGES` 枚举中添加新语言
