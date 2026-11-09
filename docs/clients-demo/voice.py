#!/usr/bin/env python3
"""Give the video a voice-over: one ElevenLabs clip per scene, each scene as long as its clip.

    python3 docs/clients-demo/voice.py speak [FOLDER]   # voice every line in voice.json that has no clip yet
    python3 docs/clients-demo/voice.py fit     # set each scene's length to its clip, and its narration to the line
    python3 docs/demo/build.py docs/clients-demo
    python3 docs/clients-demo/voice.py check   # transcribe every clip and check words, pace, pauses, loudness, tone
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
import urllib.error
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
        if voice.get("seed") is not None:
            request_body["seed"] = voice["seed"]
        if voice.get("stitch"):
            # Each line is its own request, so without its neighbours the voice's tone drifts from scene to scene.
            words = lambda k: plain(voice["lines"][k]) if 0 <= k < len(voice["lines"]) else ""
            request_body["previous_text"], request_body["next_text"] = words(n - 2), words(n)
        body = json.dumps(request_body).encode()
        request = urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/" + voice["voice_id"], data=body, method="POST",
                                         headers={"xi-api-key": secret, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                clip(n).write_bytes(response.read())
        except urllib.error.HTTPError as e:
            sys.exit("line {}: ElevenLabs said {} {}".format(n, e.code, e.read()[:300]))
        print("line {:2d}: {:.1f}s".format(n, duration(clip(n))))


def plain(line):
    return re.sub(r"\s*<[^>]+>\s*", " ", re.sub(r"\[[^\]]+\]\s*", "", line)).strip()


def loudness(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


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
        # Bring every clip to one loudness first, so no scene sounds nearer or louder than the one before it.
        gain = -23 - loudness(clip(n))
        parts.append("[{}:a]aresample=44100,aformat=channel_layouts=mono,volume={:.2f}dB,atempo={},adelay={}:all=1,apad=whole_dur={},atrim=0:{}[a{}]".format(
            n - 1, gain, voice.get("tempo", 1.0), int(lead * 1000), scene["seconds"], scene["seconds"], n))
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


# ---- check: listen to every clip before it is mixed, the way the factory checks a screen ----

PACE = (140, 215)      # words a minute once at tempo: under 140 drags, over 215 sounds rushed
LONG_PAUSE = 0.9       # seconds of silence inside a line, at tempo, before it sounds like a stall
LATE_START = 0.35      # seconds of silence before the first word of a clip
LOUD_SPREAD = 1.5      # LU from the median clip
TONE_SPREAD = 0.15     # fraction from the median spectral centroid: a brighter or duller voice
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say_number(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        rest = n % 100
        return ONES[n // 100] + " hundred" + ("" if rest == 0 else " and " + say_number(rest))
    rest = n % 1000
    return say_number(n // 1000) + " thousand" + ("" if rest == 0 else " " + say_number(rest))


def words(text):
    """Comparable words: lower case, no punctuation, numbers spelled out, so "24" matches "twenty-four"."""
    text = plain(text).lower().replace("%", " percent").replace("&", " and ")
    text = re.sub(r"\$(\d+)\.(\d\d)", lambda m: "{} dollars {} cents".format(m.group(1), m.group(2)), text)
    text = re.sub(r"\d+", lambda m: say_number(int(m.group())) if int(m.group()) < 1000000 else m.group(), text)
    return re.findall(r"[a-z]+", re.sub(r"[-/]", " ", text.replace("'", "")))


def heard(n, secret):
    """What a listener hears in clip n: ElevenLabs speech-to-text, cached by the clip's content."""
    import hashlib
    data = clip(n).read_bytes()
    digest = hashlib.sha256(data).hexdigest()[:16]
    cache = CLIPS / "heard" / "{:02d}.json".format(n)
    if cache.exists():
        saved = json.loads(cache.read_text())
        if saved.get("clip") == digest:
            return saved["text"]
    boundary = "voicecheck" + digest
    body = b"".join([
        "--{}\r\nContent-Disposition: form-data; name=\"model_id\"\r\n\r\nscribe_v1\r\n".format(boundary).encode(),
        "--{}\r\nContent-Disposition: form-data; name=\"language_code\"\r\n\r\nen\r\n".format(boundary).encode(),
        "--{}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"clip.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".format(boundary).encode(),
        data, "\r\n--{}--\r\n".format(boundary).encode()])
    request = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST",
                                     headers={"xi-api-key": secret, "Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(request, timeout=120) as response:
        text = json.loads(response.read())["text"]
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps({"clip": digest, "text": text}, indent=1) + "\n")
    return text


def silences(path, floor=0.15):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "silencedetect=n=-40dB:d={}".format(floor), "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def centroid(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af",
                          "aspectralstats=measure=centroid,ametadata=print:key=lavfi.aspectralstats.1.centroid", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    values = [float(x) for x in re.findall(r"centroid=([\d.]+)", out) if float(x) > 0]
    return sum(values) / len(values) if values else 0.0


