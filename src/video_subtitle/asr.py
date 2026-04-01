"""ASR (Automatic Speech Recognition) engine module."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from .subtitle import Subtitle
from .config import ModelConfig

logger = logging.getLogger(__name__)


class ASREngine(ABC):
    """Abstract base class for ASR engines."""

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        model_path: Optional[str] = None,
    ) -> Subtitle:
        """Transcribe audio file to subtitle."""
        pass

    @abstractmethod
    def detect_language(self, audio_path: str) -> str:
        """Detect the language of the audio file."""
        pass


class MockASREngine(ASREngine):
    """Mock ASR engine for testing purposes."""

    def __init__(self):
        self.model_loaded = False

    def load_model(self, model_path: Optional[str] = None) -> None:
        """Load the mock model."""
        self.model_loaded = True

    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        model_path: Optional[str] = None,
    ) -> Subtitle:
        """Return mock transcription for testing."""
        if not self.model_loaded:
            self.load_model(model_path)

        subtitle = Subtitle(title="Mock Subtitle")
        subtitle.add_segment(
            start_ms=0,
            end_ms=5000,
            text="This is a mock subtitle segment for testing.",
        )
        subtitle.add_segment(
            start_ms=5000,
            end_ms=10000,
            text="The quick brown fox jumps over the lazy dog.",
        )
        return subtitle

    def detect_language(self, audio_path: str) -> str:
        """Return mock language detection."""
        return "en"


class FasterWhisperEngine(ASREngine):
    """Faster Whisper ASR engine implementation."""

    def __init__(
        self,
        model_name: str = "large-v3-turbo",
        device: str = "auto",
        compute_type: str = "float16",
        vad_filter: bool = True,
        vad_parameters: Optional[dict] = None,
        beam_size: int = 5,
        best_of: int = 5,
        temperature: float = 0.0,
        length_penalty: float = 1.0,
        no_speech_threshold: float = 0.6,
        compression_ratio_threshold: float = 2.4,
        condition_on_previous_text: bool = False,
        prompt_reset_on_temperature: float = 0.5,
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.vad_filter = vad_filter
        self.vad_parameters = vad_parameters or {}
        self.beam_size = beam_size
        self.best_of = best_of
        self.temperature = temperature
        self.length_penalty = length_penalty
        self.no_speech_threshold = no_speech_threshold
        self.compression_ratio_threshold = compression_ratio_threshold
        self.condition_on_previous_text = condition_on_previous_text
        self.prompt_reset_on_temperature = prompt_reset_on_temperature
        self.model = None
        self._actual_device = None

    def load_model(self, model_path: Optional[str] = None) -> None:
        """Load the faster-whisper model."""
        try:
            import warnings
            import sys
            
            logger.info("🔍 正在检查硬件环境...")
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*_ARRAY_API.*")
                warnings.filterwarnings("ignore", message=".*Failed to initialize NumPy.*")
                
                import numpy as np
                import torch
                
                cuda_available = torch.cuda.is_available()
                
                if self.device == "auto":
                    if cuda_available:
                        self._actual_device = "cuda"
                        logger.info(f"✅ 检测到 GPU: {torch.cuda.get_device_name(0)}")
                        logger.info("🚀 将使用 GPU 加速")
                    else:
                        self._actual_device = "cpu"
                        logger.info("⚠️  未检测到 GPU")
                        logger.info("💻 将降级使用 CPU 运行（速度较慢）")
                        self.compute_type = "int8"
                        logger.info(f"📊 计算精度已自动调整为：{self.compute_type}")
                elif self.device == "cuda":
                    if not cuda_available:
                        logger.warning("⚠️  用户指定使用 GPU，但 GPU 不可用")
                        logger.warning("💻 降级使用 CPU 运行（速度较慢）")
                        self._actual_device = "cpu"
                        self.compute_type = "int8"
                        logger.info(f"📊 计算精度已自动调整为：{self.compute_type}")
                    else:
                        self._actual_device = "cuda"
                        logger.info(f"✅ GPU 可用：{torch.cuda.get_device_name(0)}")
                elif self.device == "cpu":
                    self._actual_device = "cpu"
                    if cuda_available:
                        logger.info("ℹ️  用户指定使用 CPU，尽管 GPU 可用")
                    else:
                        logger.info("💻 使用 CPU 运行")
                else:
                    self._actual_device = self.device
                
                logger.info("📥 正在加载 faster-whisper 模型...")
                from faster_whisper import WhisperModel

            model_path = model_path or self.model_name
            logger.info(f"模型名称：{model_path}")
            logger.info(f"设备：{self._actual_device}")
            logger.info(f"计算精度：{self.compute_type}")
            
            self.model = WhisperModel(
                model_path,
                device=self._actual_device,
                compute_type=self.compute_type,
            )
            logger.info("✅ 模型加载成功")
        except ImportError:
            raise ImportError(
                "faster-whisper is not installed. Please install it with: pip install faster-whisper"
            )
        except Exception as e:
            error_msg = str(e)
            if "Cannot find an appropriate version of faster-whisper" in error_msg or \
               "Failed to download model" in error_msg or \
               "ConnectionError" in type(e).__name__ or \
               "HTTPSConnectionPool" in error_msg or \
               "Connection refused" in error_msg or \
               "timeout" in error_msg.lower():
                
                project_root = Path(__file__).parent.parent.parent
                model_dir = project_root / "models"
                local_model_path = model_dir / f"faster-whisper-{self.model_name}"
                
                download_info = ModelConfig.get_model_download_info(self.model_name)
                
                raise RuntimeError(
                    f"无法在线下载 faster-whisper 模型：{self.model_name}\n\n"
                    f"错误信息：{error_msg}\n\n"
                    f"=== 手动下载解决方案 ===\n\n"
                    f"请按照以下步骤手动下载模型并放置到正确位置：\n\n"
                    f"1. 选择下载源（推荐按顺序尝试）：\n"
                    f"   - Hugging Face: {download_info['huggingface']}\n"
                    f"   - ModelScope (国内镜像): {download_info['modelscope']}\n"
                    f"   - GitHub Releases: {download_info['github_release']}\n\n"
                    f"2. 下载完成后，将模型文件解压到以下目录：\n"
                    f"   {local_model_path}\n\n"
                    f"3. 确保目录结构如下：\n"
                    f"   models/\n"
                    f"   └── faster-whisper-{self.model_name}/\n"
                    f"       ├── config.json\n"
                    f"       ├── model.bin (或 .safetensors)\n"
                    f"       ├── preprocessor_config.json\n"
                    f"       ├── tokenizer.json\n"
                    f"       ├── vocabulary.json\n"
                    f"       └── merges.txt\n\n"
                    f"4. 重新运行程序，系统将自动从本地加载模型\n\n"
                    f"模型说明：{download_info['description']}\n"
                )
            else:
                raise

    def transcribe(
        self,
        audio_path: str,
        language: str = "auto",
        model_path: Optional[str] = None,
    ) -> Subtitle:
        """Transcribe audio file using faster-whisper."""
        if self.model is None:
            self.load_model(model_path)

        lang = None if language == "auto" else language
        
        logger.info(f"🎙️ 开始语音识别...")
        logger.info(f"音频文件：{Path(audio_path).name}")
        logger.info(f"语言设置：{language}")
        if self.vad_filter:
            logger.info("VAD 过滤：已启用")

        segments, info = self.model.transcribe(
            audio_path,
            language=lang,
            vad_filter=self.vad_filter,
            vad_parameters=self.vad_parameters,
            beam_size=self.beam_size,
            best_of=self.best_of,
            temperature=self.temperature,
            length_penalty=self.length_penalty,
            no_speech_threshold=self.no_speech_threshold,
            compression_ratio_threshold=self.compression_ratio_threshold,
            condition_on_previous_text=self.condition_on_previous_text,
            prompt_reset_on_temperature=self.prompt_reset_on_temperature,
        )
        
        logger.info(f"📊 检测到的语言：{info.language} (概率：{info.language_probability:.2%})")

        subtitle = Subtitle(title="Video Subtitle")
        segment_count = 0
        for segment in segments:
            start_ms = int(segment.start * 1000)
            end_ms = int(segment.end * 1000)
            text = segment.text.strip()
            subtitle.add_segment(
                start_ms=start_ms,
                end_ms=end_ms,
                text=text,
            )
            segment_count += 1
        
        logger.info(f"✅ 语音识别完成，共 {segment_count} 个片段")

        return subtitle

    def detect_language(self, audio_path: str) -> str:
        """Detect language using faster-whisper."""
        if self.model is None:
            self.load_model()

        logger.info(f"🔍 正在进行语言检测...")
        _, info = self.model.transcribe(audio_path, language="auto")
        logger.info(f"✅ 检测到语言：{info.language} (概率：{info.language_probability:.2%})")
        return info.language
