"""Small multi-provider text-to-speech client shared by Ageha applications."""

from __future__ import annotations

import base64
import json
import os
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


class TTSError(ValueError):
    """Raised when a TTS request or provider response is invalid."""


@dataclass(frozen=True, slots=True)
class Audio:
    """Synthesized audio kept in memory until the caller chooses what to do with it."""

    data: bytes
    format: str
    media_type: str
    sample_rate: int | None = None
    bitrate: int | None = None
    channels: int | None = None
    trace_id: str | None = None
    duration_ms: int | None = None

    @property
    def bytes(self) -> bytes:
        """An alias useful when passing audio directly to another library."""
        return self.data

    @property
    def channel(self) -> int | None:
        """Singular alias matching the provider-neutral audio profile name."""
        return self.channels

    def save(self, path: str | Path, *, overwrite: bool = False) -> Path:
        destination = Path(path).expanduser()
        if not destination.suffix:
            destination = destination.with_suffix(f".{self.format}")
        if destination.suffix.lower() != f".{self.format}":
            raise TTSError(f"Output suffix must be .{self.format}: {destination}")
        destination = destination.resolve()
        if destination.exists() and not overwrite:
            raise TTSError(f"Output file already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(self.data)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return destination


_FORMATS = {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac",
            "pcm": "audio/L16", "ogg": "audio/ogg", "ogg_opus": "audio/ogg"}
_END_CODE = 20000000
_EMOTION_RATE = {
    "happy": (10, 4), "sad": (-14, -5), "angry": (7, 10),
    "fearful": (-5, -2), "disgusted": (-7, 1), "surprised": (12, 5),
    "calm": (-8, -2), "whisper": (-10, -12), "whipser": (-10, -12),
}
_EMOTION_TAG = {
    "happy": "[眉眼弯弯，忍不住笑出来，语调轻快上扬]",
    "sad": "[声音低落，强忍着难过，放慢语速，尾音轻轻落下]",
    "angry": "[皱着眉，明显生气，语气有力而克制]",
    "fearful": "[紧张地压低声音，呼吸略急，带着迟疑]",
    "disgusted": "[轻轻皱眉，明显嫌弃，语气不耐烦]",
    "surprised": "[突然睁大眼睛，十分惊讶，语调明显上扬]",
    "calm": "[放松下来，语气平静温和，像面对面聊天]",
    "whisper": "[靠近耳边，压低声音说悄悄话]",
    "whipser": "[靠近耳边，压低声音说悄悄话]",
}
_EMOTION_CONTEXT = {
    "neutral": "用自然、有生活感、像朋友聊天而不是播报的语气演绎下面这句话：",
    "happy": "用轻松开心、带一点真实笑意的语气演绎下面这句话：",
    "sad": "用低落克制、稍微放慢但不要刻意煽情的语气演绎下面这句话：",
    "angry": "用有点生气、语气更有力度但不要喊叫的方式演绎下面这句话：",
    "fearful": "用紧张害怕、略带迟疑的语气演绎下面这句话：",
    "disgusted": "用嫌弃、不耐烦但仍然自然的语气演绎下面这句话：",
    "surprised": "用真实惊讶、语调有明显起伏的方式演绎下面这句话：",
    "calm": "用平静放松、温和自然的语气演绎下面这句话：",
    "fluent": "用顺畅自然、像随口聊天的语气演绎下面这句话：",
    "whisper": "用压低声音、像说悄悄话的语气演绎下面这句话：",
    "whipser": "用压低声音、像说悄悄话的语气演绎下面这句话：",
}


class TTS:
    """One compact API for MiniMax, Doubao, BreezeBlue and Fish Audio."""

    def __init__(
        self,
        provider: str,
        *,
        api_key: str,
        model: str = "",
        voice: str = "",
        base_url: str | None = None,
        timeout: float = 60.0,
        session: requests.Session | None = None,
        **defaults: Any,
    ) -> None:
        aliases = {"breeze": "breezeblue", "fish audio": "fish"}
        self.provider = aliases.get(provider.strip().lower(), provider.strip().lower())
        if self.provider not in {"minimax", "doubao", "breezeblue", "fish"}:
            raise TTSError(f"Unsupported TTS provider: {provider}")
        self.api_key = api_key.strip()
        self.model = model or {
            "minimax": "speech-2.8-hd", "doubao": "seed-tts-2.0",
            "breezeblue": "breeze-tts-2", "fish": "s2.1-pro",
        }[self.provider]
        self.voice = voice.strip()
        self.base_url = (base_url or {
            "minimax": "https://api.minimaxi.com/v1",
            "doubao": "https://openspeech.bytedance.com",
            "fish": "https://api.fish.audio",
            "breezeblue": "",
        }[self.provider]).rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.defaults = defaults
        if timeout <= 0:
            raise ValueError("TTS timeout must be positive")

    def synthesize(
        self,
        text: str,
        *,
        voice: str | None = None,
        model: str | None = None,
        format: str = "mp3",
        sample_rate: int | None = None,
        bitrate: int | None = None,
        speed: float | None = None,
        volume: float | None = None,
        pitch: int | None = None,
        emotion: str | None = None,
        language: str | None = None,
        instructions: str | None = None,
        context_texts: Sequence[str] = (),
        consistent: bool = False,
    ) -> Audio:
        text = text.strip()
        if not text:
            raise TTSError("TTS text cannot be empty")
        if not self.api_key:
            raise TTSError(f"API key is not configured for {self.provider}")
        fmt = format.strip().lower()
        if fmt not in _FORMATS:
            raise TTSError(f"Unsupported TTS format: {fmt}")
        selected_voice = (voice or self.voice).strip()
        if not selected_voice:
            raise TTSError(f"Voice is not configured for {self.provider}")
        opts = {
            "model": model or self.model, "format": fmt,
            "sample_rate": sample_rate or self.defaults.get("sample_rate") or 24000,
            "bitrate": bitrate or self.defaults.get("bitrate") or 128000,
            "speed": speed if speed is not None else self.defaults.get("speed", 1.0),
            "volume": volume if volume is not None else self.defaults.get("volume", 1.0),
            "pitch": pitch if pitch is not None else self.defaults.get("pitch", 0),
            "emotion": (emotion if emotion is not None else self.defaults.get("emotion", "")) or "",
            "language": language or self.defaults.get("language", "zh"),
            "instructions": instructions if instructions is not None else self.defaults.get("instructions", ""),
            "context_texts": context_texts or self.defaults.get("context_texts", ()),
            "consistent": consistent or self.defaults.get("consistent", False),
            "channel": self.defaults.get("channel", 1),
        }
        try:
            if self.provider == "minimax":
                data, trace, duration = self._minimax(text, selected_voice, opts)
            elif self.provider == "doubao":
                data, trace = self._doubao(text, selected_voice, opts)
                duration = None
            elif self.provider == "breezeblue":
                data, trace = self._breeze(text, selected_voice, opts)
                duration = None
            else:
                data, trace = self._fish(text, selected_voice, opts)
                duration = None
        except requests.RequestException as error:
            raise TTSError(f"{self.provider} TTS request failed: {error}") from error
        return Audio(
            data,
            fmt,
            _FORMATS[fmt],
            opts["sample_rate"],
            opts["bitrate"],
            opts.get("channel", 1),
            trace,
            duration,
        )

    def list_voices(self, voice_type: str = "all") -> dict[str, Any]:
        if not self.api_key:
            raise TTSError(f"API key is not configured for {self.provider}")
        if self.provider == "minimax":
            response = self.session.post(
                f"{self.base_url}/get_voice",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"voice_type": voice_type}, timeout=min(self.timeout, 30),
            )
            payload = self._json(response, "MiniMax voice query")
            self._raise_minimax(payload)
            return payload
        if self.provider == "fish":
            response = self.session.get(
                f"{self.base_url}/model", headers={"Authorization": f"Bearer {self.api_key}"},
                params={"page_size": 100}, timeout=min(self.timeout, 30),
            )
            payload = self._json(response, "Fish Audio voice query")
            records = payload if isinstance(payload, list) else payload.get("items", [])
            return {"voices": records}
        if self.provider == "breezeblue":
            try:
                from breeze_blue import BreezeBlue
            except ImportError as error:
                raise TTSError("Install ageha[breeze] to use BreezeBlue voice catalog") from error
            client = BreezeBlue(api_key=self.api_key, timeout=self.timeout)
            result = client.voices.search(voice_type="personal", page_size=100)
            return {"voices": self._records(result, "voices", "data")}
        response = self.session.post(
            f"{self.base_url}/api/v3/tts/get_voice",
            headers={"X-Api-Key": self.api_key, "Content-Type": "application/json"},
            json={"speaker_id": self.voice}, timeout=min(self.timeout, 30),
        )
        return {"voices": [self._json(response, "Doubao voice query")]}

    def _minimax(
        self, text: str, voice: str, o: dict[str, Any]
    ) -> tuple[bytes, str | None, int | None]:
        if len(text) >= 10000:
            raise TTSError("MiniMax synchronous TTS text must be under 10,000 characters")
        voice_setting: dict[str, Any] = {
            "voice_id": voice, "speed": o["speed"], "vol": o["volume"], "pitch": o["pitch"]
        }
        if o["emotion"]:
            voice_setting["emotion"] = o["emotion"]
        payload = {
            "model": o["model"], "text": text, "stream": False,
            "language_boost": self.defaults.get("language_boost", "Chinese"),
            "output_format": "hex", "voice_setting": voice_setting,
            "audio_setting": {
                "sample_rate": o["sample_rate"], "bitrate": o["bitrate"],
                "format": o["format"], "channel": o["channel"],
            }, "subtitle_enable": False,
        }
        if o["consistent"]:
            payload["text_normalization"] = True
        response = self.session.post(
            f"{self.base_url}/t2a_v2",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload, timeout=self.timeout,
        )
        result = self._json(response, "MiniMax TTS")
        self._raise_minimax(result)
        try:
            audio = bytes.fromhex(result["data"]["audio"])
        except (KeyError, TypeError, ValueError) as error:
            raise TTSError("MiniMax TTS response did not contain valid audio") from error
        if not audio:
            raise TTSError("MiniMax TTS returned empty audio")
        duration = (result.get("extra_info") or {}).get("audio_length")
        try:
            duration = int(duration) if duration is not None else None
        except (TypeError, ValueError):
            duration = None
        return audio, str(result.get("trace_id") or "") or None, duration

    def _doubao(self, text: str, voice: str, o: dict[str, Any]) -> tuple[bytes, str | None]:
        resource = self.defaults.get("resource_id") or ("seed-icl-2.0" if voice.startswith("S_") else "seed-tts-2.0")
        audio_params: dict[str, Any] = {"format": o["format"], "sample_rate": o["sample_rate"]}
        if o["format"] == "mp3":
            audio_params["bit_rate"] = o["bitrate"]
        if o["emotion"] in _EMOTION_RATE:
            audio_params["speech_rate"], audio_params["loudness_rate"] = _EMOTION_RATE[o["emotion"]]
        else:
            audio_params["speech_rate"] = round((o["speed"] - 1) * 100)
            audio_params["loudness_rate"] = round((o["volume"] - 1) * 100)
        params: dict[str, Any] = {"text": text, "speaker": voice, "audio_params": audio_params}
        if o["instructions"]:
            params["context_texts"] = [o["instructions"]]
        if resource == "seed-icl-2.0":
            if o["emotion"] in _EMOTION_TAG:
                params["text"] = f"{_EMOTION_TAG[o['emotion']]}{text}"
            contexts = [" ".join(str(item).split()).strip()[:300] for item in o["context_texts"]]
            contexts = [item for item in contexts if item][-3:]
            contexts.append(_EMOTION_CONTEXT.get(o["emotion"], _EMOTION_CONTEXT["neutral"]))
            params["model"] = "seed-tts-2.0-expressive"
            params["additions"] = json.dumps({"context_texts": contexts, "use_tag_parser": True}, ensure_ascii=False)
        request = self.session.post(
            f"{self.base_url}/api/v3/tts/unidirectional",
            headers={"Content-Type": "application/json", "Accept": "application/json",
                     "X-Api-Key": self.api_key, "X-Api-Resource-Id": resource,
                     "X-Api-Request-Id": str(uuid.uuid4())},
            json={"user": {"uid": "ageha"}, "req_params": params}, timeout=self.timeout, stream=True,
        )
        if request.status_code != 200:
            raise TTSError(f"Doubao TTS HTTP {request.status_code}: {request.text[:300]}")
        audio = bytearray()
        error = ""
        try:
            for line in request.iter_lines():
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except (TypeError, ValueError):
                    continue
                code = event.get("code")
                if code == _END_CODE:
                    error = event.get("message", "")
                    break
                if code == 0 and event.get("data"):
                    audio.extend(base64.b64decode(event["data"]))
                elif code not in (None, 0):
                    error = event.get("message", "") or f"code={code}"
        finally:
            request.close()
        if not audio:
            raise TTSError(f"Doubao TTS returned no audio: {error}")
        return bytes(audio), None

    def _breeze(self, text: str, voice: str, o: dict[str, Any]) -> tuple[bytes, str | None]:
        try:
            from breeze_blue import BreezeBlue
        except ImportError as error:
            raise TTSError("Install ageha[breeze] to use BreezeBlue") from error
        client = BreezeBlue(api_key=self.api_key, timeout=self.timeout)
        options: dict[str, Any] = {
            "voice_id": voice, "text": text, "model_id": o["model"],
            "language_code": o["language"],
            "voice_settings": {"speed": o["speed"], "volume": o["volume"]},
            "output_format": o["format"],
        }
        if o["instructions"]:
            options["instructions"] = o["instructions"]
        result = client.text_to_speech.convert(**options)
        if not result.content:
            raise TTSError("BreezeBlue returned no audio")
        return result.content, None

    def _fish(self, text: str, voice: str, o: dict[str, Any]) -> tuple[bytes, str | None]:
        response = self.session.post(
            f"{self.base_url}/v1/tts",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "model": o["model"]},
            json={"text": text, "reference_id": voice, "prosody": {"speed": o["speed"]}, "format": o["format"]},
            timeout=self.timeout,
        )
        response.raise_for_status()
        if not response.content:
            raise TTSError("Fish Audio returned no audio")
        return response.content, None

    @staticmethod
    def _json(response: Any, label: str) -> dict[str, Any]:
        try:
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as error:
            raise TTSError(f"{label} request failed: {error}") from error
        except ValueError as error:
            raise TTSError(f"{label} returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise TTSError(f"{label} returned an invalid response")
        return payload

    @staticmethod
    def _raise_minimax(payload: dict[str, Any]) -> None:
        response = payload.get("base_resp") or {}
        code = response.get("status_code")
        if code not in (None, 0):
            raise TTSError(f"MiniMax API error {code}: {response.get('status_msg') or 'unknown error'}")

    @staticmethod
    def _records(value: Any, *keys: str) -> list[dict[str, Any]]:
        if isinstance(value, dict):
            for key in keys:
                entries = value.get(key)
                if isinstance(entries, list):
                    normalized = []
                    for item in entries:
                        if isinstance(item, dict):
                            normalized.append(item)
                        elif callable(getattr(item, "model_dump", None)):
                            normalized.append(item.model_dump())
                    return normalized
        return []
