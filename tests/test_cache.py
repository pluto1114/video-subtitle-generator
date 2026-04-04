"""Tests for model cache module."""

import pytest
from video_subtitle.cache import ModelCache
from video_subtitle.asr import MockASREngine, FasterWhisperEngine


class TestModelCache:
    """Test cases for ModelCache singleton."""

    def test_singleton_pattern(self):
        """Test that ModelCache is a singleton."""
        cache1 = ModelCache()
        cache2 = ModelCache()
        assert cache1 is cache2

    def test_initial_stats(self):
        """Test initial cache statistics."""
        cache = ModelCache()
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["loads"] == 0
        assert stats["cached_models"] == 0

    def test_cache_mock_engine(self):
        """Test caching mock ASR engine."""
        cache = ModelCache()
        cache.clear()

        engine = cache.get_or_load("mock")
        assert isinstance(engine, MockASREngine)

        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["loads"] == 1
        assert stats["cached_models"] == 1

    def test_cache_hit(self):
        """Test cache hit scenario."""
        cache = ModelCache()
        cache.clear()

        engine1 = cache.get_or_load("mock")
        engine2 = cache.get_or_load("mock")

        assert engine1 is engine2

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_different_models(self):
        """Test caching different models."""
        cache = ModelCache()
        cache.clear()

        engine1 = cache.get_or_load("mock", model_name="model1")
        engine2 = cache.get_or_load("mock", model_name="model2")

        assert engine1 is not engine2

        stats = cache.get_stats()
        assert stats["cached_models"] == 2

    def test_cache_different_devices(self):
        """Test caching with different devices."""
        cache = ModelCache()
        cache.clear()

        engine1 = cache.get_or_load("mock", device="cuda")
        engine2 = cache.get_or_load("mock", device="cpu")

        assert engine1 is not engine2
        assert cache.get_stats()["cached_models"] == 2

    def test_clear_cache(self):
        """Test clearing the cache."""
        cache = ModelCache()
        cache.clear()

        cache.get_or_load("mock")
        assert cache.get_stats()["cached_models"] == 1

        cache.clear()
        assert cache.get_stats()["cached_models"] == 0
        assert cache.get_stats()["hits"] == 0
        assert cache.get_stats()["misses"] == 0

    def test_remove_from_cache(self):
        """Test removing specific model from cache."""
        cache = ModelCache()
        cache.clear()

        cache.get_or_load("mock", model_name="model1")
        cache.get_or_load("mock", model_name="model2")

        assert cache.get_stats()["cached_models"] == 2

        keys = cache.get_cached_keys()
        assert len(keys) == 2
        
        result = cache.remove(keys[0])
        assert result is True
        assert cache.get_stats()["cached_models"] == 1

        result = cache.remove("nonexistent")
        assert result is False

    def test_get_cached_keys(self):
        """Test getting cached model keys."""
        cache = ModelCache()
        cache.clear()

        cache.get_or_load("mock", model_name="model1")
        cache.get_or_load("mock", model_name="model2")

        keys = cache.get_cached_keys()
        assert len(keys) == 2
        # 检查 cache_key 包含正确的参数
        assert "mock:model1:" in keys[0] or "mock:model1:" in keys[1]
        assert "mock:model2:" in keys[0] or "mock:model2:" in keys[1]
        # 检查新的默认参数值
        assert ":10:10:0.0:1.0:0.2:2.4:True:0.5" in keys[0]
        assert ":10:10:0.0:1.0:0.2:2.4:True:0.5" in keys[1]

    def test_invalid_engine_type(self):
        """Test that invalid engine type raises error."""
        cache = ModelCache()
        cache.clear()

        with pytest.raises(ValueError, match="Unknown engine type"):
            cache.get_or_load("invalid_engine")
