"""Test script to verify GPU/CPU automatic fallback functionality."""

import logging
import sys
import pytest
from pathlib import Path

# 添加 src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
from video_subtitle.asr import FasterWhisperEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="Requires model download - run manually for testing")
def test_auto_device_selection():
    """Test automatic device selection with 'auto' setting."""
    logger.info("=" * 60)
    logger.info("测试 1: 自动设备选择 (device='auto')")
    logger.info("=" * 60)
    
    cuda_available = torch.cuda.is_available()
    logger.info(f"CUDA 可用性：{cuda_available}")
    
    engine = FasterWhisperEngine(
        model_name="tiny",
        device="auto",
        compute_type="float16",
    )
    
    logger.info(f"引擎设备设置：{engine.device}")
    logger.info(f"引擎计算精度：{engine.compute_type}")
    
    try:
        engine.load_model()
        logger.info(f"实际使用设备：{engine._actual_device}")
        logger.info(f"实际计算精度：{engine.compute_type}")
        
        if cuda_available:
            assert engine._actual_device == "cuda", "CUDA 可用时应使用 GPU"
            logger.info("✅ 测试通过：CUDA 可用时自动使用 GPU")
        else:
            assert engine._actual_device == "cpu", "CUDA 不可用时应降级到 CPU"
            assert engine.compute_type == "int8", "CPU 模式下应使用 int8 精度"
            logger.info("✅ 测试通过：CUDA 不可用时自动降级到 CPU")
    except Exception as e:
        logger.error(f"❌ 测试失败：{e}")
        raise
    
    logger.info("")


@pytest.mark.skip(reason="Requires model download - run manually for testing")
def test_force_cuda_with_gpu_available():
    """Test forcing CUDA when GPU is available."""
    logger.info("=" * 60)
    logger.info("测试 2: 强制使用 GPU (device='cuda')")
    logger.info("=" * 60)
    
    cuda_available = torch.cuda.is_available()
    logger.info(f"CUDA 可用性：{cuda_available}")
    
    engine = FasterWhisperEngine(
        model_name="tiny",
        device="cuda",
        compute_type="float16",
    )
    
    try:
        engine.load_model()
        logger.info(f"实际使用设备：{engine._actual_device}")
        
        if cuda_available:
            assert engine._actual_device == "cuda", "应使用 GPU"
            logger.info("✅ 测试通过：成功使用 GPU")
        else:
            assert engine._actual_device == "cpu", "GPU 不可用时应降级到 CPU"
            logger.info("✅ 测试通过：GPU 不可用时自动降级到 CPU")
    except Exception as e:
        logger.error(f"❌ 测试失败：{e}")
        raise
    
    logger.info("")


@pytest.mark.skip(reason="Requires model download - run manually for testing")
def test_force_cpu():
    """Test forcing CPU regardless of GPU availability."""
    logger.info("=" * 60)
    logger.info("测试 3: 强制使用 CPU (device='cpu')")
    logger.info("=" * 60)
    
    cuda_available = torch.cuda.is_available()
    logger.info(f"CUDA 可用性：{cuda_available}")
    
    engine = FasterWhisperEngine(
        model_name="tiny",
        device="cpu",
        compute_type="int8",
    )
    
    engine.load_model()
    logger.info(f"实际使用设备：{engine._actual_device}")
    
    assert engine._actual_device == "cpu", "应使用 CPU"
    logger.info("✅ 测试通过：成功使用 CPU")
    
    logger.info("")


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 10 + "GPU/CPU 自动降级功能测试" + " " * 22 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    logger.info("")
    
    test_auto_device_selection()
    test_force_cuda_with_gpu_available()
    test_force_cpu()
    
    logger.info("=" * 60)
    logger.info("🎉 所有测试通过！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
