#!/usr/bin/env python3
"""Captions for a voiced video, from its own script: FOLDER/captions.srt.

    python3 docs/demo/captions.py docs/visual-demo

Each scene's words come from story.json and its timing from the clip that voices it: the
words are spread over the clip's speech in proportion to their length, so a caption is on
screen while it is being said. YouTube indexes uploaded captions, and auto-captions
mishear names like Claude Code and IoU.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

MAX_CHARS = 84   # two lines of 42, the most a caption should hold


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout)


def chunks(text):
    """Sentences, and long sentences split at commas, then at word boundaries."""
    out = []
    for sentence in re.split(r"(?<=[.?!])\s+", text.strip()):
        parts, current = re.split(r"(?<=,)\s+", sentence), ""
        for part in parts:
            if current and len(current) + 1 + len(part) > MAX_CHARS:
                out.append(current)
                current = part
            else:
                current = (current + " " + part).strip()
        while len(current) > MAX_CHARS:
            cut = current.rfind(" ", 0, MAX_CHARS)
            out.append(current[:cut])
            current = current[cut + 1:]
        if current:
            out.append(current)
    return [c.replace("...", "…") for c in out if c.strip(" .…")]


def timeline(folder):
    """(start, end, text) for every caption, in seconds from the start of the video."""
    story = json.loads((folder / "story.json").read_text())
    voice = json.loads((folder / "voice.json").read_text())
    lead, tempo = voice.get("lead", 0.3), voice.get("tempo", 1.0)
    cues, t = [], 0.0
    for n, scene in enumerate(story["scenes"], 1):
        speech = duration(folder / "voice" / "{:02d}.mp3".format(n)) / tempo
        parts = chunks(scene.get("voice", ""))
        total = sum(len(p) for p in parts) or 1
        at = t + lead
        for part in parts:
            length = speech * len(part) / total
            cues.append((at, at + length, part))
            at += length
        t += scene["seconds"]
    return cues


def stamp(seconds):
    ms = int(round(seconds * 1000))
    return "{:02d}:{:02d}:{:02d},{:03d}".format(ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def main():
    folder = Path(sys.argv[1]).resolve()
    cues = timeline(folder)
    srt = "\n".join("{}\n{} --> {}\n{}\n".format(i, stamp(a), stamp(b), text) for i, (a, b, text) in enumerate(cues, 1))
    (folder / "captions.srt").write_text(srt)
    print("wrote {} ({} captions)".format(folder / "captions.srt", len(cues)))


if __name__ == "__main__":
    main()
