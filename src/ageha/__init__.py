"""Ageha: a Python toolkit and shared integration namespace."""

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

try:
    __version__ = version("ageha-assistant")
except PackageNotFoundError:
    try:
        __version__ = version("ageha")
    except PackageNotFoundError:
        __version__ = "0.0.1"  # x-release-please-version

_tts = import_module(f"{__name__}.clients.tts")
_chat = import_module(f"{__name__}.clients.chat")
TTS = _tts.TTS
Audio = _tts.Audio
TTSError = _tts.TTSError
Chat = _chat.Chat
ChatError = _chat.ChatError

__all__ = ["TTS", "Audio", "Chat", "ChatError", "TTSError", "__version__"]
