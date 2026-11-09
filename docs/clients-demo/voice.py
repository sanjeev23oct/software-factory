#!/usr/bin/env python3
"""Give the video a voice-over: one ElevenLabs clip per scene, each scene as long as its clip.

    python3 docs/clients-demo/voice.py speak [FOLDER]   # voice every line in voice.json that has no clip yet
    python3 docs/clients-demo/voice.py fit     # set each scene's length to its clip, and its narration to the line
    python3 docs/demo/build.py docs/clients-demo
    python3 docs/clients-demo/voice.py mix     # lay the clips on the video: clients-demo-voiced.mp4

FOLDER is another video's folder (default: this one). voice.json names the voice, the model, and
optionally its stability; without one, the voice's own saved settings apply, as on the ElevenLabs site.

The API key comes from ELEVENLABS_API_KEY, or from ~/.config/elevenlabs/key. It is never
written into this folder. Delete voice/NN.mp3 to voice one line again.
"""

import json
import math
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parent
CLIPS = HERE / "voice"
LEAD, BREATH = 0.3, 0.7   # seconds of quiet before each line, and after it before the next scene (voice.json may override)


def key():
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    text = (Path.home() / ".config" / "elevenlabs" / "key").read_text().strip()
    return text.split("=", 1)[1].strip().strip('"') if "=" in text else text


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout)


def clip(n):
    return CLIPS / "{:02d}.mp3".format(n)


def speak(voice):
    CLIPS.mkdir(exist_ok=True)
    secret = key()
    for n, line in enumerate(voice["lines"], 1):
        if clip(n).exists():
            continue
        request_body = {"text": line, "model_id": voice["model_id"]}
        if voice.get("settings"):
            # The voice's saved settings, with the speed this narration needs; a line may ask for its own speed.
            request_body["voice_settings"] = dict(voice["settings"], **({"speed": voice["speeds"][str(n)]}
                                                                        if str(n) in voice.get("speeds", {}) else {}))
        elif voice.get("stability") is not None:
            request_body["voice_settings"] = {"stability": voice["stability"]}
        body = json.dumps(request_body).encode()
        request = urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/" + voice["voice_id"], data=body, method="POST",
                                         headers={"xi-api-key": secret, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                clip(n).write_bytes(response.read())
        except urllib.error.HTTPError as e:
            sys.exit("line {}: ElevenLabs said {} {}".format(n, e.code, e.read()[:300]))
        print("line {:2d}: {:.1f}s".format(n, duration(clip(n))))


def gaps(voice):
    return voice.get("lead", LEAD), voice.get("breath", BREATH)


def spoken(voice, n):
    """How long line n takes once played at the narration's tempo (1.25 = a quarter faster, same pitch)."""
    return duration(clip(n)) / voice.get("tempo", 1.0)


def fit(voice):
    lead, breath = gaps(voice)
    story = json.loads((HERE / "story.json").read_text())
    if len(story["scenes"]) != len(voice["lines"]):
        sys.exit("voice.json has {} lines for {} scenes".format(len(voice["lines"]), len(story["scenes"])))
    for n, (scene, line) in enumerate(zip(story["scenes"], voice["lines"]), 1):
        scene["seconds"] = max(4, math.ceil(lead + spoken(voice, n) + breath))
        scene["voice"] = re.sub(r"\s*<[^>]+>\s*", " ", re.sub(r"\[[^\]]+\]\s*", "", line)).strip()   # words, not delivery cues or pauses
    (HERE / "story.json").write_text(json.dumps(story, indent=1, ensure_ascii=False) + "\n")
    total = sum(s["seconds"] for s in story["scenes"])
    print("{} scenes, {}:{:02d}".format(len(story["scenes"]), total // 60, total % 60))


def mix(voice):
    lead, _ = gaps(voice)
    story = json.loads((HERE / "story.json").read_text())
    scenes, inputs, parts = story["scenes"], [], []
    for n, scene in enumerate(scenes, 1):
        inputs += ["-i", str(clip(n))]
        parts.append("[{}:a]aresample=44100,aformat=channel_layouts=mono,atempo={},adelay={}:all=1,apad=whole_dur={},atrim=0:{}[a{}]".format(
            n - 1, voice.get("tempo", 1.0), int(lead * 1000), scene["seconds"], scene["seconds"], n))
    total = sum(s["seconds"] for s in scenes)
    # loudnorm works at 192 kHz; players and YouTube expect 48 kHz stereo, so the track ends as that.
    # The fades go before loudnorm: it hands on its first 3 seconds as one frame, and a fade after it mutes all of them.
    graph = ";".join(parts) + ";" + "".join("[a{}]".format(n) for n in range(1, len(scenes) + 1)) + \
        "concat=n={}:v=0:a=1,afade=t=in:d=0.4,afade=t=out:st={}:d=1.5,loudnorm=I=-16:TP=-1.5,aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[out]".format(len(scenes), total - 1.5)
    track = HERE / "voice" / "track.m4a"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", graph, "-map", "[out]",
                    "-c:a", "aac", "-b:a", "160k", str(track)], check=True)
    video, out = HERE / story["video"], HERE / story["video"].replace(".mp4", "-voiced.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(track), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("{}  {}:{:02d}  {:.1f} MB".format(out.name, int(duration(out)) // 60, int(duration(out)) % 60, out.stat().st_size / 1e6))


def review(voice):
    """Words a minute for each clip, pauses included: relaxed narration sits near 150, and above 170 sounds rushed."""
    for n, line in enumerate(voice["lines"], 1):
        words = len(re.sub(r"<[^>]+>|\[[^\]]+\]", " ", line).split())
        rate = words / spoken(voice, n) * 60
        limit = 170 * voice.get("tempo", 1.0)   # a faster tempo is a deliberate choice; judge each line against it
        print("line {:2d}: {:4.0f} wpm{}".format(n, rate, "   <-- rushed" if rate > limit else ""))


if __name__ == "__main__":
    commands = {"speak": speak, "fit": fit, "mix": mix, "review": review}
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](json.loads((HERE / "voice.json").read_text()))
