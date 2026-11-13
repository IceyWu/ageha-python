from __future__ import annotations

import base64
import sys
from types import ModuleType, SimpleNamespace

import pytest

from ageha import TTS, Audio, TTSError


class Response:
    status_code = 200
    text = ""

    def __init__(self, payload=None, content=b"audio"):
        self.payload = payload or {
            "data": {"audio": content.hex()},
            "base_resp": {"status_code": 0},
            "trace_id": "trace-1",
        }
        self.content = content
        self.closed = False

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload

    def iter_lines(self):
        encoded = base64.b64encode(b"audio").decode()
        yield f'{{"code":0,"data":"{encoded}"}}'.encode()
        yield b'{"code":20000000,"message":"OK"}'

    def close(self):
        self.closed = True


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def test_minimax_returns_audio_and_keeps_provider_parameters():
    session = Session(Response())
    client = TTS("minimax", api_key="key", voice="v1", session=session)

    result = client.synthesize(" Hello ", emotion="calm", format="mp3", bitrate=64000)

    assert isinstance(result, Audio)
    assert result.data == b"audio"
    assert result.format == "mp3"
    assert result.trace_id == "trace-1"
    payload = session.calls[0][1]["json"]
    assert payload["text"] == "Hello"
    assert payload["voice_setting"]["emotion"] == "calm"
    assert payload["audio_setting"]["bitrate"] == 64000


def test_doubao_returns_decoded_stream_audio():
    response = Response()
    session = Session(response)
    client = TTS("doubao", api_key="key", voice="zh_voice", session=session)

    result = client.synthesize("你好", format="mp3")

    assert result.data == b"audio"
    assert response.closed is True
    assert session.calls[0][1]["headers"]["X-Api-Resource-Id"] == "seed-tts-2.0"


def test_fish_audio_uses_selected_model_and_voice():
    session = Session(Response(content=b"fish-audio"))
    client = TTS("fish", api_key="key", model="s2.1-pro", voice="voice-id", session=session)

    result = client.synthesize("hello", speed=1.2)

    assert result.data == b"fish-audio"
    url, request = session.calls[0]
    assert url == "https://api.fish.audio/v1/tts"
    assert request["headers"]["model"] == "s2.1-pro"
    assert request["json"]["reference_id"] == "voice-id"
    assert request["json"]["prosody"]["speed"] == 1.2


def test_breeze_blue_uses_common_options(monkeypatch):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))

        @property
        def text_to_speech(self):
            return self

        def convert(self, **kwargs):
            calls.append(("convert", kwargs))
            return SimpleNamespace(content=b"breeze-audio")

    module = ModuleType("breeze_blue")
    module.BreezeBlue = Client
    monkeypatch.setitem(sys.modules, "breeze_blue", module)
    client = TTS("breezeblue", api_key="key", model="breeze-tts-2", voice="voice-id")

    result = client.synthesize("hello", speed=0.9, instructions="Warm tone")

    assert result.data == b"breeze-audio"
    assert calls[-1][1]["model_id"] == "breeze-tts-2"
    assert calls[-1][1]["voice_settings"]["speed"] == 0.9
    assert calls[-1][1]["instructions"] == "Warm tone"


def test_audio_save_requires_explicit_overwrite(tmp_path):
    result = Audio(b"audio", "mp3", "audio/mpeg")
    output = result.save(tmp_path / "sample")
    assert output.name == "sample.mp3"
    assert output.read_bytes() == b"audio"
    with pytest.raises(TTSError, match="already exists"):
        result.save(output)
    result.save(output, overwrite=True)


def test_unknown_provider_and_missing_voice_are_clear_errors():
    with pytest.raises(TTSError, match="Unsupported TTS provider"):
        TTS("unknown", api_key="key")
    with pytest.raises(TTSError, match="Voice is not configured"):
        TTS("fish", api_key="key").synthesize("hello")
