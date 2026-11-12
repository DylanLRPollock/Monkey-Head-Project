"""Coverage of audio adapter routing, payloads, and backend failures."""

from __future__ import annotations

import asyncio

import aiohttp
import pytest

from huey.banana_brain.audio_adapter import AudioAdapter, _payload_num, _safe_text

from .conftest import make_job


class Response:
    def __init__(
        self, *, status=200, text="", data=None, audio=b"audio", fail_text=False
    ):
        self.status = status
        self._text = text
        self._data = data or {}
        self._audio = audio
        self.fail_text = fail_text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def text(self):
        if self.fail_text:
            raise RuntimeError("body unavailable")
        return self._text

    async def json(self, **_kwargs):
        return self._data

    async def read(self):
        return self._audio


class Session:
    closed = False

    def __init__(self, response=None):
        self.response = response or Response()
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self.response

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self.response

    async def close(self):
        self.closed = True


def adapter(config=None, response=None):
    item = AudioAdapter(config or {}, object())
    item._session = Session(response)
    return item


@pytest.mark.asyncio
async def test_config_validation_vram_estimates_and_lifecycle():
    with pytest.raises(ValueError, match="audio_stt_base_url"):
        AudioAdapter({"audio_stt_backend": "whisper-cpp"}, object())
    with pytest.raises(ValueError, match="audio_tts_base_url"):
        AudioAdapter({"audio_tts_backend": "piper"}, object())
    stt = adapter(
        {
            "audio_stt_backend": "faster-whisper-server",
            "audio_stt_base_url": "http://stt/",
            "audio_model_vram_gib": {"stt:large-v3": 1.0},
        }
    )
    assert stt._stt_url == "http://stt"
    assert await stt.estimate_vram(make_job(payload={"task": "transcribe"})) == int(
        1.5 * 1024**3
    )
    assert await stt.estimate_vram(
        make_job(payload={"task": "transcribe", "model": "TINY"})
    ) == int(0.7 * 1024**3)
    with pytest.raises(RuntimeError, match="synthesis is not configured"):
        await stt.estimate_vram(make_job(payload={"task": "synthesize"}))
    tts = adapter(
        {
            "audio_tts_backend": "piper",
            "audio_tts_base_url": "http://tts",
            "audio_model_vram_gib": {"piper": 0.1},
        }
    )
    assert await tts.estimate_vram(
        make_job(payload={"task": "synthesize", "model": "ignored"})
    ) == int(0.6 * 1024**3)
    with pytest.raises(ValueError, match="unknown audio task"):
        await tts.estimate_vram(make_job(payload={"task": "unknown"}))
    with pytest.raises(RuntimeError, match="session is not open"):
        AudioAdapter({"audio_tts_backend": "disabled"}, object())._require_session()
    tts._session.closed = True
    with pytest.raises(RuntimeError, match="session is not open"):
        tts._require_session()
    assert not await tts.request_cancel(make_job(id="cancel-me", payload={"task": "x"}))
    assert "cancel-me" in tts._cancellation_requested
    await tts.stop()
    assert tts._session is None


@pytest.mark.asyncio
async def test_transcription_faster_whisper_json_text_errors_and_cleanup(tmp_path):
    source = tmp_path / "sample.wav"
    source.write_bytes(b"wave")
    item = adapter(
        {
            "audio_stt_backend": "faster-whisper-server",
            "audio_stt_base_url": "http://stt",
        },
        Response(data={"text": "recognized", "language": "en", "segments": [1]}),
    )
    result = await item.execute(
        make_job(
            payload={
                "task": "transcribe",
                "audio_path": str(source),
                "language": "en",
                "prompt": "context",
                "temperature": 0.2,
            }
        )
    )
    assert result["text"] == "recognized"
    assert result["backend"] == "faster-whisper-server"
    assert item._busy == 0
    assert item._session.calls[0][1].endswith("/v1/audio/transcriptions")

    item._session.response = Response(text="raw words")
    text = await item.execute(
        make_job(
            payload={
                "task": "transcribe",
                "audio_path": str(source),
                "response_format": "text",
            }
        )
    )
    assert text["text"] == "raw words"
    assert text["raw"] is None
    for payload, error in [
        ({"task": "transcribe"}, ValueError),
        (
            {"task": "transcribe", "audio_path": str(tmp_path / "missing")},
            FileNotFoundError,
        ),
    ]:
        with pytest.raises(error):
            await item.execute(make_job(payload=payload))
    item._session.response = Response(status=500, text="bad backend")
    with pytest.raises(RuntimeError, match="returned 500"):
        await item.execute(
            make_job(payload={"task": "transcribe", "audio_path": str(source)})
        )
    assert item._busy == 0
    assert _payload_num(make_job(payload={"speed": "bad"}), "speed") is None
    assert await _safe_text(Response(fail_text=True)) == "<unreadable body>"


