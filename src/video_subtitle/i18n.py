"""Internationalization (i18n) module for Video Subtitle Generator."""

import json
import locale
import logging
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages."""
    ZH_CN = "zh_CN"
    EN_US = "en_US"


LANGUAGE_NAMES = {
    Language.ZH_CN: "简体中文",
    Language.EN_US: "English (US)",
}


class I18nManager:
    """Internationalization manager for handling translations."""

    _instance: Optional['I18nManager'] = None
    _translations: Dict[str, str] = {}
    _current_language: Language = Language.EN_US
    _locale_dir: Path
    _callbacks: list[Callable[[], None]] = []

    def __new__(cls) -> 'I18nManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self._locale_dir = Path(__file__).parent / "locales"
            self._initialized = True

    def detect_system_language(self) -> Language:
        """Detect the system default language."""
        try:
            system_locale, _ = locale.getdefaultlocale()
            if system_locale:
                if system_locale.startswith("zh"):
                    return Language.ZH_CN
        except Exception as e:
            logger.warning(f"Failed to detect system language: {e}")
        return Language.EN_US

    def set_language(self, language: Language) -> None:
        """Set the current language and load translations."""
        self._current_language = language
        self._load_translations()
        for callback in self._callbacks:
            callback()

    def get_language(self) -> Language:
        """Get the current language."""
        return self._current_language

    def _load_translations(self) -> None:
        """Load translation file for the current language."""
        translation_file = self._locale_dir / f"{self._current_language.value}.json"
        try:
            if translation_file.exists():
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self._translations = json.load(f)
                logger.info(f"Loaded translations for {self._current_language.value}")
            else:
                logger.warning(f"Translation file not found: {translation_file}")
                self._translations = {}
        except Exception as e:
            logger.error(f"Failed to load translations: {e}")
            self._translations = {}

    def translate(self, key: str, **kwargs) -> str:
        """Translate a key to the current language."""
        text = self._translations.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format key '{e}' in translation: {key}")
        return text

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when language changes."""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[], None]) -> None:
        """Unregister a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


_i18n_manager = I18nManager()


def _(key: str, **kwargs) -> str:
    """Translate a key to the current language (shortcut function)."""
    return _i18n_manager.translate(key, **kwargs)


def get_i18n_manager() -> I18nManager:
    """Get the global i18n manager instance."""
    return _i18n_manager


def init_i18n(language: Optional[Language] = None) -> None:
    """Initialize the i18n system."""
    manager = get_i18n_manager()
    if language is None:
        language = manager.detect_system_language()
    manager.set_language(language)
