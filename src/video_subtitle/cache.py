"""Model cache management for efficient model loading."""

import threading
from typing import Dict, Optional, Any
from .asr import ASREngine, FasterWhisperEngine, MockASREngine


class ModelCache:
    """Thread-safe cache for ASR models."""

    _instance: Optional["ModelCache"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelCache":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache: Dict[str, ASREngine] = {}
        self._cache_lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "loads": 0}

    def get_or_load(
        self,
        engine_type: str,
        model_name: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
        local_model_path: Optional[str] = None,
        vad_filter: bool = True,
        vad_parameters: Optional[dict] = None,
        beam_size: int = 5,
        best_of: int = 5,
        temperature: float = 0.0,
        length_penalty: float = 1.0,
        no_speech_threshold: float = 0.6,
        compression_ratio_threshold: float = 2.4,
        condition_on_previous_text: bool = True,
        prompt_reset_on_temperature: float = 0.5,
    ) -> ASREngine:
        """Get model from cache or load it if not present."""
        cache_key = f"{engine_type}:{model_name}:{device}:{compute_type}:{local_model_path}:{vad_filter}:{vad_parameters}:{beam_size}:{best_of}:{temperature}"

        with self._cache_lock:
            if cache_key in self._cache:
                self._stats["hits"] += 1
                return self._cache[cache_key]

            self._stats["misses"] += 1

            if engine_type == "mock":
                engine = MockASREngine()
            elif engine_type == "faster_whisper":
                engine = FasterWhisperEngine(
                    model_name=model_name,
                    device=device,
                    compute_type=compute_type,
                    vad_filter=vad_filter,
                    vad_parameters=vad_parameters,
                    beam_size=beam_size,
                    best_of=best_of,
                    temperature=temperature,
                    length_penalty=length_penalty,
                    no_speech_threshold=no_speech_threshold,
                    compression_ratio_threshold=compression_ratio_threshold,
                    condition_on_previous_text=condition_on_previous_text,
                    prompt_reset_on_temperature=prompt_reset_on_temperature,
                )
            else:
                raise ValueError(f"Unknown engine type: {engine_type}")

            engine.load_model(model_path=local_model_path)
            self._cache[cache_key] = engine
            self._stats["loads"] += 1

            return engine

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        with self._cache_lock:
            return {
                **self._stats,
                "cached_models": len(self._cache),
            }

    def clear(self) -> None:
        """Clear all cached models."""
        with self._cache_lock:
            self._cache.clear()
            self._stats = {"hits": 0, "misses": 0, "loads": 0}

    def remove(self, cache_key: str) -> bool:
        """Remove a specific model from cache."""
        with self._cache_lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False

    def get_cached_keys(self) -> list[str]:
        """Get list of cached model keys."""
        with self._cache_lock:
            return list(self._cache.keys())