@pytest.mark.asyncio
async def test_transcription_whisper_cpp_and_remote_audio_fetch():
    item = adapter(
        {"audio_stt_backend": "whisper-cpp", "audio_stt_base_url": "http://cpp"},
        Response(data={"text": "  words ", "language": "fr", "segments": [1]}),
    )
    result = await item.execute(
        make_job(
            payload={
                "task": "transcribe",
                "audio_url": "https://audio.test/a.mp3?token=x",
            }
        )
    )
    assert result["text"] == "words"
    assert result["backend"] == "whisper-cpp"
    assert item._session.calls[0][1] == "https://audio.test/a.mp3?token=x"
    assert item._session.calls[1][1] == "http://cpp/inference"
    with pytest.raises(ValueError, match="empty audio_url"):
        await item._fetch_audio("")
    item._session.response = Response(status=404, text="not found")
    with pytest.raises(RuntimeError, match="failed to fetch audio_url"):
        await item._fetch_audio("https://audio.test/missing")


@pytest.mark.asyncio
async def test_synthesis_backends_write_files_and_report_errors(tmp_path):
    out = tmp_path / "sub" / "speech.wav"
    coqui = adapter(
        {
            "audio_tts_backend": "coqui",
            "audio_tts_base_url": "http://coqui",
            "audio_tts_default_voice": "voice",
        },
        Response(audio=b"wav"),
    )
    result = await coqui.execute(
        make_job(
            payload={
                "task": "synthesize",
                "text": "hello",
                "output_path": str(out),
                "speed": 1.2,
            }
        )
    )
    assert result["bytes"] == 3 and out.read_bytes() == b"wav"
    body = coqui._session.calls[0][2]["json"]
    assert body["speaker"] == "voice" and body["speed"] == 1.2
    assert coqui._busy == 0

    piper = adapter(
        {"audio_tts_backend": "piper", "audio_tts_base_url": "http://piper"},
        Response(audio=b"piper"),
    )
    result = await piper.execute(
        make_job(payload={"task": "synthesize", "text": "hi", "speed": 2})
    )
    assert result["backend"] == "piper"
    assert piper._session.calls[0][1] == "http://piper/"
    for item, payload in [
        (coqui, {"task": "synthesize"}),
    ]:
        with pytest.raises(ValueError):
            await item.execute(make_job(payload=payload))
    coqui._session.response = Response(status=500, text="server error")
    with pytest.raises(RuntimeError, match="coqui TTS returned"):
        await coqui.execute(make_job(payload={"task": "synthesize", "text": "hello"}))
    piper._session.response = Response(status=400, text="bad request")
    with pytest.raises(RuntimeError, match="piper returned"):
        await piper.execute(make_job(payload={"task": "synthesize", "text": "hello"}))
    with pytest.raises(RuntimeError, match="synthesis is not configured"):
        await adapter().execute(make_job(payload={"task": "synthesize", "text": "hi"}))
    with pytest.raises(ValueError, match="must be 'transcribe'"):
        await coqui.execute(make_job(payload={"task": "other"}))


@pytest.mark.asyncio
async def test_unload_command_idle_busy_failure_timeout_and_success(monkeypatch):
    item = adapter()
    assert await item.unload_idle_models(100) == 0
    item._unload_command = "   "
    assert await item.unload_idle_models(100) == 0
    item._unload_command = "systemctl restart audio"
    item._busy = 1
    assert await item.unload_idle_models(100) == 0
    item._busy = 0

    class Proc:
        def __init__(self, code=0):
            self.returncode = code
            self.killed = False

        async def communicate(self):
            return b"", b"error"

        def kill(self):
            self.killed = True

        async def wait(self):
            return None

    proc = Proc(1)

    async def spawn(*_args, **_kwargs):
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    assert await item.unload_idle_models(100) == 0
    proc = Proc()
    assert await item.unload_idle_models(100) == 100
    proc = Proc()

    async def timeout(self):
        raise TimeoutError

    proc.communicate = timeout.__get__(proc)
    item._unload_wait = 0.001
    assert await item.unload_idle_models(100) == 0
    assert proc.killed

    async def missing(*_args, **_kwargs):
        raise OSError("not found")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", missing)
    assert await item.unload_idle_models(100) == 0


@pytest.mark.asyncio
async def test_probe_paths_and_start_cleanup(monkeypatch):
    item = adapter(
        {
            "audio_stt_backend": "whisper-cpp",
            "audio_stt_base_url": "http://stt",
            "audio_tts_backend": "coqui",
            "audio_tts_base_url": "http://tts",
        }
    )
    item._session.response = Response(status=500)
    await item._probe_stt()
    with pytest.raises(RuntimeError, match="TTS probe returned"):
        await item._probe_tts()
    assert len(item._session.calls) >= 3

    class NewSession(Session):
        def __init__(self, **_kwargs):
            super().__init__(Response(status=200))

    monkeypatch.setattr(aiohttp, "ClientSession", lambda **kwargs: NewSession(**kwargs))
    fresh = AudioAdapter(
        {"audio_stt_backend": "disabled", "audio_tts_backend": "disabled"}, object()
    )
    await fresh.start()
    with pytest.raises(RuntimeError, match="already started"):
        await fresh.start()
    await fresh.stop()

    async def failed_probe():
        raise RuntimeError("probe failed")

    broken = AudioAdapter(
        {"audio_stt_backend": "whisper-cpp", "audio_stt_base_url": "http://stt"},
        object(),
    )
    monkeypatch.setattr(broken, "_probe_stt", failed_probe)
    with pytest.raises(RuntimeError, match="probe failed"):
        await broken.start()
    assert broken._session is None