def differences(expected, got):
    """The words the listener heard differently, as "script -> heard" pieces."""
    import difflib
    out = []
    for op, a1, a2, b1, b2 in difflib.SequenceMatcher(None, expected, got, autojunk=False).get_opcodes():
        if op != "equal":
            out.append("{} -> {}".format(" ".join(expected[a1:a2]) or "(nothing)", " ".join(got[b1:b2]) or "(nothing)"))
    return out


def check(voice):
    """Every clip against its line, then the final mix. Exit 1 if anything fails; list what to listen to."""
    import statistics
    secret, tempo, lines = key(), voice.get("tempo", 1.0), voice["lines"]
    rows, listen, can_hear = [], [], True
    try:
        heard(1, secret)
    except urllib.error.HTTPError as e:
        # The words check needs speech-to-text on the key; the other checks still tell a lot.
        can_hear = False
        print("words not checked: ElevenLabs said {} ({}).\n".format(e.code, json.loads(e.read() or b"{}").get("detail", {}).get("message", "")))
    louds = {n: loudness(clip(n)) for n in range(1, len(lines) + 1)}
    tones = {n: centroid(clip(n)) for n in range(1, len(lines) + 1)}
    mid_loud, mid_tone = statistics.median(louds.values()), statistics.median(tones.values())
    for n, line in enumerate(lines, 1):
        problems = []
        expected = words(line)
        got = words(heard(n, secret)) if can_hear else expected
        missed = differences(expected, got)
        wrong = sum(len(m.split(" -> ")[0].split()) for m in missed if not m.startswith("(nothing)"))
        error = wrong / max(1, len(expected))
        if error > 0.06:
            problems.append("words: " + "; ".join(missed[:4]))
        rate = len(expected) / spoken(voice, n) * 60
        if not PACE[0] <= rate <= PACE[1]:
            problems.append("pace {:.0f} wpm".format(rate))
        quiet = silences(clip(n))
        if quiet and quiet[0][0] <= 0.01 and quiet[0][1] and quiet[0][1] > LATE_START * tempo:
            problems.append("starts {:.2f}s late".format(quiet[0][1] / tempo))
        stalls = [(a, b) for a, b in quiet if b and a > 0.01 and (b - a) / tempo > LONG_PAUSE and b < duration(clip(n)) - 0.05]
        if stalls:
            problems.append("pause {:.1f}s at {:.1f}s".format((stalls[0][1] - stalls[0][0]) / tempo, stalls[0][0] / tempo))
        if abs(louds[n] - mid_loud) > LOUD_SPREAD:
            problems.append("loudness {:+.1f} LU (levelled in the mix)".format(louds[n] - mid_loud))
        if mid_tone and abs(tones[n] / mid_tone - 1) > TONE_SPREAD:
            problems.append("tone {:+.0%} {}".format(tones[n] / mid_tone - 1, "brighter" if tones[n] > mid_tone else "duller"))
        hard = [p for p in problems if not p.startswith(("loudness", "tone"))]
        rows.append((n, "FAIL" if hard else ("LISTEN" if n in listen or any(p.startswith("tone") for p in problems) else "PASS"), "{:.0%}".format(error) if can_hear else "-", "{:.0f}".format(rate), "; ".join(problems)))
        if [p for p in problems if not p.startswith("loudness")]:   # the mix levels loudness; the rest needs an ear
            listen.append(n)
    print("line  result  words-off  wpm  findings")
    for n, result, error, rate, found in rows:
        print("{:>4}  {:<6}  {:>9}  {:>3}  {}".format(n, result, error, rate, found))
    failed = [r[0] for r in rows if r[1] == "FAIL"]
    final = HERE / json.loads((HERE / "story.json").read_text())["video"].replace(".mp4", "-voiced.mp4")
    if final.exists():
        quiet = silences(final, floor=0.3)
        start = quiet[0][1] if quiet and quiet[0][0] <= 0.01 and quiet[0][1] else 0.0
        verdict = "PASS" if start < 1.0 else "FAIL"
        opening = "{:.2f}s of silence before the first word".format(start) if start else "no silence over 0.3s before the first word"
        print("\nfinal mix: {} ({}), {} long".format(opening, verdict, "{:.0f}:{:02.0f}".format(*divmod(duration(final), 60))))
        if verdict == "FAIL":
            failed.append("mix")
    print("\n{} lines: {} pass, {} to listen to, {} fail".format(len(rows), sum(r[1] == "PASS" for r in rows),
                                                              sum(r[1] == "LISTEN" for r in rows), len([f for f in failed if f != "mix"])))
    if listen:
        print("listen to lines: " + ", ".join(str(n) for n in listen))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    commands = {"speak": speak, "fit": fit, "mix": mix, "review": review, "check": check}
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](json.loads((HERE / "voice.json").read_text()))
